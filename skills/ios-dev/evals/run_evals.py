#!/usr/bin/env python3
"""Layer 3 of the ios-dev routing evals: run Step 0 for real and check what it decided.

For each case in `cases/ios-dev.json` this builds the case's fixture repo
(`fixtures.py`), runs headless Claude in it with the case prompt, and checks the
confirmation screen that Step 0 prints (`skill-router.md` §6) two ways:

  fields        `expected` against the screen's fixed fields, by string matching —
                free, deterministic, and the part worth trusting
  expectations  behaviour the fields cannot show, judged by a second model call that
                reads the trace (skip with --no-grade)

plus one hard check: the fixture repo must be untouched when the turn ends — Step 0
asks before it acts.

Headless Claude has no AskUserQuestion, so the screen arrives as plain text and the
turn ends there (verified 2026-09-19).  A case may carry a `followup`: it is sent as a
second turn with `--resume`, to see what happens after "照這組跑".  Only those cases
persist a session (under `~/.claude/projects/<the temp dir>`).

This costs tokens: about $1 and 70 s per case on opus.  Nothing runs without --run.

Usage:
  run_evals.py                          # list the cases and the plan, spend nothing
  run_evals.py --run [--case 3 --case 9] [--jobs 3] [--budget 2.0] [--model M]
                     [--no-grade] [--no-followup] [--grader-model sonnet] [--out DIR]
  run_evals.py --parse FILE.jsonl --case 3   # re-check a saved trace, spend nothing
  run_evals.py --probe-sandbox               # prove the sandbox holds before trusting --run (~$0.05)

Exit codes: 0 every case passed (or nothing was run) · 1 a case failed · 2 bad input.
"""
import argparse, concurrent.futures, datetime, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixtures  # noqa: E402

CASES_FILE = os.path.join(HERE, "cases", "ios-dev.json")

# The model under test runs with the user's own ~/.claude/settings.json, whose allowlist pre-approves
# `git commit`, `git push` and Edit/Write into a real project.  Contain it (Codex review 2026-09-19, P0):
# - Bash runs in the OS sandbox, may write only inside the fixture repo, has no network, and cannot
#   fall back to running unsandboxed; if the sandbox cannot start the run fails instead of going bare.
# - Edit/Write/NotebookEdit under /Users are denied (deny beats any allow rule).  The fixture repo
#   lives under the system temp dir, and -p auto-denies edits there anyway: Step 0 must not edit.
# Verified 2026-09-19 with --probe-sandbox: Bash write to $HOME → "Operation not permitted"; Write under
# $HOME → denied by permission settings; writes inside the fixture repo still work.  Re-run it after
# changing SANDBOX or upgrading Claude Code.
_HOME = os.path.expanduser("~")
SANDBOX = {
    "sandbox": {"enabled": True, "allowUnsandboxedCommands": False, "failIfUnavailable": True,
                "filesystem": {"allowWrite": ["."]}, "network": {"allowedDomains": []}},
    "permissions": {"deny": [f"{t}(/{_HOME}/**)" for t in ("Edit", "Write", "NotebookEdit")]},
}

# label → pattern.  Headless runs drift from §6: `Phase 3 派：` also shows up as a table row `| Phase 3 | … |`.
LABELS = {"載入": "載入", "Phase 3 派": r"Phase\s*3(?:\s*派)?", "Review 路線": r"Review\s*路線", "架構結論": "架構結論",
          "交棒": "交棒", "會問你": "會問你", "提醒": "提醒"}
# which §6 label each `expected` field is read from; a missing label is a hard fail, never a grader question
FIELD_LABEL = dict(gate="Phase 3 派", review_route="Review 路線", architecture="架構結論", handoff="交棒")
CORE_LABELS = ("載入", "Phase 3 派", "Review 路線", "架構結論", "交棒")
MIN_LABELS = 3  # fewer than this and there is no §6 screen, whatever the prose says
AXES = ("不適用", "兩者", "功能", "畫面", "效能", "行為")
SCENARIOS = {
    "1": ("新專案", "新模組", "大功能"), "2": ("小功能",), "3": ("純呈現", "純畫面"),
    "4": ("修正",), "5": ("優化",), "6": ("重構",), "7": ("接 ticket", "接ticket"),
}
# tiers, most specific first: `情境＝…` → table row `| 情境 | … |` → `情境 N` anywhere
SCENARIO_TIERS = [
    re.compile(r"情境\s*[＝=：:]\s*\**\s*([1-7])?[\s　]*([^\n（(|*]{0,24})"),
    re.compile(r"^\|\s*\**情境\**\s*\|\s*\**\s*([1-7])?[\s　]*([^\n（(|*]{0,24})", re.M),
    re.compile(r"情境\s*([1-7])()"),
]
AXIS_RE = re.compile(r"內容(?:軸)?\s*[＝=：:|]\s*\**\s*([^）)\n]+)")
# a gate word standing alone: `→ 輕（`, `（重）`, `輕重＝待定`, `（輕；…`, `輕閘門`, `預判「輕」`
# — not the 重 in 重繪／重判 or the 輕 in 輕量
GATE_RE = re.compile(r"(?:^|[\s（(→、：:*|＝=「])(待定|輕|重)(?=$|[\s（(）)，,、。*|；;」閘])", re.M)
# the route is the first thing in the field (§6: `Review 路線：<B 純 agent（預設）／…>`), never a letter found later
ROUTE_RE = re.compile(r"^[\s*<`]*([ABC])(?![A-Za-z])")

GRADER_SYSTEM = """你是 skill 評測的評審。你會拿到一段 agent 執行 ios-dev skill Step 0（情境路由）的軌跡，\
以及一組期望。逐條判定軌跡是否滿足該期望。

規則：
- 只看軌跡裡真的有的東西。evidence 引用軌跡原文或工具呼叫；找不到證據就判 fail，不要推測。
- 這是 headless 執行，沒有 AskUserQuestion 工具：確認畫面用文字印出、印完就停，是正常的，不算缺失。
- 期望描述的是行為，不是措辭；意思對就算過。
- 軌跡有 `[使用者第二輪]` 時，那之後的內容是使用者確認後才發生的。"""

GRADER_SCHEMA = {
    "type": "object", "required": ["results"],
    "properties": {"results": {"type": "array", "items": {
        "type": "object", "required": ["expectation", "pass", "evidence"],
        "properties": {"expectation": {"type": "string"}, "pass": {"type": "boolean"},
                       "evidence": {"type": "string"}}}}},
}


def squash(s):
    return re.sub(r"[\s　`*]", "", s or "")


def parse_stream(path):
    """Assistant text, tool calls and the result event from one stream-json file."""
    texts, tools, result = [], [], {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("{"):
                continue
            ev = json.loads(line)
            if ev.get("type") == "assistant":
                for b in ev["message"]["content"]:
                    if b["type"] == "text":
                        texts.append(b["text"])
                    elif b["type"] == "tool_use":
                        tools.append(dict(name=b["name"], input=b["input"]))
                        if b["name"] == "AskUserQuestion":  # interactive runs put the screen here
                            texts.extend(q.get("question", "") for q in b["input"].get("questions", []))
            elif ev.get("type") == "result":
                result = ev
    return texts, tools, result


def screen_fields(screen):
    """The §6 confirmation screen as {label: text}; a value runs until the next label."""
    hits = []
    for lab, pat in LABELS.items():
        m = re.search(rf"(?m)^[\s>*\-]*\**{pat}\**\s*[:：]|^\|\s*\**{pat}\**\s*\|", screen)
        if m:
            hits.append((m.start(), m.end(), lab, m.group(0).lstrip().startswith("|")))
    hits.sort()
    out = {}
    for i, (_, end, lab, in_table) in enumerate(hits):
        stop = hits[i + 1][0] if i + 1 < len(hits) else len(screen)
        value = screen[end:stop]
        if in_table:  # a table cell is one line
            value = value.split("\n", 1)[0].rstrip().rstrip("|")
        elif i + 1 == len(hits):  # the last field ends at a blank line or the closing fence
            value = re.split(r"\n\s*\n|```", value, maxsplit=1)[0]
        out[lab] = value.strip()
    out["_labels"] = len(hits)
    out["情境"] = scenario_of(screen)
    m = AXIS_RE.search(screen)
    value = m.group(1).strip() if m else ""
    if "功能" in value and "畫面" in value and not value.startswith(("兩者", "不適用")):
        value = "兩者"  # 「功能＋畫面」
    out["內容"] = next((a for a in AXES if value.startswith(a)), "?" + value if value else "")
    return out


def scenario_number(num, name):
    if num:
        return num
    return next((n for n, names in SCENARIOS.items() if any(a in name for a in names)), None)


def scenario_of(screen):
    """The one scenario the screen names: "N", "" when none, "?a,b" when it names more than one."""
    for tier in SCENARIO_TIERS:
        found = {n for m in tier.finditer(screen) if (n := scenario_number(m.group(1), m.group(2)))}
        if len(found) == 1:
            return found.pop()
        if found:
            return "?" + ",".join(sorted(found))
    return ""


def gate_of(text):
    """輕／重／待定 from the Phase 3 field; "?…" when the field names more than one."""
    if "每張 ticket" in text:
        return "依每張 ticket"
    words = set(GATE_RE.findall(text))
    if re.search(r"輕重\s*[＝=：:]?\s*待定", text):
        words.add("待定")  # 「輕重待定（預判輕…）」
    if "待定" in words:  # 「待定（預判 重，理由）」 is one answer, not two
        return "待定"
    return words.pop() if len(words) == 1 else ("?" + ",".join(sorted(words)) if words else "")


def check_fields(expected, f):
    """[(field, expected, got, ok)] for every field the case pins down."""
    rows = []

    def any_of(want, test):
        return any(test(w) for w in (want if isinstance(want, list) else [want]))

    def add(key, got, test):
        want = expected.get(key)
        if want is not None:
            rows.append((key, want, got, any_of(want, test)))

    add("scenario", f["情境"], lambda w: f["情境"] == w)
    add("content_axis", f["內容"], lambda w: f["內容"] == w or (w == "不適用" and not f["內容"]))
    gate = gate_of(f.get("Phase 3 派", ""))
    add("gate", gate, lambda w: w == gate)
    route = route_of(f.get("Review 路線", ""))
    add("review_route", route, lambda w: w == route)
    add("architecture", f.get("架構結論", ""), lambda w: bool(f.get("架構結論")) and squash(w) in squash(f["架構結論"]))
    add("handoff", f.get("交棒", ""), lambda w: bool(f.get("交棒")) and squash(w) in squash(f["交棒"]))
    return rows


NEGATION = re.compile(r"^[\s*）)]*(不成立|不適用|不行|不能|出局|被擋|擋下|✗|❌|不走|不選)")


def route_of(text):
    """The route the field starts with; "?X" when that first letter is being ruled out (「C 不成立，走 B」)."""
    m = ROUTE_RE.match(text)
    if not m:
        return ""
    return "?" + m.group(1) if NEGATION.match(text[m.end():]) else m.group(1)


def screen_problems(f):
    """Why this is not a §6 confirmation screen at all; empty when it is one."""
    if f["_labels"] < MIN_LABELS:
        return [f"no §6 confirmation screen: found {f['_labels']} of the labels {'／'.join(CORE_LABELS)}"]
    if not f["情境"]:
        return ["§6 screen names no scenario"]
    return []


def repo_changes(repo):
    """What the run did to the fixture repo; empty when Step 0 kept its hands off."""
    git = ["git", "-C", repo]
    dirty = subprocess.run(git + ["status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    commits = subprocess.run(git + ["rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = [l for l in dirty.split("\n") if l]
    if commits not in ("", "1"):
        out.append(f"{int(commits) - 1} new commit(s)")
    return out


def trace_text(turns):
    parts = []
    for i, (texts_tools, prompt) in enumerate(turns):
        parts.append(f"[使用者{'第二輪' if i else ''}] {prompt}")
        for kind, item in texts_tools:
            parts.append(item if kind == "text" else f"[工具] {item['name']} {json.dumps(item['input'], ensure_ascii=False)[:400]}")
    return "\n\n".join(parts)


def ordered_events(path):
    """Text and tool calls in the order they happened, for the grader."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("{"):
                continue
            ev = json.loads(line)
            if ev.get("type") == "assistant":
                for b in ev["message"]["content"]:
                    if b["type"] == "text":
                        out.append(("text", b["text"]))
                    elif b["type"] == "tool_use":
                        out.append(("tool", dict(name=b["name"], input=b["input"])))
    return out


def claude(args, cwd, out_path, stdin=None, timeout=900):
    with open(out_path, "w", encoding="utf-8") as fh:
        p = subprocess.run(["claude", *args], cwd=cwd, stdout=fh, stderr=subprocess.PIPE,
                           input=stdin, text=True, timeout=timeout)
    return p.returncode, p.stderr


def grade(expectations, trace, a, out_path, workdir):
    prompt = f"## 期望\n{json.dumps(expectations, ensure_ascii=False, indent=1)}\n\n## 軌跡\n{trace}"
    args = ["-p", "--output-format", "json", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
            "--system-prompt", GRADER_SYSTEM, "--json-schema", json.dumps(GRADER_SCHEMA),
            "--model", a.grader_model, "--max-budget-usd", "1"]
    code, err = claude(args, workdir, out_path, stdin=prompt, timeout=300)
    with open(out_path, encoding="utf-8") as fh:
        raw = fh.read()
    try:
        data = json.loads(raw)
        body = data.get("structured_output") or json.loads(re.sub(r"^```(?:json)?|```$", "", data["result"].strip()))
        return body["results"], data.get("total_cost_usd", 0)
    except (ValueError, KeyError, TypeError):
        return [dict(expectation="(grader)", **{"pass": False}, evidence=f"grader output unreadable: {err or raw[:200]}")], 0


def run_case(case, a, out_dir):
    cid = case["id"]
    stem = os.path.join(out_dir, f"case-{cid:02d}")
    res = dict(id=cid, group=case.get("group"), prompt=case["prompt"], cost=0.0)
    with tempfile.TemporaryDirectory(prefix=f"ios-dev-eval-{cid:02d}-") as repo:
        repo = os.path.realpath(repo)
        fixtures.build(cid, repo)
        base = ["--output-format", "stream-json", "--verbose", "--max-budget-usd", str(a.budget),
                "--settings", json.dumps(SANDBOX)]
        if a.model:
            base += ["--model", a.model]
        followup = None if a.no_followup else case.get("followup")
        first = ["-p", case["prompt"], *base] + ([] if followup else ["--no-session-persistence"])
        code, err = claude(first, repo, stem + ".jsonl")
        texts, tools, result = parse_stream(stem + ".jsonl")
        if code != 0 or not result:
            return dict(res, status="error", error=(err or "no result event").strip()[:400])
        res["cost"] += result.get("total_cost_usd") or 0
        res["seconds"] = round((result.get("duration_ms") or 0) / 1000)
        res["repo_changes"] = repo_changes(repo)  # before any followup: that turn is allowed to act
        turns = [(ordered_events(stem + ".jsonl"), case["prompt"])]
        if followup:
            try:
                claude(["-p", followup, "--resume", result["session_id"], *base], repo, stem + ".turn2.jsonl")
                res["cost"] += parse_stream(stem + ".turn2.jsonl")[2].get("total_cost_usd") or 0
                turns.append((ordered_events(stem + ".turn2.jsonl"), followup))
            finally:
                forget_sessions(repo)

        screen = "\n\n".join(texts)
        fields = screen_fields(screen)
        # Fixed fields are checked by string only.  Missing, unparseable or ambiguous is a fail —
        # the grader never gets to reinterpret prose as a field (Codex review 2026-09-19, P0).
        res["screen_problems"] = screen_problems(fields)
        rows = check_fields(case.get("expected", {}), fields)
        # an expectation about the second turn cannot be judged when that turn was skipped
        expectations = [e for e in case.get("expectations", []) if followup or "第二輪" not in e]
        res["fields"] = [dict(field=k, expected=w, got=g, ok=ok) for k, w, g, ok in rows]
        res["grades"] = []
        if expectations and not a.no_grade:
            res["grades"], cost = grade(expectations, trace_text(turns), a, stem + ".grade.json", repo)
            res["cost"] += cost
    ok = (not res["screen_problems"] and all(f["ok"] for f in res["fields"]) and not res["repo_changes"]
          and all(g["pass"] for g in res["grades"]))
    return dict(res, status="pass" if ok else "fail")


def probe_sandbox(model="haiku"):
    """Ask a sandboxed headless Claude to write outside its repo; PASS only if every attempt is stopped.

    The probe is given every permission it could need (unrestricted Bash, a Write allow rule for a
    scratch folder under $HOME), so only SANDBOX can be what stops it.  Anything it manages to write
    is deleted before returning.
    """
    home = os.path.expanduser("~")
    outside_bash = os.path.join(home, "claude-sandbox-probe.txt")
    outside_dir = os.path.join(home, "claude-deny-probe")
    prompt = ("Do exactly these three things and report each result verbatim: "
              f"1) run the bash command: touch {outside_bash} "
              "2) run the bash command: touch ./inside-probe.txt "
              f"3) use the Write tool to create {outside_dir}/x.txt with content hi. "
              "Do not retry or work around failures.")
    with tempfile.TemporaryDirectory(prefix="ios-dev-eval-probe-") as repo:
        subprocess.run(["git", "init", "-q", repo], check=True)
        p = subprocess.run(["claude", "-p", prompt, "--model", model, "--settings", json.dumps(SANDBOX),
                            "--allowedTools", "Bash", f"Write(/{outside_dir}/**)", "--no-session-persistence",
                            "--max-budget-usd", "0.3"], cwd=repo, capture_output=True, text=True, timeout=300)
        inside = os.path.exists(os.path.join(repo, "inside-probe.txt"))
    leaked = [x for x in (outside_bash, outside_dir) if os.path.exists(x)]
    for x in leaked:
        shutil.rmtree(x) if os.path.isdir(x) else os.remove(x)
    print(p.stdout.strip()[-1200:] or p.stderr.strip()[-600:])
    print()
    if leaked:
        print(f"FAIL: wrote outside the repo (deleted now): {', '.join(leaked)} — do not run --run")
        return 1
    if not inside:
        print("INCONCLUSIVE: nothing was written anywhere, so the sandbox may not have been exercised")
        return 1
    print("PASS: writes inside the repo work, writes outside were blocked")
    return 0


def forget_sessions(repo):
    """Delete the transcript that a resumable (two-turn) case left in ~/.claude/projects."""
    root = os.path.expanduser("~/.claude/projects")
    for path in {repo, os.path.realpath(repo), repo.replace("/private/", "/", 1)}:
        d = os.path.join(root, re.sub(r"[^A-Za-z0-9]", "-", path))
        if "ios-dev-eval-" in d and os.path.isdir(d):
            shutil.rmtree(d)


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def fixture_fingerprint(cid):
    """Hash of the files one case's fixture repo is built from (BASE plus its overlay)."""
    files = dict(fixtures.BASE)
    files.update(fixtures.CASES.get(cid, {}))
    return hashlib.sha256(json.dumps(files, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def provenance(cases):
    """What a results folder actually tested, so a later edit to cases or runner marks it stale."""
    head = subprocess.run(["git", "-C", HERE, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", "."],
                                capture_output=True, text=True).stdout.strip())
    return dict(cases_sha=sha(CASES_FILE), runner_sha=sha(os.path.abspath(__file__)),
                fixtures_sha=sha(os.path.join(HERE, "fixtures.py")), git_head=head, git_dirty=dirty,
                started=datetime.datetime.now().isoformat(timespec="seconds"), cases=cases,
                fixture_fps={cid: fixture_fingerprint(cid) for cid in cases})


def current_verdict(run_dir, meta, r, cases):
    """This result judged by today's definitions: "pass"/"fail", or why it no longer counts.

    What the model saw and what the grader judged must be unchanged, and so must the fixture.  A changed
    runner does not invalidate a trace: the fixed fields are re-parsed with today's parser (free); the
    grader's verdicts are kept, since an unchanged case means unchanged expectations.
    """
    cid = r["id"]
    if cid not in cases:
        return "stale: case removed"
    # What the model saw (prompt, followup) and what the grader judged (expectations) must be unchanged.
    # `expected` is re-checked live below, and notes or guards change nothing about the run.
    then = meta["cases"].get(str(cid)) or {}
    changed = [k for k in ("prompt", "followup", "expectations") if then.get(k) != cases[cid].get(k)]
    if changed:
        return "stale: case " + "/".join(changed) + " edited"
    fps = meta.get("fixture_fps")
    if fps is None:
        if meta.get("fixtures_sha") != sha(os.path.join(HERE, "fixtures.py")):
            return "unknown: fixtures.py changed and this run predates per-case fixture fingerprints"
    elif fps.get(str(cid)) != fixture_fingerprint(cid):
        return "stale: fixture edited"
    if r["status"] == "error":
        return "fail"
    trace = os.path.join(run_dir, f"case-{cid:02d}.jsonl")
    fields = screen_fields("\n\n".join(parse_stream(trace)[0]))
    rows = check_fields(cases[cid].get("expected", {}), fields)
    ok = (not screen_problems(fields) and all(x[3] for x in rows) and not r.get("repo_changes")
          and all(g["pass"] for g in r.get("grades", [])))
    return "pass" if ok else "fail"


def results_overview(cases):
    """Per results folder, and per case: the latest result that still counts under today's definitions."""
    root = os.path.join(HERE, "results")
    latest = {}
    print("\nresults (judged by today's cases, fixtures and parser):")
    for d in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        f = os.path.join(root, d, "summary.json")
        data = json.load(open(f, encoding="utf-8")) if os.path.isfile(f) else None
        if not (isinstance(data, dict) and "meta" in data):
            print(f"  {d}  no provenance (before 2026-09-19 fix): not counted")
            continue
        verdicts = {r["id"]: current_verdict(os.path.join(root, d), data["meta"], r, cases) for r in data["results"]}
        for cid, v in verdicts.items():
            if v in ("pass", "fail"):
                latest[cid] = (v, d)
        tally = {k: sum(1 for v in verdicts.values() if v.split(":")[0] == k) for k in ("pass", "fail", "stale", "unknown")}
        print(f"  {d}  cases {sorted(verdicts)}  now: " + "  ".join(f"{k} {n}" for k, n in tally.items() if n))
    covered = [c for c in cases if c in latest]
    passing = [c for c in covered if latest[c][0] == "pass"]
    print(f"\n  {len(passing)}/{len(cases)} cases pass on a result that still counts"
          + (f"; failing: {sorted(c for c in covered if latest[c][0] == 'fail')}" if len(passing) < len(covered) else "")
          + (f"; no counting result: {sorted(c for c in cases if c not in latest)}" if len(covered) < len(cases) else ""))


def report(results):
    for r in sorted(results, key=lambda r: r["id"]):
        print(f"\ncase {r['id']:>2} [{r['status'].upper()}] {r.get('group') or ''}  {r['prompt'][:50]}"
              f"   ${r.get('cost', 0):.2f} {r.get('seconds', '?')}s")
        if r["status"] == "error":
            print(f"    {r['error']}")
            continue
        for p in r.get("screen_problems", []):
            print(f"    {p}")
        for f in r["fields"]:
            if not f["ok"]:
                print(f"    field {f['field']}: expected {f['expected']!r}, got {f['got']!r}")
        for c in r["repo_changes"]:
            print(f"    repo changed before confirmation: {c}")
        for g in r["grades"]:
            if not g["pass"]:
                print(f"    expectation failed: {g['expectation']}\n        {g['evidence'][:200]}")
    passed = sum(r["status"] == "pass" for r in results)
    print(f"\n{passed}/{len(results)} passed   total ${sum(r.get('cost', 0) for r in results):.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="actually call Claude (spends tokens)")
    ap.add_argument("--case", type=int, action="append", help="case id; repeatable; default all")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--budget", type=float, default=2.0, help="USD cap per turn")
    ap.add_argument("--model", default=None, help="default: whatever `claude` is configured to use")
    ap.add_argument("--no-grade", action="store_true", help="fields and repo check only")
    ap.add_argument("--no-followup", action="store_true", help="first turn only, even for two-turn cases")
    ap.add_argument("--grader-model", default="sonnet")
    ap.add_argument("--out", default=None, help="default: results/<timestamp> next to this script")
    ap.add_argument("--parse", metavar="JSONL", help="re-check a saved trace against --case")
    ap.add_argument("--probe-sandbox", action="store_true", help="check SANDBOX really stops writes outside the repo (~$0.05)")
    a = ap.parse_args()
    if a.probe_sandbox:
        return probe_sandbox()

    with open(CASES_FILE, encoding="utf-8") as fh:
        cases = {c["id"]: c for c in json.load(fh)["evals"]}
    wanted = a.case or sorted(cases)
    if any(c not in cases for c in wanted):
        print(f"error: no such case; have {sorted(cases)}", file=sys.stderr)
        return 2

    if a.parse:
        if len(wanted) != 1 or not os.path.isfile(a.parse):
            print("error: --parse needs an existing file and exactly one --case", file=sys.stderr)
            return 2
        texts, _, _ = parse_stream(a.parse)
        fields = screen_fields("\n\n".join(texts))
        problems = screen_problems(fields)
        for p in problems:
            print(f"FAIL {p}")
        rows = check_fields(cases[wanted[0]].get("expected", {}), fields)
        for k, want, got, ok in rows:
            print(f"{'ok  ' if ok else 'FAIL'} {k}: expected {want!r}, got {got!r}")
        return 0 if all(r[3] for r in rows) and not problems else 1

    if not a.run:
        for cid in wanted:
            c = cases[cid]
            print(f"case {cid:>2}  {c.get('group', ''):10s} turns={2 if c.get('followup') else 1}  "
                  f"fields={sum(v is not None for v in c.get('expected', {}).values())}  "
                  f"expectations={len(c.get('expectations', []))}  {c['prompt'][:46]}")
        results_overview(cases)
        turns = sum(2 if cases[c].get("followup") else 1 for c in wanted)
        print(f"\n{len(wanted)} cases, {turns} turns, cap ${a.budget:.2f} per turn "
              f"(worst case ${turns * a.budget:.0f}; the 2026-09-19 trial cost $0.96).  Add --run to spend it.")
        return 0

    out_dir = a.out or os.path.join(HERE, "results", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)
    meta = provenance({cid: cases[cid] for cid in wanted})
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        results = list(pool.map(lambda cid: run_case(cases[cid], a, out_dir), wanted))
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(meta=meta, results=results), fh, ensure_ascii=False, indent=1)
    report(results)
    print(f"traces: {out_dir}")
    return 0 if all(r["status"] == "pass" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Lint a phase-workflow feature folder — the scripted half of `references/lint-rules.md`.

phase-workflow cuts a root doc (`overview.md`, or `rd-spec.md` for the PM-spec entry) into
one-file-per-ticket under `tickets/`.  The rules that keep that bundle honest used to be a
checklist the model walked by hand; a dry run (2026-09-20) showed the hand walk misses
things a parser does not.  This script reads the folder and checks, without calling a model:

  A. frontmatter   required keys, enums, ID letter matches `type`, file name equals the ID,
                   front matter really starts on line 1, no unfilled `{PLACEHOLDER}`,
                   every Behavior has a Demo line, every ticket has the fixed sections
  B. links         relative links resolve, no wikilinks, no leftover `{IF_…}` markers,
                   callout markers sit alone on their line (GitHub does not render
                   `> [!NOTE] title`), a medium bundle never links large-only files
  C. orphans       every ticket file is linked from `tickets/README.md`
  F. coverage      every `FR#` in the root doc is covered by a ticket, marked
                   `deferred: Stage N` in the README, or moved to "不做"; `covers` never
                   names an unknown `FR#`; only Foundation / Prefactor may cover nothing
  G. deps          `deps` is a list, every entry exists, no cycle, no forward dependency
  H. overlap/size  (warnings) two tickets edit the same file without a deps chain between
                   them; split signals; one FR covered by two Behaviors; a Foundation file
                   that only one Behavior touches; a Foundation bigger than every Behavior

What it cannot judge and leaves to the model: whether a title *means* two things (it only
sees conjunctions), whether two modules are independent, stale decisions (§ D), missing
concept pages (§ E).

Folders cut before 2026-09-20 use `type: Service|UI|Delta|Integration`, string `deps` and
free-form file names.  They are not migrated: when no ticket uses a new `type`, the folder
runs in legacy mode — § A basics and § B/C only, everything downgraded to a warning.

Usage:
  lint-tickets.py FEATURE_DIR [--strict] [--json]
  lint-tickets.py --scan ROOT [--strict] [--json]     lint every feature folder under ROOT
                                                      (for a scheduled docs health check)

Exit code: 0 clean (warnings allowed unless --strict) · 1 errors · 2 bad invocation.
"""
import argparse, json, os, re, sys
from urllib.parse import unquote

NEW_TYPES = {"Foundation": "F", "Prefactor": "P", "Behavior": "B"}
LEGACY_TYPES = {"Service", "UI", "Delta", "Integration"}
LAYERS = {"Service", "UI", "Delta", "Integration"}
STATUSES = {"backlog", "in-progress", "review", "done", "blocked"}
REQUIRED = ("ticket", "stage", "type", "status", "estimate")
REQUIRED_NEW = ("layers", "covers", "deps")
SECTIONS = ("Refs", "Files", "架構約束", "Tasks", "Acceptance Criteria", "Verification")
LARGE_ONLY = ("sprint-roadmap.md", "architecture/", "coordination/")
TEST_FILE = re.compile(r"Tests?(/|\.swift|\b)|Mock", re.I)
CALLOUT_WITH_TITLE = re.compile(r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]+\S", re.M)
FR = re.compile(r"\bFR\d+\b")


# ───────────────────────── parsing ─────────────────────────

def strip_comment(value):
    """Drop a trailing ` # comment` that is outside quotes."""
    quote = None
    for i, ch in enumerate(value):
        if ch in "\"'":
            quote = None if quote == ch else (quote or ch)
        elif ch == "#" and quote is None and (i == 0 or value[i - 1] in " \t"):
            return value[:i].rstrip()
    return value.rstrip()


def scalar(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def flow_list(text):
    inner, items, buf, quote = text.strip()[1:-1], [], "", None
    for ch in inner:
        if ch in "\"'":
            quote = None if quote == ch else (quote or ch)
            buf += ch
        elif ch == "," and quote is None:
            items.append(buf)
            buf = ""
        else:
            buf += ch
    items.append(buf)
    return [scalar(item) for item in items if item.strip()]


def front_matter(text):
    """Return (mapping, body, problem).  Handles the subset the ticket template uses:
    `key: scalar`, `key: [flow, list]`, and a block list under an empty `key:`."""
    lines = text.split("\n")
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first is None or lines[first].strip() != "---":
        return None, text, "front matter 不在檔案第一行（`---` 前面還有東西）"
    try:
        end = next(i for i in range(first + 1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text, "front matter 沒有結尾的 `---`"
    data, key = {}, None
    for raw in lines[first + 1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s+(.*)$", raw)
        if item and key is not None:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(scalar(strip_comment(item.group(1))))
            continue
        pair = re.match(r"^([A-Za-z_][\w-]*):(.*)$", raw)
        if not pair:
            continue
        key, value = pair.group(1), strip_comment(pair.group(2)).strip()
        if not value:
            data[key] = None
        elif value.startswith("[") and value.endswith("]"):
            data[key] = flow_list(value)
        else:
            data[key] = scalar(value)
    return data, "\n".join(lines[end + 1:]), None


def section(body, title):
    match = re.search(rf"^##\s+{re.escape(title)}.*?\n(.*?)(?=^##\s|\Z)", body, re.S | re.M)
    return match.group(1) if match else None


def without_code(text, keep_fences=False):
    if not keep_fences:
        text = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def as_list(value):
    """Legacy `deps` is a string ("1-S1, 2-S1", "none") or empty; new `deps` is a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [part.strip() for part in str(value).split(",")
            if part.strip() and part.strip().lower() not in {"none", "—", "-"}]


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# ───────────────────────── checks ─────────────────────────

class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, rule, where, message):
        self.errors.append({"rule": rule, "where": where, "message": message})

    def warn(self, rule, where, message):
        self.warnings.append({"rule": rule, "where": where, "message": message})


def load_tickets(folder, report):
    tickets, directory = {}, os.path.join(folder, "tickets")
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".md") or name == "README.md":
            continue
        data, body, problem = front_matter(read(os.path.join(directory, name)))
        if problem:
            report.error("A", f"tickets/{name}", problem)
            continue
        if "phase-ticket" not in as_list(data.get("tags")):
            continue
        tickets[str(data.get("ticket"))] = {"file": name, "fm": data, "body": body}
    return tickets


def root_requirements(folder, report):
    """Return (root doc name, [FR ids], {FR ids already handled in the root doc})."""
    overview, rd_spec = os.path.join(folder, "overview.md"), os.path.join(folder, "rd-spec.md")
    if os.path.exists(overview):
        text = read(overview)
        todo = re.search(r"^#{2,4}[^\n]*這次要做[^\n]*\n(.*?)(?=^#{2,4}\s|^---\s*$|\Z)", text, re.S | re.M)
        skip = re.search(r"^#{2,4}[^\n]*這次不做[^\n]*\n(.*?)(?=^#{2,4}\s|^---\s*$|\Z)", text, re.S | re.M)
        ids = FR.findall(without_code(todo.group(1))) if todo else []
        handled = set(FR.findall(without_code(skip.group(1)))) if skip else set()
        return "overview.md", sorted(set(ids), key=lambda x: int(x[2:])), handled
    if os.path.exists(rd_spec):
        text = read(rd_spec)
        table = re.search(r"^##[^\n]*需求對照[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.S | re.M)
        ids, handled = [], set()
        for line in (table.group(1) if table else "").splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3 or not FR.fullmatch(cells[0]):
                continue
            ids.append(cells[0])
            if not cells[-1] or "{" in cells[-1]:
                report.error("F", "rd-spec.md", f"{cells[0]}：需求對照表的「T 卡／處置」是空的")
            elif not re.search(r"\bT\d+\b", cells[-1]):
                handled.add(cells[0])  # Out of Scope / 待 PO: decided in the root doc itself
        return "rd-spec.md", ids, handled
    report.error("F", ".", "找不到根文件（overview.md 或 rd-spec.md）")
    return None, [], set()


def check_front_matter(tickets, report):
    for tid, ticket in tickets.items():
        fm, body, where = ticket["fm"], ticket["body"], f"tickets/{ticket['file']}"
        for key in REQUIRED:
            if fm.get(key) in (None, ""):
                report.error("A", where, f"缺 {key}")
        if fm.get("status") not in STATUSES:
            report.error("A", where, f"status 值不合法：{fm.get('status')}")
        if fm.get("status") == "done" and not fm.get("pr"):
            report.warn("A", where, "status 是 done 卻沒有 pr")
        kind = fm.get("type")
        if kind in LEGACY_TYPES:
            continue
        if kind not in NEW_TYPES:
            report.error("A", where, f"type 值不合法：{kind}")
            continue
        for key, value in fm.items():
            if isinstance(value, str) and re.search(r"\{[^}]*\}", value):
                report.error("A", where, f"{key} 還留著 placeholder：{value}")
        for key in REQUIRED_NEW:
            if key not in fm:
                report.error("A", where, f"缺 {key}")
        if not isinstance(fm.get("deps") or [], list):
            report.error("G", where, f"deps 不是 YAML list：{fm.get('deps')}")
        extra = set(as_list(fm.get("layers"))) - LAYERS
        if extra:
            report.error("A", where, f"layers 有不認得的值：{sorted(extra)}")
        letter = NEW_TYPES[kind]
        if re.fullmatch(r"\d+-[A-Z]\d+", tid) and not re.fullmatch(rf"\d+-{letter}\d+", tid):
            report.error("A", where, f"ID {tid} 的字母跟 type {kind} 對不上（應為 {letter}）")
        if os.path.splitext(ticket["file"])[0] != tid:
            report.error("A", where, f"檔名跟 ticket ID {tid} 不一致")
        for title in SECTIONS:
            if section(body, title) is None:
                report.error("A", where, f"缺「{title}」段")
        if kind == "Behavior":
            demo = re.search(r"^>\s*\*\*Demo\*\*\s*[:：]\s*(.*)$", body, re.M)
            if not demo or not demo.group(1).strip() or "{" in demo.group(1):
                report.error("A", where, "Behavior 的 Demo 行空白或還是 placeholder")
        verification = section(body, "Verification") or ""
        if re.search(r"\{(TEST|BUILD)_[A-Z_]+\}", verification):
            report.error("A", where, "Verification 段還留著 {TEST_…}／{BUILD_…} placeholder")


def check_links(folder, scale, legacy, report):
    flag = report.warn if legacy else report.error
    for base, _, names in os.walk(folder):
        for name in names:
            if not name.endswith(".md"):
                continue
            path = os.path.join(base, name)
            where, text = os.path.relpath(path, folder), read(path)
            prose = without_code(text)
            if re.search(r"\[\[[^\]\n]+\]\]", prose):
                flag("B", where, "出現 wikilink（產出要在 GitHub render，用 relative link）")
            # ai-prompts.md keeps its prompts in fenced blocks, so look inside fences for this one
            if re.search(r"\{IF_[A-Z_]*", without_code(text, keep_fences=True)):
                flag("B", where, "殘留 {IF_…} 條件標記")
            if CALLOUT_WITH_TITLE.search(prose):
                flag("B", where, "callout 標記後面接了標題；GitHub 只在標記獨佔一行時 render")
            for target in re.findall(r"\]\((?!https?:|mailto:|#)([^)\s]+)\)", prose):
                target = unquote(target.split("#")[0])
                if not target or "{" in target or "<" in target:
                    continue
                if scale == "medium" and any(part in target for part in LARGE_ONLY):
                    flag("B", where, f"中型連到大型專屬檔：{target}")
                elif not os.path.exists(os.path.normpath(os.path.join(base, target))):
                    flag("B", where, f"斷鏈：{target}")


def check_orphans(folder, tickets, legacy, report):
    readme = os.path.join(folder, "tickets", "README.md")
    if not os.path.exists(readme):
        (report.warn if legacy else report.error)("C", "tickets/README.md", "找不到 tickets/README.md")
        return ""
    text = read(readme)
    for ticket in tickets.values():
        if ticket["file"] not in text:
            report.warn("C", f"tickets/{ticket['file']}", "沒有被 tickets/README.md 連入")
    return text


def check_coverage(root, requirements, handled, tickets, readme, report):
    covered = {}
    for tid, ticket in tickets.items():
        fm, where = ticket["fm"], f"tickets/{ticket['file']}"
        if fm.get("type") not in NEW_TYPES:
            continue
        covers = as_list(fm.get("covers"))
        if not covers and fm.get("type") == "Behavior":
            report.error("F", where, "Behavior 的 covers 是空的（只有 Foundation／Prefactor 可以）")
        for item in covers:
            if item not in requirements:
                report.error("F", where, f"covers 列了 {root} 沒有的 {item}")
            covered.setdefault(item, []).append(tid)
    if not requirements:
        report.error("F", root or ".", "根文件沒有任何 FR# 編號，涵蓋檢查做不了")
    deferred = set()
    for line in readme.splitlines():
        if "deferred" in line:
            deferred.update(FR.findall(line))
    for item in requirements:
        if item not in covered and item not in deferred and item not in handled:
            report.error("F", item, "沒有任何 ticket 接，也沒標 deferred／不做")
        if root == "overview.md" and item not in readme:
            report.error("F", item, "tickets/README.md 的需求涵蓋表沒有這一列")
    for item, tids in sorted(covered.items()):
        behaviors = [t for t in tids if tickets[t]["fm"].get("type") == "Behavior"]
        if len(behaviors) > 1:
            report.warn("F", item, f"被 {len(behaviors)} 張 Behavior 涵蓋（{'、'.join(behaviors)}）："
                                   "這條 FR 可能並列了兩件事，回根文件拆成兩條")


def dependency_closure(tickets, report):
    graph = {}
    for tid, ticket in tickets.items():
        fm, where = ticket["fm"], f"tickets/{ticket['file']}"
        graph[tid] = as_list(fm.get("deps"))
        if fm.get("type") not in NEW_TYPES:
            continue
        for dep in graph[tid]:
            if dep not in tickets:
                report.error("G", where, f"deps 指向不存在的 {dep}")
            elif number(tickets[dep]["fm"].get("stage")) > number(fm.get("stage")):
                report.error("G", where, f"前向依賴：{dep} 的 Stage 比自己後面")
    closure = {}
    for tid in graph:
        seen, stack = set(), list(graph[tid])
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(graph.get(node, []))
        closure[tid] = seen
        if tid in seen:
            report.error("G", f"tickets/{tickets[tid]['file']}", "循環依賴")
    return closure


def listed_files(body):
    """Yield (name, is_edit, is_production) for each bullet in the Files section.
    A bullet that does not say 編輯 counts as newly created."""
    for line in (section(body, "Files") or "").splitlines():
        bullet = re.match(r"\s*-\s+(.*)$", line)
        if not bullet:
            continue
        text = bullet.group(1)
        quoted = re.match(r"`([^`]+)`", text)
        name = os.path.basename(quoted.group(1)) if quoted else re.split(r"[（(]", text)[0].strip()
        if name:
            yield name, "編輯" in text, not TEST_FILE.search(quoted.group(1) if quoted else name)


def check_overlap_and_size(tickets, closure, report):
    editors = {}
    current = {tid: t for tid, t in tickets.items() if t["fm"].get("type") in NEW_TYPES}
    for tid, ticket in current.items():
        fm, where = ticket["fm"], f"tickets/{ticket['file']}"
        files = list(listed_files(ticket["body"]))
        for name, is_edit, _ in files:
            if is_edit:
                editors.setdefault(name, []).append(tid)
        production = [name for name, _, is_production in files if is_production]
        if len(production) > 5:
            report.warn("H", where, f"production 檔 {len(production)} 個（>5）")
        if number(fm.get("estimate")) > 0.5:
            report.warn("H", where, f"estimate {fm.get('estimate')} >0.5 人天")
        criteria = len(re.findall(r"^\s*- \[[ xX]\]", section(ticket["body"], "Acceptance Criteria") or "", re.M))
        if criteria > 4:
            report.warn("H", where, f"Acceptance Criteria {criteria} 條（>4）")
        title = str(fm.get("title") or "")
        if fm.get("type") == "Behavior" and re.search(r"[和及與＋+、；;]", title):
            report.warn("H", where, f"Behavior 標題可能並列兩件事（看語意，可註記理由放行）：{title}")
        if re.search(r"全部|所有", title):
            report.warn("H", where, f"標題像一整層一張，檢查是不是按層切了：{title}")
    for name, tids in sorted(editors.items()):
        for i, first in enumerate(tids):
            for second in tids[i + 1:]:
                if second not in closure.get(first, ()) and first not in closure.get(second, ()):
                    report.warn("H", name, f"同檔未排序：{first}、{second} 都編輯它，互不在對方的 deps 鏈上")
    behaviors = {tid: t for tid, t in current.items() if t["fm"].get("type") == "Behavior"}
    largest = max((number(t["fm"].get("estimate")) for t in behaviors.values()), default=0)
    for tid, ticket in current.items():
        if ticket["fm"].get("type") != "Foundation":
            continue
        where = f"tickets/{ticket['file']}"
        for name, is_edit, is_production in listed_files(ticket["body"]):
            stem = os.path.splitext(name)[0]
            users = [b for b, t in behaviors.items() if stem and stem in t["body"]]
            if is_production and not is_edit and len(users) == 1:
                report.warn("H", where, f"`{name}` 只被一張 Behavior（{users[0]}）提到，可能不該在地基")
        if behaviors and number(ticket["fm"].get("estimate")) > largest:
            report.warn("H", where, f"estimate {ticket['fm'].get('estimate')} 大於每一張 Behavior"
                                    f"（最大 {largest}）；檢查是不是把 >0.5 人天的型別整份塞進來了")


# ───────────────────────── entry point ─────────────────────────

def lint(folder):
    report = Report()
    tickets = load_tickets(folder, report)
    legacy = bool(tickets) and not any(t["fm"].get("type") in NEW_TYPES for t in tickets.values())
    overview = os.path.join(folder, "overview.md")
    declared = (front_matter(read(overview))[0] or {}).get("scale") if os.path.exists(overview) else None
    scale = declared if declared in {"medium", "large"} else (
        "large" if os.path.exists(os.path.join(folder, "sprint-roadmap.md")) else "medium")

    check_front_matter(tickets, report)
    check_links(folder, scale, legacy, report)
    readme = check_orphans(folder, tickets, legacy, report)
    if not tickets:
        report.error("A", "tickets/", "沒有任何帶 tags: [phase-ticket] 的 ticket 檔")
    elif not legacy:
        root, requirements, handled = root_requirements(folder, report)
        check_coverage(root, requirements, handled, tickets, readme, report)
        check_overlap_and_size(tickets, dependency_closure(tickets, report), report)
    if legacy:  # never fail a folder cut under the old rules
        report.warnings = report.errors + report.warnings
        report.errors = []
    return {"folder": folder, "mode": "legacy" if legacy else "current", "scale": scale,
            "tickets": len(tickets), "errors": report.errors, "warnings": report.warnings}


def render(result):
    lines = [f"## Phase-Doc Lint — {os.path.basename(os.path.normpath(result['folder']))}",
             f"mode={result['mode']}  scale={result['scale']}  tickets={result['tickets']}", ""]
    if result["mode"] == "legacy":
        lines += ["（舊規則切的資料夾：只跑 § A 基本欄位與 § B／C，全部降成警告，不擋）", ""]
    for label, key in (("🔴 errors", "errors"), ("🟡 warnings", "warnings")):
        lines.append(f"### {label} ({len(result[key])})")
        lines += [f"- [§{item['rule']}] {item['where']} → {item['message']}" for item in result[key]]
        lines.append("")
    return "\n".join(lines)


def feature_folders(root):
    """Every folder under root whose tickets/ holds at least one phase-ticket file."""
    found = []
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "node_modules")
        if os.path.basename(base) != "tickets":
            continue
        for name in sorted(names):
            if name.endswith(".md") and name != "README.md":
                data = front_matter(read(os.path.join(base, name)))[0] or {}
                if "phase-ticket" in as_list(data.get("tags")):
                    found.append(os.path.dirname(base))
                    break
    return found


def render_scan(root, results):
    lines = [f"## Phase-Doc Lint — scan {root}", f"folders={len(results)}", ""]
    for result in results:
        lines.append(f"- {os.path.relpath(result['folder'], root)}  mode={result['mode']}  "
                     f"tickets={result['tickets']}  🔴 {len(result['errors'])}  🟡 {len(result['warnings'])}")
    for result in results:
        if result["mode"] == "current" and (result["errors"] or result["warnings"]):
            lines += ["", render(result)]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Lint a phase-workflow feature folder.")
    parser.add_argument("folder", nargs="?", help="feature folder that contains tickets/ and the root doc")
    parser.add_argument("--scan", metavar="ROOT", help="lint every feature folder found under ROOT")
    parser.add_argument("--strict", action="store_true", help="warnings also fail")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args()
    if bool(args.folder) == bool(args.scan):
        parser.print_usage(sys.stderr)
        return 2
    if args.scan:
        if not os.path.isdir(args.scan):
            print(f"error: {args.scan} 不是資料夾", file=sys.stderr)
            return 2
        results = [lint(folder) for folder in feature_folders(args.scan)]
        print(json.dumps(results, ensure_ascii=False, indent=2) if args.json else render_scan(args.scan, results))
        failed = any(r["errors"] or (args.strict and r["warnings"]) for r in results)
        return 1 if failed else 0
    if not os.path.isdir(os.path.join(args.folder, "tickets")):
        print(f"error: {args.folder} 不是 phase-workflow 功能資料夾（找不到 tickets/）", file=sys.stderr)
        return 2
    result = lint(args.folder)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
    failed = result["errors"] or (args.strict and result["warnings"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

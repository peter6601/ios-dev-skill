#!/usr/bin/env python3
"""Reference integrity check for the ios-dev skill — layer 1 of the routing evals.

The router promises that every skill and agent it names is really installed
(`skill-router.md` §9) and the five docs point at each other by section number,
section title and file path.  Nothing enforced that; a rename or an uninstall
only showed up when a real session tripped on it.  This script reads `SKILL.md`
and `references/*.md` and checks, without calling a model:

  1. declared   every name in router §9 resolves where its bullet says it lives
                (workspace skill + symlink · ~/.claude/skills · plugin · agent);
                `asc-*` N 個 must match the installed count
  2. slash      every `/command` written in the docs resolves to an installed skill
  3. undeclared skill-looking names used in the docs but missing from §9 (warning)
  4. section    `router §N` / `handoff-checklist.md §N` / bare `§N` point at a
                heading that exists
  5. title      `x.md` 的「標題」 points at a heading that exists in x.md
  6. path       `references/…`, `scripts/…`, `skills/…`, `<skill>/references/…`,
                `~/…` and absolute paths exist; absolute paths also warn (they
                break on another machine and in the public repo)
  7. frontmatter SKILL.md `name` equals the folder name, description ≤ 1024 chars

`§0 架構形狀` is the design doc's own §0 (it lives in overview.md / rd-spec.md), so it is
skipped.  A bare `§N` in handoff-checklist.md must be one of that file's own sections; a
router section has to be written `router §N`.

Usage:
  validate-router.py [--skill-dir DIR] [--workspace DIR] [--claude-home DIR]
                     [--strict] [--json]

Exit codes: 0 clean · 1 at least one error (or a warning under --strict) · 2 bad input.
"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

NAME = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
NAME_RE = re.compile(rf"^/?({NAME})(?::({NAME}))?$")
SLASH_RE = re.compile(rf"^/({NAME})(?=\s|$)")
TOKEN_RE = re.compile(r"`([^`\n]+)`")
SECTION_RE = re.compile(r"§(\d+)")
TITLE_REF_RE = re.compile(rf"`(?:references/)?({NAME}\.md)`\s*的?\s*「([^」]+)」")
BARE_MD_RE = re.compile(rf"^{NAME}\.md$")
ASC_COUNT_RE = re.compile(r"`asc-\*`\s*(\d+)\s*個")

PATH_PREFIXES = ("references/", "scripts/", "skills/", "agents/", "AI-Skills/")
PLACEHOLDER = re.compile(r"[<*\[]|YYYY|路徑")
# a slash command written bare inside a fenced block (router §8's examples live there)
FENCED_SLASH_RE = re.compile(rf"(?:^|\s)/({NAME})(?=\s|$)")
# `/x/y`, `/x.md`: a real absolute path; `/ios-dev` and `/consensus-review --profile ios` are commands
ABS_PATH_RE = re.compile(r"^/[^/\s]+(?:/|\.[A-Za-z0-9]{1,5}(?:#|$))")

# Docs that live in the target iOS repo or in another skill, not in references/.
EXTERNAL_DOCS = {"overview.md", "rd-spec.md", "latest-apis.md", "implementation-log.md"}

# Hyphenated tokens that are not skills or agents.
IGNORE = {
    # ai-review CLI and its subcommands
    "ai-review", "approve-code", "re-review", "submit-preflight",
    # project-layer framework skills: they live in the target repo's .claude/skills
    "speech-recognition", "natural-language", "ios-networking", "app-store-review",
    # plugin names
    "mattpocock-skills",
    "fix-first",
}
# Names this repo's docs mention that are neither skills nor agents (target repo names, product terms):
# one per line in `.validate-router-ignore` next to this script, so the script itself stays generic.
_extra = os.path.join(HERE, ".validate-router-ignore")
if os.path.isfile(_extra):
    with open(_extra, encoding="utf-8") as _fh:
        IGNORE |= {l.strip() for l in _fh if l.strip() and not l.startswith("#")}


class Report:
    def __init__(self):
        self.errors, self.warnings, self.counts = [], [], {}

    def _add(self, bucket, check, file, line, msg):
        bucket.append(dict(check=check, file=file, line=line, message=msg))

    def err(self, *a):
        self._add(self.errors, *a)

    def warn(self, *a):
        self._add(self.warnings, *a)

    def count(self, check, n=1):
        self.counts[check] = self.counts.get(check, 0) + n


def has_skill(d):
    return os.path.isfile(os.path.join(d, "SKILL.md"))


def build_inventory(workspace, claude_home):
    """Where every skill and agent on this machine actually lives."""
    inv = dict(workspace=set(), commands=set(), home=set(), agents=set(), plugins={}, broken=[], repo=workspace)

    for d in glob.glob(os.path.join(workspace, "skills", "*")):
        if has_skill(d) and not os.path.basename(d).startswith("_"):
            inv["workspace"].add(os.path.basename(d))

    for key, sub in (("commands", "commands"), ("home", "skills")):
        for d in glob.glob(os.path.join(claude_home, sub, "*")):
            name = os.path.basename(d)
            if os.path.islink(d) and not os.path.exists(d):
                inv["broken"].append(d)
            elif has_skill(d):
                inv[key].add(name)
            elif d.endswith(".md") and os.path.isfile(d):  # `~/.claude/commands/<name>.md`
                inv[key].add(name[:-3])

    for f in glob.glob(os.path.join(claude_home, "agents", "*.md")):
        if os.path.islink(f) and not os.path.exists(f):
            inv["broken"].append(f)
        else:
            inv["agents"].add(os.path.basename(f)[:-3])

    manifest = os.path.join(claude_home, "plugins", "installed_plugins.json")
    if os.path.isfile(manifest):
        with open(manifest, encoding="utf-8") as fh:
            data = json.load(fh)
        for key, entries in data.get("plugins", {}).items():
            prefix = key.split("@")[0]
            for e in entries if isinstance(entries, list) else [entries]:
                root = os.path.join(e.get("installPath", ""), "skills")
                for depth in ("*", "*/*", "*/*/*"):
                    for f in glob.glob(os.path.join(root, depth, "SKILL.md")):
                        inv["plugins"].setdefault(prefix, set()).add(os.path.basename(os.path.dirname(f)))
    return inv


def resolves(name, prefix, kind, inv):
    """None when the name is installed where `kind` expects it, else the reason."""
    plugin_names = set().union(*inv["plugins"].values()) if inv["plugins"] else set()
    linked = inv["commands"] | inv["home"]
    if prefix:
        if name in inv["plugins"].get(prefix, ()):
            return None
        return f"plugin `{prefix}` has no skill `{name}`" if prefix in inv["plugins"] else f"plugin `{prefix}` is not installed"
    if kind == "workspace":
        if name not in inv["workspace"]:
            return "no SKILL.md under workspace skills/"
        return None if name in linked else "in workspace but not linked from ~/.claude/commands or ~/.claude/skills"
    if kind == "home":
        if name in inv["home"] | inv["workspace"] | inv["commands"]:
            return None
        # A third-party pack the reader may not have installed yet: warn, and fail only under --strict.
        return "warn: not installed (third-party; install it or drop it from §9)"
    if kind == "plugin":
        return None if name in plugin_names else "no installed plugin ships it"
    if kind == "agent":
        return None if name in inv["agents"] else "not in ~/.claude/agents"
    if kind == "repo":  # published copy: the skill ships in this repo, or is already installed
        if os.path.isfile(os.path.join(inv["repo"], "skills", name, "SKILL.md")) or \
                os.path.isfile(os.path.join(inv["repo"], "agents", name + ".md")):
            return None
        return None if name in inv["workspace"] | linked | inv["agents"] else "not shipped in this repo and not installed"
    if kind == "external":  # lives in another repo (the consensus CLI); nothing local to check
        return None
    if name in inv["workspace"] | linked | inv["agents"] | plugin_names:
        return None
    return "not installed anywhere"


# §9 bullet heads, in both wordings this script serves: the workspace copy ("自家 skill …")
# and the published copy ("本 repo 附的 …").  A bullet may list skills and agents together, so the
# kind is tracked per token from the nearest preceding keyword, not guessed once per bullet.
HEAD_KINDS = (("workspace", ("自家 skill",)), ("repo", ("本 repo 附的",)),
              ("home", ("第三方 skill", "自寫但")), ("plugin", ("plugin",)), ("agent", ("agent",)),
              ("external", ("共識審查",)))
KIND_WORDS = (("agent", "agent"), ("skill", None))  # None = keep the bullet's own kind


def bullet_kind(text):
    head = text.lstrip("- ").lstrip().lstrip("*").lstrip()
    for kind, marks in HEAD_KINDS:
        if head.startswith(marks):
            return kind
    return "any"


def token_kinds(line, bullet):
    """[(token, kind)] for one §9 bullet; `skill …；agent …` switches kind mid-line."""
    out, kind = [], bullet
    for m in re.finditer(r"`([^`\n]+)`|\b(agents?|skills?)\b", line):
        if m.group(2):
            word = m.group(2).rstrip("s")
            kind = "agent" if word == "agent" else bullet
        else:
            out.append((m.group(1).strip(), kind))
    return out


def load_docs(skill_dir):
    paths = [os.path.join(skill_dir, "SKILL.md")] + sorted(glob.glob(os.path.join(skill_dir, "references", "*.md")))
    docs = {}
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            docs[os.path.relpath(p, skill_dir)] = fh.read().split("\n")
    return docs


def tokens(lines, fenced_too=False):
    """(line number, token) for every `backticked` span; fenced code blocks only on request."""
    fenced = False
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced_too or not fenced:
            for m in TOKEN_RE.finditer(line):
                yield i, m.group(1).strip().strip('"')


def headings(lines):
    return [l for l in lines if l.startswith("#")]


def section_span(lines, number):
    start = next((i for i, l in enumerate(lines) if re.match(rf"##\s+{number}\.", l)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return start, end


def check_declared(docs, inv, rep):
    """§9 of the router: every name resolves where its bullet says it lives."""
    rel = os.path.join("references", "skill-router.md")
    lines = docs.get(rel, [])
    span = section_span(lines, 9)
    declared, claims = set(), {}
    if span is None:
        rep.err("declared", rel, 0, "no `## 9.` section — nothing declares what must be installed")
        return declared
    for i in range(span[0] + 1, span[1]):
        line = lines[i]
        if not line.startswith("- "):
            # §9 also names things in prose (the published copy's fallback table); those count as
            # declared so they are not reported as undeclared later, but carry no install claim.
            declared.update(t.strip().lstrip("/") for t in TOKEN_RE.findall(line) if NAME_RE.match(t.strip()))
            continue
        kinds = dict(token_kinds(line, bullet_kind(line)))
        m = ASC_COUNT_RE.search(line)
        if m:
            found = sorted(n for n in inv["home"] if n.startswith("asc-"))
            declared.update(found)
            rep.count("declared")
            if len(found) != int(m.group(1)):
                rep.err("declared", rel, i + 1, f"`asc-*` says {m.group(1)} 個, {len(found)} installed")
        for tok in TOKEN_RE.findall(line):
            nm = NAME_RE.match(tok.strip())
            if not nm:
                continue
            first, second = nm.groups()
            prefix, name = (first, second) if second else (None, first)
            declared.add(tok.strip().lstrip("/"))
            declared.add(name)
            claims.setdefault(tok.strip(), []).append(
                (i + 1, resolves(name, prefix, kinds.get(tok.strip(), "any"), inv)))
    # A name may be listed twice (the published §9 mentions an agent again in another bullet's prose);
    # it is fine as long as one of its listings resolves.
    for tok, tries in claims.items():
        rep.count("declared")
        if any(why is None for _, why in tries):
            continue
        line_no, why = tries[0]
        (rep.warn if why.startswith("warn: ") else rep.err)(
            "declared", rel, line_no, f"`{tok}` — {why[6:] if why.startswith('warn: ') else why}")
    return declared


def check_names(docs, inv, declared, rep):
    """Slash commands must resolve; skill-looking names outside §9 are a warning."""
    seen = set()
    for rel, lines in docs.items():
        fenced = False
        for ln, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced and "`" not in line:
                for m in FENCED_SLASH_RE.finditer(line):
                    rep.count("slash")
                    why = resolves(m.group(1), None, "any", inv)
                    if why:
                        rep.err("slash", rel, ln, f"`/{m.group(1)}` (in a code block) — {why}")
        for ln, tok in tokens(lines):
            sm = SLASH_RE.match(tok)
            if sm:
                rep.count("slash")
                why = resolves(sm.group(1), None, "any", inv)
                if why:
                    rep.err("slash", rel, ln, f"`/{sm.group(1)}` — {why}")
                continue
            nm = NAME_RE.match(tok)
            if not nm or ("-" not in tok and ":" not in tok):
                continue
            key = tok.lstrip("/")
            if key in declared or key in IGNORE or key in seen:
                continue
            seen.add(key)
            first, second = nm.groups()
            why = resolves(second or first, first if second else None, "any", inv)
            rep.warn("undeclared", rel, ln,
                     f"`{tok}` is installed but not listed in router §9" if why is None
                     else f"`{tok}` looks like a skill or agent, is not in router §9, and is not installed "
                          f"(add it to IGNORE in this script if it is neither)")


def check_sections(docs, rep):
    router = os.path.join("references", "skill-router.md")
    handoff = os.path.join("references", "handoff-checklist.md")
    numbered = {
        router: {int(m.group(1)) for l in docs.get(router, []) if (m := re.match(r"##\s+(\d+)\.", l))},
        handoff: {int(m.group(1)) for l in docs.get(handoff, []) if (m := re.match(r"##\s+§(\d+)", l))},
    }
    for rel, lines in docs.items():
        for ln, line in enumerate(lines, 1):
            for m in SECTION_RE.finditer(line):
                if line[m.end():].lstrip().startswith("架構形狀"):
                    continue  # the design doc's own §0, not a router or handoff section
                n = int(m.group(1))
                back = line[max(0, m.start() - 30):m.start()]
                if "handoff-checklist" in back:
                    targets, label = numbered[handoff], "handoff-checklist.md"
                elif "router" in back:
                    targets, label = numbered[router], "skill-router.md"
                elif rel == handoff:  # a bare § here is this file's own; a router § must say "router"
                    targets, label = numbered[handoff], "handoff-checklist.md (bare § in this file; write `router §N` for the router)"
                else:
                    targets, label = numbered[router], "skill-router.md"
                rep.count("section")
                if n not in targets:
                    rep.err("section", rel, ln, f"§{n} — no such section in {label}")

            for m in TITLE_REF_RE.finditer(line):
                target = os.path.join("references", m.group(1))
                rep.count("title")
                if target not in docs:
                    rep.err("title", rel, ln, f"`{m.group(1)}` is not in references/")
                elif not any(m.group(2) in h for h in headings(docs[target])):
                    rep.err("title", rel, ln, f"「{m.group(2)}」 — no heading with this text in {m.group(1)}")


def check_paths(docs, skill_dir, workspace, claude_home, inv, rep):
    for rel, lines in docs.items():
        # Fenced blocks included: plan-template.md's fence is the text that lands in real plans.
        for ln, tok in tokens(lines, fenced_too=True):
            if PLACEHOLDER.search(tok):
                continue
            path_shaped = tok.startswith(PATH_PREFIXES + ("~/",)) or bool(ABS_PATH_RE.match(tok))
            if " " in tok and not path_shaped:
                continue
            if BARE_MD_RE.match(tok):
                rep.count("path")
                if tok not in EXTERNAL_DOCS and not os.path.isfile(os.path.join(skill_dir, "references", tok)):
                    rep.err("path", rel, ln, f"`{tok}` is not in references/ "
                                             f"(add it to EXTERNAL_DOCS in this script if it lives in the target repo)")
                continue
            if tok.startswith("~/") or ABS_PATH_RE.match(tok):
                rep.count("path")
                home = os.path.expanduser("~")
                real = tok.replace("~/.claude", claude_home, 1) if tok.startswith("~/.claude") else os.path.expanduser(tok)
                m = re.match(r"~/\.claude/(?:skills|commands)/([^/]+)/(.+)", tok)
                if m and not os.path.exists(real):  # not installed here, but this repo ships it
                    shipped = os.path.join(inv["repo"], "skills", m.group(1), m.group(2))
                    real = shipped if os.path.exists(shipped) else real
                if not os.path.exists(real):
                    rep.err("path", rel, ln, f"`{tok}` does not exist")
                elif os.path.isabs(tok) and tok.startswith(home):
                    rep.warn("path", rel, ln, f"`{tok}` is an absolute path — breaks on another machine and in the public repo")
                continue
            head = tok.split("/", 1)[0]
            if tok.startswith(PATH_PREFIXES):
                bases = [skill_dir, workspace]
            elif "/" in tok and head in inv["home"]:
                bases = [os.path.join(claude_home, "skills")]
            else:
                continue
            rep.count("path")
            if not any(os.path.exists(os.path.join(b, tok)) for b in bases):
                rep.err("path", rel, ln, f"`{tok}` does not exist")


def check_frontmatter(docs, skill_dir, rep):
    lines = docs["SKILL.md"]
    rep.count("frontmatter")
    if not lines or lines[0].strip() != "---" or "---" not in [l.strip() for l in lines[1:]]:
        rep.err("frontmatter", "SKILL.md", 1, "no frontmatter block")
        return
    block = lines[1:1 + [l.strip() for l in lines[1:]].index("---")]
    fields = {m.group(1): m.group(2).strip() for l in block if (m := re.match(r"([\w-]+):\s*(.*)$", l))}
    folder = os.path.basename(os.path.abspath(skill_dir))
    if fields.get("name") != folder:
        rep.err("frontmatter", "SKILL.md", 2, f"name is `{fields.get('name')}`, folder is `{folder}`")
    desc = fields.get("description", "")
    if not desc:
        rep.err("frontmatter", "SKILL.md", 3, "description is empty")
    elif len(desc) > 1024:
        rep.warn("frontmatter", "SKILL.md", 3, f"description is {len(desc)} chars (> 1024)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=os.path.dirname(HERE))
    ap.add_argument("--workspace", default=None, help="default: two levels above --skill-dir")
    ap.add_argument("--claude-home", default=os.path.expanduser("~/.claude"))
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    skill_dir = os.path.abspath(a.skill_dir)
    workspace = os.path.abspath(a.workspace or os.path.join(skill_dir, "..", ".."))
    if not os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
        err = dict(error="SKILL.md not found", path=skill_dir)
        if a.json:
            print(json.dumps(err, ensure_ascii=False))
        else:
            print(f"error: SKILL.md not found under {skill_dir}", file=sys.stderr)
        return 2

    docs = load_docs(skill_dir)
    inv = build_inventory(workspace, a.claude_home)
    rep = Report()
    for link in inv["broken"]:
        rep.err("declared", os.path.relpath(link, a.claude_home), 0, "broken symlink")
    declared = check_declared(docs, inv, rep)
    check_names(docs, inv, declared, rep)
    check_sections(docs, rep)
    check_paths(docs, skill_dir, workspace, a.claude_home, inv, rep)
    check_frontmatter(docs, skill_dir, rep)

    failed = bool(rep.errors) or (a.strict and bool(rep.warnings))
    if a.json:
        print(json.dumps(dict(errors=rep.errors, warnings=rep.warnings, checked=rep.counts,
                              docs=sorted(docs)), ensure_ascii=False, indent=1))
        return 1 if failed else 0

    for label, rows in (("ERROR", rep.errors), ("warn ", rep.warnings)):
        for r in rows:
            print(f"{label} [{r['check']}] {r['file']}:{r['line']}  {r['message']}")
    checked = "  ".join(f"{k}={v}" for k, v in sorted(rep.counts.items()))
    print(f"\ndocs={len(docs)}  checked: {checked}  errors={len(rep.errors)}  warnings={len(rep.warnings)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

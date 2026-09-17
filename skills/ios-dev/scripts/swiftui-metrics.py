#!/usr/bin/env python3
"""SwiftUI view-shape metrics — the quantitative half of `architecture-auditor`.

Measures every `struct X: View` in every file under a path and flags the four
gates agreed in the iOS workflow (2026-09-16):

  1. any view's `body` > 80 lines
  2. `@State` count per file > 5
  3. `isPresented:` count per file > 1   (→ use an Identifiable enum + .sheet(item:))
  4. `.onChange(of: <something>.should*/did*)`   (ViewModel commanding the View via Bool)

String literals and comments are blanked before measuring, so a `Text("}")` or a
commented-out block can no longer close a brace count early.  Every `var body`
in a file is measured, not just the first one.

Usage:
  swiftui-metrics.py <path> [--body 80] [--state 5] [--ispres 1] [--top 15] [--json]

Exit codes: 0 clean · 1 at least one gate violated · 2 bad input (path missing).
"""
import argparse, glob, json, os, re, sys

EXCLUDE = re.compile(r"(^|/)(\.build|DerivedData|Pods|Packages|.*Tests?|Preview Content|Previews?)(/|$)")
BODY_RE = re.compile(r"var\s+body\s*:\s*some\s+View\s*\{")
OWNER_RE = re.compile(r"\b(?:struct|class|extension)\s+(\w+)")
VIEW_RE = re.compile(r"struct\s+(\w+)\s*:\s*[^{]*\bView\b")


def blank_noise(src):
    """Replace the content of string literals and comments with spaces.

    Handles raw strings (`#"…"#`, `##"…"##`), multi-line strings, escapes, and
    interpolation: `\\(…)` is code, so a string nested inside it is blanked in
    turn.  Length and newlines are preserved, so offsets and line counts stay
    exact while braces, quotes and keywords hiding in text stop being counted.
    """
    out = list(src)
    n = len(src)

    def blank(a, b):
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    def hashes_at(j):
        k = j
        while k < n and src[k] == "#":
            k += 1
        return k - j

    stack = []  # ("str", terminator, hashes) | ("interp", open_paren_depth)
    i = 0
    while i < n:
        top = stack[-1] if stack else None

        # ---- inside a string literal ----
        if top and top[0] == "str":
            _, term, h = top
            esc = "\\" + "#" * h               # `\` normally, `\#` in a raw string
            if src.startswith(esc + "(", i):    # interpolation: back to code
                blank(i, i + len(esc) + 1)
                stack.append(("interp", 1))
                i += len(esc) + 1
                continue
            if src.startswith(esc, i):          # escape: \n, \", and raw \#n, \#"
                blank(i, i + len(esc) + 1)
                i += len(esc) + 1
                continue
            if src.startswith(term, i):
                blank(i, i + len(term))
                stack.pop()
                i += len(term)
                continue
            if not term.startswith('"""') and src[i] == "\n":
                stack.pop()                        # unterminated single-line string
                i += 1
                continue
            blank(i, i + 1)
            i += 1
            continue

        # ---- code inside an interpolation: track its parens ----
        if top and top[0] == "interp":
            if src[i] == "(":
                stack[-1] = ("interp", top[1] + 1)
                i += 1
                continue
            if src[i] == ")":
                blank(i, i + 1)
                if top[1] == 1:
                    stack.pop()
                else:
                    stack[-1] = ("interp", top[1] - 1)
                i += 1
                continue

        # ---- comments ----
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            blank(i, j)
            i = j
            continue
        if src.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/*", j):
                    depth += 1
                    j += 2
                elif src.startswith("*/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            blank(i, j)
            i = j
            continue

        # ---- string openers, raw or not, multi-line or not ----
        if src[i] in '#"':
            h = hashes_at(i)
            j = i + h
            if j < n and src[j] == '"':
                if src.startswith('"""', j):
                    blank(i, j + 3)
                    stack.append(("str", '"""' + "#" * h, h))
                    i = j + 3
                else:
                    blank(i, j + 1)
                    stack.append(("str", '"' + "#" * h, h))
                    i = j + 1
                continue
        i += 1
    return "".join(out)


def bodies_of(clean):
    """Every `var body` in the file, as (owner type name, line count, balanced)."""
    found = []
    for m in BODY_RE.finditer(clean):
        start, depth, i = m.end(), 1, m.end()
        while i < len(clean) and depth:
            c = clean[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        owner = "?"
        for om in OWNER_RE.finditer(clean, 0, m.start()):
            owner = om.group(1)
        found.append(dict(view=owner, lines=clean[start:i].count("\n"), balanced=depth == 0,
                          text=clean[start:i]))
    return found


def measure(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    src = blank_noise(raw)
    views = VIEW_RE.findall(src)
    if not views:
        return None
    bodies = bodies_of(src)
    worst = max(bodies, key=lambda b: b["lines"], default=None)
    branches = 0
    if worst:
        branches = (len(re.findall(r"^\s*(if|} else|switch)\b", worst["text"], re.M))
                    + len(re.findall(r"\?\s*[^:\n]+:\s*", worst["text"])))
    return dict(
        file=path,
        lines=raw.count("\n"),
        views=len(views),
        body=worst["lines"] if worst else 0,
        body_view=worst["view"] if worst else "-",
        bodies=[{k: v for k, v in b.items() if k != "text"} for b in bodies],
        unbalanced=[b["view"] for b in bodies if not b["balanced"]],
        branches=branches,
        state=len(re.findall(r"@State\b", src)),
        bool_toggles=len(re.findall(r"@State\s+(?:private\s+)?var\s+(?:is|show|should|has|did)\w*\s*(?::\s*Bool)?\s*=\s*(?:true|false)", src)),
        isPresented=len(re.findall(r"isPresented:", src)),
        subviews=max(len(re.findall(r"(?:@ViewBuilder\s+)?(?:private\s+)?(?:var|func)\s+\w+[^{\n]*->?\s*some\s+View", src)) - len(bodies), 0),
        onX=len(re.findall(r"\.onChange\(|\.onAppear|\.onReceive|\.onDisappear", src)),
        task_blocks=len(re.findall(r"Task\s*\{", src)),
        should_onchange=re.findall(r"\.onChange\(of:\s*[\w.]*\.(should\w+|did\w+)", src),
    )


def swift_files(path):
    if os.path.isfile(path):
        return [path] if path.endswith(".swift") else []
    return [f for f in glob.glob(os.path.join(path, "**", "*.swift"), recursive=True)
            if not EXCLUDE.search(os.path.relpath(f, path))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--body", type=int, default=80)
    ap.add_argument("--state", type=int, default=5)
    ap.add_argument("--ispres", type=int, default=1)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.path):
        err = dict(error="path not found", path=a.path)
        if a.json:
            print(json.dumps(err, ensure_ascii=False))
        else:
            print(f"error: path not found: {a.path}", file=sys.stderr)
        return 2

    rows = []
    for f in swift_files(a.path):
        r = measure(f)
        if r:
            r["file"] = os.path.relpath(f, a.path if os.path.isdir(a.path) else os.path.dirname(a.path))
            rows.append(r)

    if not rows:
        if a.json:
            print(json.dumps(dict(files=0, median_body=0, violators=[], all=[]), ensure_ascii=False))
        else:
            print("no SwiftUI view files found under", a.path)
        return 0

    for r in rows:
        over = [b for b in r["bodies"] if b["lines"] > a.body]
        r["violations"] = [v for v, hit in (
            (f"body>{a.body}" + (f" ({', '.join(b['view'] for b in over)})" if over else ""), bool(over)),
            (f"@State>{a.state}", r["state"] > a.state),
            (f"isPresented>{a.ispres}", r["isPresented"] > a.ispres),
            ("onChange(should*/did*)", bool(r["should_onchange"])),
        ) if hit]
    rows.sort(key=lambda r: (len(r["violations"]), r["body"]), reverse=True)
    violators = [r for r in rows if r["violations"]]
    bodies = sorted(r["body"] for r in rows)

    if a.json:
        print(json.dumps(dict(files=len(rows), median_body=bodies[len(bodies) // 2],
                              violators=violators, all=rows), ensure_ascii=False, indent=1))
        return 1 if violators else 0

    print(f"{'file':52s} {'views':>5} {'lines':>5} {'body':>5} {'@State':>6} {'boolTg':>6} {'isPres':>6} {'subV':>4} {'onX':>4} {'Task{':>5}  violations")
    for r in rows[:a.top]:
        print(f"{r['file'][-52:]:52s} {r['views']:5d} {r['lines']:5d} {r['body']:5d} {r['state']:6d} "
              f"{r['bool_toggles']:6d} {r['isPresented']:6d} {r['subviews']:4d} {r['onX']:4d} {r['task_blocks']:5d}  {', '.join(r['violations'])}")
    print(f"\nview files={len(rows)}  median body={bodies[len(bodies) // 2]}  violators={len(violators)}  "
          f"(gates: body>{a.body}, @State>{a.state}, isPresented>{a.ispres}, onChange(should*/did*))")
    for r in violators:
        big = [b for b in r["bodies"] if b["lines"] > a.body]
        if len(r["bodies"]) > 1 and big:
            print(f"  {r['file']}: bodies " + ", ".join(f"{b['view']}={b['lines']}" for b in r["bodies"]))
        if r["should_onchange"]:
            print(f"  {r['file']}: onChange watches {', '.join(sorted(set(r['should_onchange'])))}")
        if r["unbalanced"]:
            print(f"  {r['file']}: UNBALANCED braces in {', '.join(r['unbalanced'])} — measure by hand")
    return 1 if violators else 0


if __name__ == "__main__":
    sys.exit(main())

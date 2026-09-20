#!/bin/bash
# PreToolUse hook for /careful-ios.
# 讀 stdin 的 hook JSON，取出 Bash 指令，比對 SKILL.md「防護清單」的 pattern。
# 命中 → 回 permissionDecision=ask（警告，讓使用者選繼續或取消）；沒命中 → 靜默放行。
# 這個 hook 只提醒、不阻擋；解析失敗一律放行，不讓護欄自己變成故障點。

INPUT="$(cat)"

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

CAREFUL_IOS_INPUT="$INPUT" python3 - <<'PY'
import json, os, re, shlex, sys

# 不會被誤認成 source 目錄的 cache 名字：路徑裡任何一段是它，整條就是 cache。
SAFE_RM_CACHE_DIRS = {
    "DerivedData", "Pods", ".build", "xcuserdata", "xcshareddata",
    "SourcePackages", "ModuleCache", "node_modules",
}
# 泛用到可能真的是 source 目錄的名字（`Modules/Feature/build` 是真實存在的寫法）：
# 只有當它是相對路徑的第一段——也就是專案自己的頂層產物——才放行。
SAFE_RM_TOP_LEVEL_ONLY = {"build", "dist", "coverage"}
PROTECTED_BRANCH = re.compile(r"(^|[\s:/+])(release/[^\s]*|main|master|develop)(\s|$)")

# `git checkout/restore` 帶這些 pathspec = 整個工作區
WHOLE_TREE_PATHSPEC = {".", "./", ":/", ":/*", "*", ":(top)"}

# 會把真正的指令藏在字串參數裡的 wrapper
SHELL_WRAPPERS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
MAX_WRAPPER_DEPTH = 4

# 會吃掉自己的 option 的前綴指令：{名字: 需要再吃一個參數的 option}
PREFIX_COMMANDS = {
    "sudo": {"-u", "-g", "-p", "-C", "-D", "-h", "-R", "-t", "-U", "-c",
             "--user", "--group", "--prompt", "--close-from", "--chdir",
             "--host", "--role", "--type", "--other-user", "--command-timeout"},
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "command": set(),
    "time": {"-o", "--output", "-f", "--format"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p"},
    "stdbuf": {"-i", "-o", "-e"},
}

# SQL 只有真的交給資料庫執行才算破壞性；echo／grep 提到關鍵字不算
DB_CLIENTS = {"sqlite3", "sqlite", "psql", "mysql", "mariadb", "mysqlsh",
              "mongo", "mongosh", "sqlcmd", "duckdb", "usql"}
SQL_DESTRUCTIVE = re.compile(r"\b(DROP\s+TABLE|TRUNCATE(\s+TABLE)?)\b", re.I)


def command_from_hook_input(raw):
    try:
        return json.loads(raw).get("tool_input", {}).get("command", "") or ""
    except Exception:
        return ""


def split_segments(cmd):
    """Split a shell line into simple commands on ; && || | and newlines.

    Returns (segments, seps) where seps[i] is the operator that follows
    segments[i] — a `|` there is how `printf ... | sqlite3 db` is recognised.
    """
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None
    segments, seps, current = [], [], []
    for tok in tokens:
        if tok and set(tok) <= set(";&|"):
            if current:
                segments.append(current)
                seps.append(tok)
            current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
        seps.append(None)
    while len(seps) < len(segments):
        seps.append(None)
    return segments, seps


def strip_prefix(seg):
    """Drop `VAR=1`, `sudo -u root`, `env -i`, `nice -n 10`… to reach the real command."""
    seg = list(seg)
    while seg:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[0]):
            seg.pop(0)
            continue
        name = os.path.basename(seg[0])
        if name not in PREFIX_COMMANDS:
            break
        takes_arg = PREFIX_COMMANDS[name]
        seg.pop(0)
        while len(seg) > 1 and seg[0].startswith("-") and seg[0] != "-":
            opt = seg.pop(0)
            if opt == "--":
                break
            if "=" in opt:
                continue
            if opt in takes_arg and seg:
                seg.pop(0)
    return seg


def shell_c_argument(seg):
    """The command string of `sh -c '<cmd>'`, or None if this isn't that shape."""
    for i, tok in enumerate(seg[1:], 1):
        if not tok.startswith("-"):
            return None
        if tok == "--":
            return None
        if tok.startswith("--"):
            continue
        if "c" in tok[1:]:
            return seg[i + 1] if i + 1 < len(seg) else None
    return None


def _path_segments(target):
    parts = target.replace("\\", "/").strip().rstrip("/").split("/")
    return [p for p in parts if p and p != "."]


def is_safe_rm_target(target):
    """Only a cache path is safe.  A basename match anywhere is not enough."""
    segments = _path_segments(target)
    if not segments or ".." in segments:
        return False
    if any(part in SAFE_RM_CACHE_DIRS for part in segments):
        return True
    absolute = target.strip().startswith(("/", "~"))
    return not absolute and segments[0] in SAFE_RM_TOP_LEVEL_ONLY


def check_rm(seg):
    flags = [t for t in seg[1:] if t.startswith("-") and t != "--"]
    targets = [t for t in seg[1:] if not t.startswith("-")]
    short = "".join(f[1:] for f in flags if not f.startswith("--"))
    recursive = "r" in short or "R" in short or "--recursive" in flags

    for t in targets:
        if re.search(r"\.(xcodeproj|xcworkspace)/?$", t):
            return ("CRITICAL", f"刪除 Xcode 專案檔（{t}）：專案會無法建構。")
        if t.endswith(".entitlements"):
            return ("CRITICAL", f"刪除 entitlements（{t}）：App capabilities 全部失效。")
        if "Provisioning Profiles" in t:
            return ("DESTRUCTIVE", "刪除 Provisioning Profiles：需從 Apple Developer Portal 重新下載。")
    if not recursive:
        return None
    for t in targets:
        # 只有整個資料夾本身；底下某個 app 的 cache 是日常操作，不必問
        if re.search(r"Library/Developer/Xcode/DerivedData/?$", t):
            return ("CAUTION", "刪除全域 DerivedData：所有專案的 build cache 清除，下次 full rebuild。")
    unsafe = [t for t in targets if not is_safe_rm_target(t)]
    if unsafe:
        return ("DESTRUCTIVE", f"rm -r 非安全目標（{', '.join(unsafe[:3])}）：檔案會永久刪除。")
    return None


def check_git(seg):
    args = seg[1:]
    if not args:
        return None
    sub, rest = args[0], args[1:]
    joined = " ".join(rest)
    if sub == "push":
        forced = any(a in ("-f", "--force") or a.startswith("--force-with-lease") or a.startswith("--force-if-includes") for a in rest) \
            or any(not a.startswith("-") and a.startswith("+") for a in rest)
        if forced:
            if PROTECTED_BRANCH.search(" " + joined + " "):
                return ("CRITICAL", "force-push 到保護分支（release/main/master/develop）：覆寫分支歷史，破壞 CI/CD 和其他人的分支。")
            return ("CRITICAL", "force-push：覆寫 remote 歷史，其他人的 work 可能遺失。")
    if sub == "reset" and "--hard" in rest:
        return ("CRITICAL", "git reset --hard：永久丟失未 commit 的變更。")
    if sub in ("checkout", "restore") and any(a in WHOLE_TREE_PATHSPEC for a in rest):
        return ("CRITICAL", f"git {sub} <整個工作區>：丟失所有未 commit 的變更。")
    if sub == "branch" and any(a == "-D" or (a.startswith("-") and not a.startswith("--") and "D" in a) for a in rest):
        return ("CRITICAL", "git branch -D：未合併的 commit 可能遺失。")
    return None


def check_segment(seg, depth=0, piped_into=None):
    """Hits for one simple command.  A shell wrapper is scanned recursively."""
    seg = strip_prefix(seg)
    if not seg:
        return []
    head = os.path.basename(seg[0])
    if head in SHELL_WRAPPERS:
        inner = shell_c_argument(seg)
        if inner is not None and depth < MAX_WRAPPER_DEPTH:
            return scan(inner, depth + 1)
        return []
    text = " ".join(seg)
    hit = check_command(seg, head, text, piped_into)
    return [hit] if hit else []


def check_command(seg, head, text, piped_into):
    if head == "rm":
        return check_rm(seg)
    if head == "git":
        return check_git(seg)
    if head == "xcrun" and len(seg) >= 3 and seg[1] == "simctl":
        if seg[2] == "erase" and "all" in seg[3:]:
            return ("DESTRUCTIVE", "xcrun simctl erase all：所有 Simulator 重設為出廠狀態。")
        if seg[2] == "delete":
            return ("DESTRUCTIVE", "xcrun simctl delete：刪除 Simulator，需從 Xcode 重建。")
    if head == "security" and len(seg) >= 2 and seg[1] in ("delete-generic-password", "delete-internet-password", "delete-keychain", "delete-certificate", "delete-identity"):
        return ("DESTRUCTIVE", f"security {seg[1]}：儲存的憑證和 token 永久刪除。")
    if head == "pod" and "deintegrate" in seg[1:]:
        return ("DESTRUCTIVE", "pod deintegrate：CocoaPods 從專案移除，xcworkspace 失效。")
    if head == "swift" and seg[1:3] == ["package", "reset"]:
        return ("CAUTION", "swift package reset：SPM 依賴重新下載。")
    if head == "defaults" and len(seg) >= 2 and seg[1] == "delete":
        return ("CAUTION", "defaults delete：App 的 UserDefaults 全部清除。")
    if SQL_DESTRUCTIVE.search(text) and (head in DB_CLIENTS or piped_into in DB_CLIENTS):
        return ("DESTRUCTIVE", "DROP TABLE / TRUNCATE：SQLite / Core Data 資料永久遺失。")
    return None


def scan(cmd, depth=0):
    """Every hit in a whole command line, following pipes and shell wrappers."""
    if depth > MAX_WRAPPER_DEPTH:
        return []
    parsed = split_segments(cmd)
    if parsed is None:
        return [h for h in [fallback_regex(cmd)] if h]
    segments, seps = parsed
    hits = []
    for i, seg in enumerate(segments):
        piped_into = None
        if seps[i] == "|" and i + 1 < len(segments):
            nxt = strip_prefix(segments[i + 1])
            piped_into = os.path.basename(nxt[0]) if nxt else None
        hits.extend(check_segment(seg, depth, piped_into))
    return hits


def fallback_regex(cmd):
    """Used only when the line cannot be tokenised (unbalanced quotes, heredocs)."""
    rules = [
        (r"\bgit\s+push\b.*(\s-f\b|--force)", "CRITICAL", "force-push：覆寫 remote 歷史。"),
        (r"\bgit\s+reset\s+--hard\b", "CRITICAL", "git reset --hard：永久丟失未 commit 的變更。"),
        (r"\bxcrun\s+simctl\s+(erase\s+all|delete)\b", "DESTRUCTIVE", "xcrun simctl erase/delete：Simulator 資料會被清除。"),
        (r"\bpod\s+deintegrate\b", "DESTRUCTIVE", "pod deintegrate：CocoaPods 從專案移除。"),
        (r"\b(?:" + "|".join(sorted(DB_CLIENTS)) + r")\b.*\b(?:DROP\s+TABLE|TRUNCATE)\b",
         "DESTRUCTIVE", "DROP TABLE / TRUNCATE：資料永久遺失。"),
    ]
    for pattern, level, message in rules:
        if re.search(pattern, cmd, re.I):
            return (level, message)
    return None


ORDER = {"CRITICAL": 0, "DESTRUCTIVE": 1, "CAUTION": 2}
ICON = {"CRITICAL": "🚨", "DESTRUCTIVE": "⚠️", "CAUTION": "⚡"}

cmd = command_from_hook_input(os.environ.get("CAREFUL_IOS_INPUT", ""))
if not cmd.strip():
    sys.exit(0)

hits = scan(cmd)

if not hits:
    sys.exit(0)

hits.sort(key=lambda h: ORDER[h[0]])
level, message = hits[0]
extra = f"（另有 {len(hits) - 1} 項）" if len(hits) > 1 else ""
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": f"[careful-ios] {ICON[level]} {level}：{message}{extra}",
    }
}, ensure_ascii=False))
PY
exit 0

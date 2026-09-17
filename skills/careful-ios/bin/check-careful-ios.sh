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

SAFE_RM_TARGETS = {
    "DerivedData", "Pods", ".build", "xcuserdata", "xcshareddata",
    "SourcePackages", "ModuleCache", "node_modules", "dist", "build", "coverage",
}
PROTECTED_BRANCH = re.compile(r"(^|[\s:/+])(release/[^\s]*|main|master|develop)(\s|$)")


def command_from_hook_input(raw):
    try:
        return json.loads(raw).get("tool_input", {}).get("command", "") or ""
    except Exception:
        return ""


def split_segments(cmd):
    """Split a shell line into simple commands on ; && || | and newlines."""
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None
    segments, current = [], []
    for tok in tokens:
        if tok and set(tok) <= set(";&|"):
            if current:
                segments.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def strip_prefix(seg):
    seg = list(seg)
    while seg and (seg[0] in ("sudo", "command", "env", "time") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[0])):
        seg.pop(0)
    return seg


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
        if "Library/Developer/Xcode/DerivedData" in t:
            return ("CAUTION", "刪除全域 DerivedData：所有專案的 build cache 清除，下次 full rebuild。")
    unsafe = [t for t in targets if os.path.basename(t.rstrip("/")) not in SAFE_RM_TARGETS]
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
    if sub in ("checkout", "restore") and any(a in (".", "--", ":/") for a in rest) and "." in rest:
        return ("CRITICAL", f"git {sub} .：丟失所有未 commit 的變更。")
    if sub == "branch" and any(a == "-D" or (a.startswith("-") and not a.startswith("--") and "D" in a) for a in rest):
        return ("CRITICAL", "git branch -D：未合併的 commit 可能遺失。")
    return None


def check_segment(seg):
    seg = strip_prefix(seg)
    if not seg:
        return None
    head = os.path.basename(seg[0])
    text = " ".join(seg)
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
    if re.search(r"\b(DROP\s+TABLE|TRUNCATE(\s+TABLE)?)\b", text, re.I):
        return ("DESTRUCTIVE", "DROP TABLE / TRUNCATE：SQLite / Core Data 資料永久遺失。")
    return None


def fallback_regex(cmd):
    """Used only when the line cannot be tokenised (unbalanced quotes, heredocs)."""
    rules = [
        (r"\bgit\s+push\b.*(\s-f\b|--force)", "CRITICAL", "force-push：覆寫 remote 歷史。"),
        (r"\bgit\s+reset\s+--hard\b", "CRITICAL", "git reset --hard：永久丟失未 commit 的變更。"),
        (r"\bxcrun\s+simctl\s+(erase\s+all|delete)\b", "DESTRUCTIVE", "xcrun simctl erase/delete：Simulator 資料會被清除。"),
        (r"\bpod\s+deintegrate\b", "DESTRUCTIVE", "pod deintegrate：CocoaPods 從專案移除。"),
        (r"\b(DROP\s+TABLE|TRUNCATE)\b", "DESTRUCTIVE", "DROP TABLE / TRUNCATE：資料永久遺失。"),
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

segments = split_segments(cmd)
if segments is None:
    hits = [h for h in [fallback_regex(cmd)] if h]
else:
    hits = [h for h in (check_segment(s) for s in segments) if h]

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

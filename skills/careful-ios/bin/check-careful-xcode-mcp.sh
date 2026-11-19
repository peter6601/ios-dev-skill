#!/bin/bash
# PreToolUse hook for /careful-ios — Xcode MCP（xcrun mcpbridge）那幾個會刪檔、覆寫或改簽章的 tool。
# Bash 那支 hook 看不到 MCP 呼叫：透過 XcodeRM 刪檔、XcodeMV 覆寫、XcodeWrite 蓋掉 entitlements、
# UpdateTargetBuildSetting 改簽章，都不經過 Bash，所以另外攔。
# 命中 → permissionDecision=ask（Codex 加 --codex 時改 deny）；沒命中或解析失敗 → 靜默放行。
#
# 用法：
#   bash check-careful-xcode-mcp.sh           Claude Code 用
#   bash check-careful-xcode-mcp.sh --codex   Codex 用

CAREFUL_IOS_MODE="claude"
for arg in "$@"; do
  case "$arg" in
    --codex) CAREFUL_IOS_MODE="codex" ;;
  esac
done

INPUT="$(cat)"

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

CAREFUL_IOS_INPUT="$INPUT" CAREFUL_IOS_MODE="$CAREFUL_IOS_MODE" python3 - <<'PY'
import json, os, re, sys

# 跟 Bash 那支一致：路徑裡任何一段是這些名字，就是 cache，刪了不心疼。
SAFE_CACHE_DIRS = {
    "DerivedData", "Pods", ".build", "xcuserdata", "xcshareddata",
    "SourcePackages", "ModuleCache", "node_modules",
}
# 寫壞或蓋掉會讓專案建不起來、capability 失效、隱私宣告不見的檔
CRITICAL_FILE = re.compile(r"(\.xcodeproj|\.xcworkspace|\.pbxproj|\.entitlements|\.xcprivacy)/?$|(^|/)Info\.plist$")
# 改錯會讓簽章、bundle id、capability 跟 Apple Developer 帳號對不上
SIGNING_SETTING = re.compile(r"^(CODE_SIGN_.*|DEVELOPMENT_TEAM|PROVISIONING_PROFILE.*|PRODUCT_BUNDLE_IDENTIFIER)$")

try:
    data = json.loads(os.environ.get("CAREFUL_IOS_INPUT", ""))
    tool = str(data.get("tool_name", "")).rsplit("__", 1)[-1]
    args = data.get("tool_input") or {}
except Exception:
    sys.exit(0)


def segments(path):
    return [s for s in str(path).replace("\\", "/").split("/") if s]


def check():
    if tool == "XcodeRM":
        path = str(args.get("path", ""))
        if any(s in SAFE_CACHE_DIRS for s in segments(path)):
            return None
        if CRITICAL_FILE.search(path):
            return "🚨 CRITICAL", f"XcodeRM 要移除專案關鍵檔 `{path}`，專案可能建不起來或 capability 全部失效"
        trash = args.get("deleteFiles", True) is not False
        what = "並把檔案移到垃圾桶" if trash else "（只從專案移除，檔案留著）"
        rec = "，連同底下所有內容" if args.get("recursive") else ""
        return "⚠️ DESTRUCTIVE", f"XcodeRM 要從專案移除 `{path}`{rec}{what}"
    if tool == "XcodeMV":
        src, dst = str(args.get("sourcePath", "")), str(args.get("destinationPath", ""))
        if args.get("overwriteExisting"):
            return "⚠️ DESTRUCTIVE", f"XcodeMV 會覆寫已存在的 `{dst}`（來源 `{src}`），原檔內容不會保留"
        if CRITICAL_FILE.search(src) and args.get("operation", "move") != "copy":
            return "🚨 CRITICAL", f"XcodeMV 要搬動或改名專案關鍵檔 `{src}` → `{dst}`，build setting 裡寫死的路徑會失效"
        return None
    if tool == "XcodeWrite":
        path = str(args.get("filePath", ""))
        if CRITICAL_FILE.search(path):
            return "🚨 CRITICAL", f"XcodeWrite 會整份覆寫專案關鍵檔 `{path}`；改 Info.plist／entitlements 請優先用 AddInfoPlist／AddEntitlement"
        return None
    if tool == "UpdateTargetBuildSetting":
        name = str(args.get("buildSettingName", ""))
        target = args.get("targetName", "")
        if "buildSettingValue" not in args:
            return "⚡ CAUTION", f"UpdateTargetBuildSetting 要刪掉 target `{target}` 的 `{name}`"
        if SIGNING_SETTING.match(name):
            return "⚠️ DESTRUCTIVE", f"UpdateTargetBuildSetting 要把 target `{target}` 的 `{name}` 改成 `{args.get('buildSettingValue')}`，簽章或 bundle id 改錯會無法安裝、上架"
        return None
    return None


hit = check()
if hit is None:
    sys.exit(0)
level, detail = hit
if os.environ.get("CAREFUL_IOS_MODE") == "codex":
    decision = "deny"
    reason = f"[careful-ios] {level}：{detail}。確定要做的話，請自己在 Xcode 裡操作。"
else:
    decision = "ask"
    reason = f"[careful-ios] {level}：{detail}。確定要繼續嗎？"
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }
}, ensure_ascii=False))
PY

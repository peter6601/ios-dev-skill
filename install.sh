#!/bin/bash
# 把本 repo 的 skill 與 agent 裝進 Claude Code 與／或 Codex，然後檢查相依的 skill／plugin 裝了沒。
# 已存在且不是本 repo 裝的目標一律跳過，不覆蓋。
#
#   ./install.sh              安裝＋檢查相依（偵測這台電腦有 Claude、Codex 或兩者，每邊各裝一份）
#   ./install.sh --check      只檢查相依，不動任何檔案
#   ./install.sh --uninstall  移除（只移除本 repo 裝的連結與產生的檔案）
#   --platform=claude|codex|both   不自動偵測，指定平台
#   CLAUDE_HOME=/path  Claude 的位置（預設 ~/.claude）
#   CODEX_HOME=/path   Codex 的位置（預設 ~/.codex）；AGENTS_HOME=/path  Codex 讀 skill 的位置（預設 ~/.agents）
#
# vibe 版（給不讀 code 的使用者，見 VIBE.md）：
#   ./install.sh --vibe --dry-run   列出會做的事，不動任何東西
#   ./install.sh --vibe --yes       照清單全部做完（相依套件、模擬器工具、防呆、全域預設路由）
#   ./install.sh --vibe --check     多檢查 vibe 需要的東西
#   ./install.sh --vibe --uninstall 另外移除 ios-vibe 寫入全域設定的內容
#   測試用：NPX_BIN、CLAUDE_BIN、CODEX_BIN 可換成假指令；VIBE_SKIP_PREREQ=1 略過 Xcode 檢查。

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
NPX_BIN="${NPX_BIN:-npx}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
CODEX_BIN="${CODEX_BIN:-codex}"

usage() {
  sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
}

MODE=install
VIBE=0
YES=0
DRY=0
PLATFORM=auto
for arg in "$@"; do
  case "$arg" in
    --check) MODE=check ;;
    --uninstall) MODE=uninstall ;;
    --vibe) VIBE=1 ;;
    --yes|-y) YES=1 ;;
    --dry-run) DRY=1 ;;
    --platform=claude|--platform=codex|--platform=both) PLATFORM="${arg#--platform=}" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "不認得的參數：$arg"; usage; exit 2 ;;
  esac
done
if [ "$DRY" -eq 1 ] && [ "$VIBE" -eq 0 ]; then
  echo "--dry-run 只能搭配 --vibe 使用。"
  exit 2
fi

has_claude_cli() { command -v "$CLAUDE_BIN" >/dev/null 2>&1; }
has_codex_cli() { command -v "$CODEX_BIN" >/dev/null 2>&1; }

USE_CLAUDE=0
USE_CODEX=0
case "$PLATFORM" in
  claude) USE_CLAUDE=1 ;;
  codex) USE_CODEX=1 ;;
  both) USE_CLAUDE=1; USE_CODEX=1 ;;
  auto)
    if [ -d "$CLAUDE_HOME" ] || has_claude_cli; then USE_CLAUDE=1; fi
    if [ -d "$CODEX_HOME" ] || has_codex_cli; then USE_CODEX=1; fi
    # 兩邊都偵測不到：維持舊行為，裝給 Claude
    if [ "$USE_CLAUDE" -eq 0 ] && [ "$USE_CODEX" -eq 0 ]; then USE_CLAUDE=1; fi
    ;;
esac

link() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "  已安裝  $dst"
  elif [ -e "$dst" ] || [ -L "$dst" ]; then
    echo "  跳過    ${dst}（已存在，不是本 repo 的 symlink；要換請自己先移走）"
    SKIPPED=$((SKIPPED + 1))
  else
    ln -s "$src" "$dst"
    echo "  連結    $dst"
  fi
}

unlink_if_ours() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    rm "$dst"
    echo "  移除    $dst"
  fi
}

# Claude：skill 三種安裝形狀都算裝了：
#   skills/<name>/SKILL.md      npx skills / 本 repo installer 的落點
#   commands/<name>/SKILL.md    把 skill 目錄掛進 commands/ 的做法
#   commands/<name>.md          Claude Code 的 legacy command（單檔）
has_skill() {
  [ -e "$CLAUDE_HOME/skills/$1/SKILL.md" ] \
    || [ -e "$CLAUDE_HOME/commands/$1/SKILL.md" ] \
    || [ -e "$CLAUDE_HOME/commands/$1.md" ]
}

has_plugin() {
  local f="$CLAUDE_HOME/plugins/installed_plugins.json"
  [ -f "$f" ] && grep -q "\"$1@" "$f"
}

# Codex：使用者層 ~/.agents/skills、舊位置 ~/.codex/skills（npx skills -a codex 的落點）、plugin 附帶的 skill
has_skill_codex() {
  [ -e "$AGENTS_HOME/skills/$1/SKILL.md" ] && return 0
  [ -e "$CODEX_HOME/skills/$1/SKILL.md" ] && return 0
  local f
  for f in "$CODEX_HOME"/plugins/cache/*/*/*/skills/"$1"/SKILL.md; do
    [ -e "$f" ] && return 0
  done
  return 1
}

has_plugin_codex() {
  local f="$CODEX_HOME/config.toml"
  [ -f "$f" ] && grep -qF "plugins.\"$1@" "$f"
}

# 每列：層級|種類|名字|缺了會怎樣
# 層級：必裝＝主線跑不動；建議＝該情境降級；選配＝只影響出貨與 build 分析
DEPS='
必裝|skill|swiftui-expert-skill|6 個 agent 開工必讀它的 references，缺了 Phase 3 閘門整個跑不起來
必裝|plugin|superpowers|writing-plans／subagent-driven-development／TDD／verification 都來自它
必裝|skill|swift-architecture-skill|Step 4 產不出 §0 架構形狀；architecture-auditor 少一把尺
必裝|skill|swift-concurrency|async ownership 契約與 concurrency-auditor 的診斷清單
建議|skill|swiftui-specialist|實作 SwiftUI 時的寫法指引
建議|skill|swiftui-ui-patterns|畫面情境的 pattern 參考
建議|skill|swiftui-view-refactor|body >80 行要先拆時用
建議|skill|swiftui-performance-audit|perf-auditor 的稽核流程
建議|skill|review-swarm|重閘門的第四把（regression／安全／測試缺口）
建議|skill|bug-hunt-swarm|crash／regression／flaky 的假設階段
建議|skill|orchestrate-batch-refactor|重構 >3 檔要平行時
建議|plugin|mattpocock-skills|Step 3 的 /grill-with-docs；缺了改用 superpowers:brainstorming
建議|skill|consensus-review|review 路線 A（Codex 交叉審查）；缺了走路線 B
建議|skill|consensus-plan|Step 7 文件審查；缺了由人自己審
選配|skill|app-store-preflight-skills|store-preflight-auditor 的規則庫
選配|skill|xcode-project-analyzer|build-analyzer 的專案設定稽核項
選配|skill|xcode-compilation-analyzer|build-analyzer 的編譯時間熱點
選配|skill|spm-build-analysis|build-analyzer 的 SPM 依賴分析
選配|skill|xcode-build-fixer|build-analyzer 找到問題後要實際修 build 才需要；只分析可以不裝
'

# $1＝claude|codex
check_deps() {
  local platform="$1" missing_required=0 missing_other=0 where entry
  if [ "$platform" = "codex" ]; then where="Codex：${AGENTS_HOME}、${CODEX_HOME}"; entry='$ios-dev'; else where="Claude：${CLAUDE_HOME}"; entry='/ios-dev'; fi
  echo
  echo "相依檢查（${where}）："
  while IFS='|' read -r tier kind name why; do
    [ -z "$tier" ] && continue
    local ok=1
    if [ "$platform" = "codex" ]; then
      if [ "$kind" = "plugin" ]; then has_plugin_codex "$name" || ok=0; else has_skill_codex "$name" || ok=0; fi
    else
      if [ "$kind" = "plugin" ]; then has_plugin "$name" || ok=0; else has_skill "$name" || ok=0; fi
    fi
    if [ "$ok" -eq 1 ]; then
      echo "  ✓ [$tier] $name"
    else
      echo "  ✗ [$tier] $name — $why"
      if [ "$tier" = "必裝" ]; then missing_required=$((missing_required + 1)); else missing_other=$((missing_other + 1)); fi
    fi
  done <<< "$DEPS"
  echo
  if [ "$missing_required" -gt 0 ]; then
    echo "缺 ${missing_required} 個必裝相依：${entry} 會啟動，但主線走不完。安裝指令在 README「安裝」的第 1 步。"
  elif [ "$missing_other" -gt 0 ]; then
    echo "必裝的都在。另有 ${missing_other} 個建議／選配沒裝——${entry} 進場時會提醒，並改走 router §9 的替代路徑。"
  else
    echo "相依都裝好了。"
  fi
}

# ---------- Codex：agent 轉檔 ----------

CODEX_AGENT_MARK='generated by ios-dev-skill gen-codex-agents.py'

codex_gen_agents() {
  if ! python3 -c 'pass' >/dev/null 2>&1; then
    echo "  ⚠️ 沒有 python3，無法把 agent 轉成 Codex 格式。"
    return 1
  fi
  # plugin 快取的萬用字元原樣交給腳本展開：同一個 plugin 有多個版本時，它會讓新版優先
  python3 "$REPO/scripts/gen-codex-agents.py" --out "$CODEX_HOME/agents" \
    --skills-root "$AGENTS_HOME/skills" --skills-root "$CODEX_HOME/skills" \
    --skills-root "$CODEX_HOME/plugins/cache/*/*/*/skills"
}

codex_remove_agents() {
  local file name dst
  for file in "$REPO"/agents/*.md; do
    name="$(basename "$file" .md)"
    dst="$CODEX_HOME/agents/$name.toml"
    if [ -f "$dst" ] && head -1 "$dst" | grep -qF "$CODEX_AGENT_MARK"; then
      rm "$dst"
      echo "  移除    $dst"
    fi
  done
}

# ---------- vibe 版 ----------

ROUTING_BEGIN='<!-- ios-vibe:begin（由 ios-dev-skill 的 install.sh --vibe 寫入；install.sh --vibe --uninstall 會移除） -->'
ROUTING_END='<!-- ios-vibe:end -->'
CLAUDE_ROUTING_FILE="$CLAUDE_HOME/CLAUDE.md"
CODEX_ROUTING_FILE="$CODEX_HOME/AGENTS.md"
CODEX_HOOKS_FILE="$CODEX_HOME/hooks.json"
CAREFUL_HOOK_CMD="bash \"$REPO/skills/careful-ios/bin/check-careful-ios.sh\" --codex"
XCODEBUILDMCP_WORKFLOWS='simulator,simulator-management,ui-automation'

# 每列：這組提供的 skill（空白分隔）|npx 參數（Tab 分隔）
VIBE_NPX_GROUPS='
swift-architecture-skill|skills	add	https://github.com/efremidze/swift-architecture-skill	-a	claude-code	-g	-y
swift-concurrency|skills	add	https://github.com/AvdLee/Swift-Concurrency-Agent-Skill	-a	claude-code	-g	-y
swiftui-expert-skill|skills@latest	add	https://github.com/AvdLee/SwiftUI-Agent-Skill	--skill	swiftui-expert-skill	-a	claude-code	-g	-y
swiftui-specialist swiftui-whats-new-27|skills	add	superagents-lab/xcode27-skills	--skill	swiftui-specialist	--skill	swiftui-whats-new-27	-a	claude-code	-g	-y
swiftui-ui-patterns swiftui-view-refactor swiftui-performance-audit bug-hunt-swarm review-swarm orchestrate-batch-refactor|skills	add	https://github.com/Dimillian/Skills	--skill	swiftui-ui-patterns	--skill	swiftui-view-refactor	--skill	swiftui-performance-audit	--skill	bug-hunt-swarm	--skill	review-swarm	--skill	orchestrate-batch-refactor	-a	claude-code	-g	-y
'

# Codex 版：swiftui-ui-patterns／swiftui-view-refactor／swiftui-performance-audit 由官方 build-ios-apps plugin 提供，這裡不重複裝
VIBE_NPX_GROUPS_CODEX='
swift-architecture-skill|skills	add	https://github.com/efremidze/swift-architecture-skill	-a	codex	-g	-y
swift-concurrency|skills	add	https://github.com/AvdLee/Swift-Concurrency-Agent-Skill	-a	codex	-g	-y
swiftui-expert-skill|skills@latest	add	https://github.com/AvdLee/SwiftUI-Agent-Skill	--skill	swiftui-expert-skill	-a	codex	-g	-y
swiftui-specialist swiftui-whats-new-27|skills	add	superagents-lab/xcode27-skills	--skill	swiftui-specialist	--skill	swiftui-whats-new-27	-a	codex	-g	-y
bug-hunt-swarm review-swarm orchestrate-batch-refactor|skills	add	https://github.com/Dimillian/Skills	--skill	bug-hunt-swarm	--skill	review-swarm	--skill	orchestrate-batch-refactor	-a	codex	-g	-y
'

# Codex plugin：名字|要裝的 selector|用途
VIBE_CODEX_PLUGINS='
superpowers|superpowers@openai-curated|計畫、實作、驗證流程
build-ios-apps|build-ios-apps@openai-curated|模擬器工具（XcodeBuildMCP）與畫面相關 skill
'

has_routing() { [ -f "$1" ] && grep -qF 'ios-vibe:begin' "$1"; }
has_xcodebuildmcp() { has_claude_cli && "$CLAUDE_BIN" mcp get XcodeBuildMCP >/dev/null 2>&1; }
has_careful_hook() { [ -f "$CODEX_HOOKS_FILE" ] && grep -qF 'check-careful-ios.sh' "$CODEX_HOOKS_FILE"; }

# $1＝群組的 skill 名稱，$2＝claude|codex
group_missing() {
  local names="$1" platform="$2" n
  for n in $names; do
    if [ "$platform" = "codex" ]; then has_skill_codex "$n" || return 0; else has_skill "$n" || return 0; fi
  done
  return 1
}

vibe_prereq() {
  [ "${VIBE_SKIP_PREREQ:-0}" = "1" ] && return 0
  if ! xcodebuild -version >/dev/null 2>&1 && ! ls -d /Applications/Xcode*.app >/dev/null 2>&1; then
    echo "找不到 Xcode。請先從 App Store 安裝 Xcode，打開一次、同意授權條款，再重新執行。"
    return 1
  fi
  if ! python3 -c 'pass' >/dev/null 2>&1; then
    echo "找不到可用的 python3。裝好 Xcode 後通常就有；請打開 Xcode 一次讓它完成安裝，再重新執行。"
    return 1
  fi
  if [ ! -d "$CLAUDE_HOME" ] && ! has_claude_cli && [ ! -d "$CODEX_HOME" ] && ! has_codex_cli; then
    echo "找不到 Claude 或 Codex。請先安裝其中一個（Claude 桌面 app／Claude Code，或 Codex 桌面 app／Codex CLI）。"
    return 1
  fi
  return 0
}

vibe_plan() {
  local names args name selector why
  echo "vibe 版會做這些事："
  if [ "$USE_CLAUDE" -eq 1 ]; then
    echo " Claude："
    echo "  - 把本專案的 skill 與 agent 連結到 ${CLAUDE_HOME}（已有的不覆蓋）"
    while IFS='|' read -r names args; do
      [ -z "$names" ] && continue
      if group_missing "${names}" claude; then echo "  - 安裝 skill：${names}"; fi
    done <<< "$VIBE_NPX_GROUPS"
    has_plugin superpowers || echo "  - 安裝 Claude plugin：superpowers（計畫、實作、驗證流程）"
    if has_claude_cli; then
      has_xcodebuildmcp || echo "  - 加入 XcodeBuildMCP（讓 AI 能在模擬器截圖、點擊）"
    fi
    has_routing "$CLAUDE_ROUTING_FILE" || echo "  - 在 ${CLAUDE_ROUTING_FILE} 加一段：這台電腦的 iOS 需求預設走 ios-vibe（有起訖標記，--vibe --uninstall 會移除）"
  fi
  if [ "$USE_CODEX" -eq 1 ]; then
    echo " Codex："
    echo "  - 把本專案的 skill 連結到 ${AGENTS_HOME}/skills、agent 轉成 Codex 格式放到 ${CODEX_HOME}/agents（已有的不覆蓋）"
    while IFS='|' read -r names args; do
      [ -z "$names" ] && continue
      if group_missing "${names}" codex; then echo "  - 安裝 skill：${names}"; fi
    done <<< "$VIBE_NPX_GROUPS_CODEX"
    while IFS='|' read -r name selector why; do
      [ -z "$name" ] && continue
      has_plugin_codex "$name" || echo "  - 安裝 Codex plugin：${name}（${why}）"
    done <<< "$VIBE_CODEX_PLUGINS"
    has_careful_hook || echo "  - 在 ${CODEX_HOOKS_FILE} 加入擋破壞性指令的防呆（要你之後在 Codex 輸入 /hooks 按一次信任）"
    has_routing "$CODEX_ROUTING_FILE" || echo "  - 在 ${CODEX_ROUTING_FILE} 加一段：這台電腦的 iOS 需求預設走 ios-vibe（有起訖標記，--vibe --uninstall 會移除）"
  fi
}

vibe_confirm() {
  [ "$YES" -eq 1 ] && return 0
  if [ -t 0 ]; then
    local ans
    read -r -p "要繼續嗎？[y/N] " ans
    case "$ans" in y|Y|yes|YES) return 0 ;; esac
    echo "沒有做任何變更。"
    return 1
  fi
  echo "沒有加 --yes，這次不動任何東西。先用 --dry-run 看清單，同意後加 --yes 再執行。"
  return 1
}

VIBE_FAILED=0
vibe_run() {
  if ! "$@"; then
    echo "  ⚠️ 沒成功：$*"
    VIBE_FAILED=$((VIBE_FAILED + 1))
  fi
}

write_routing() {
  local file="$1" entry="$2"
  has_routing "$file" && return 0
  mkdir -p "$(dirname "$file")"
  {
    [ -s "$file" ] && printf '\n'
    printf '%s\n' "$ROUTING_BEGIN"
    printf '%s\n' '## iOS 開發預設走 ios-vibe'
    printf '\n'
    printf '%s\n' "這台電腦的使用者不讀 code。任何 iOS app 的開發需求（做新 app、加功能、改畫面、修 bug）一律用 \`ios-vibe\` skill 處理，不要直接用 \`ios-dev\`。使用者明確要求 ${entry} 時例外。"
    printf '%s\n' "$ROUTING_END"
  } >> "$file"
  echo "  已寫入全域預設路由：${file}"
}

remove_routing() {
  local file="$1" tmp
  [ -f "$file" ] || return 0
  has_routing "$file" || return 0
  tmp="$(mktemp)"
  awk -v b="ios-vibe:begin" -v e="ios-vibe:end" '
    index($0, b) { skip = 1; next }
    skip && index($0, e) { skip = 0; next }
    !skip { print }
  ' "$file" > "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
  echo "  已移除全域預設路由：${file}"
}

# $1＝add|remove：在 Codex 的 hooks.json 加入或移除 careful-ios（合併，不覆蓋別人的 hook）
careful_hook() {
  python3 - "$1" "$CODEX_HOOKS_FILE" "$CAREFUL_HOOK_CMD" <<'PY'
import json, os, sys
action, path, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
data = {}
if os.path.exists(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read().strip()
    if text:
        data = json.loads(text)
hooks = data.setdefault("hooks", {})
groups = hooks.setdefault("PreToolUse", [])

def ours(h):
    return "check-careful-ios.sh" in h.get("command", "")

for g in groups:
    g["hooks"] = [h for h in g.get("hooks", []) if not ours(h)]
groups[:] = [g for g in groups if g.get("hooks")]
if action == "add":
    groups.append({
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": cmd,
                   "statusMessage": "careful-ios：檢查破壞性指令"}],
    })
if not groups:
    hooks.pop("PreToolUse", None)
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
PY
}

vibe_apply_claude() {
  local names args
  echo
  echo "安裝 vibe 版需要的東西（Claude）："
  while IFS='|' read -r names args; do
    [ -z "$names" ] && continue
    if group_missing "$names" claude; then
      local -a argv
      IFS=$'\t' read -r -a argv <<< "$args"
      echo "  安裝 skill：${names}"
      vibe_run "$NPX_BIN" "${argv[@]}"
    fi
  done <<< "$VIBE_NPX_GROUPS"

  if ! has_plugin superpowers; then
    if has_claude_cli; then
      echo "  安裝 plugin：superpowers"
      vibe_run "$CLAUDE_BIN" plugin install superpowers@claude-plugins-official -s user
    else
      echo "  ⚠️ 沒有 claude 指令，無法自動裝 superpowers。請在 Claude 裡輸入：/plugin install superpowers@claude-plugins-official"
      VIBE_FAILED=$((VIBE_FAILED + 1))
    fi
  fi

  if has_claude_cli && ! has_xcodebuildmcp; then
    echo "  加入 XcodeBuildMCP"
    vibe_run "$CLAUDE_BIN" mcp add -s user -e "XCODEBUILDMCP_ENABLED_WORKFLOWS=$XCODEBUILDMCP_WORKFLOWS" XcodeBuildMCP -- npx -y xcodebuildmcp@latest mcp
  fi

  write_routing "$CLAUDE_ROUTING_FILE" '`/ios-dev`'
}

vibe_apply_codex() {
  local names args name selector why
  echo
  echo "安裝 vibe 版需要的東西（Codex）："
  while IFS='|' read -r names args; do
    [ -z "$names" ] && continue
    if group_missing "$names" codex; then
      local -a argv
      IFS=$'\t' read -r -a argv <<< "$args"
      echo "  安裝 skill：${names}"
      vibe_run "$NPX_BIN" "${argv[@]}"
    fi
  done <<< "$VIBE_NPX_GROUPS_CODEX"

  while IFS='|' read -r name selector why; do
    [ -z "$name" ] && continue
    has_plugin_codex "$name" && continue
    if has_codex_cli; then
      echo "  安裝 Codex plugin：${name}"
      vibe_run "$CODEX_BIN" plugin add "$selector"
    else
      echo "  ⚠️ 沒有 codex 指令，無法自動裝 ${name}。請在 Codex 桌面 app 的 Plugins 裡搜尋並安裝「${name}」。"
      VIBE_FAILED=$((VIBE_FAILED + 1))
    fi
  done <<< "$VIBE_CODEX_PLUGINS"

  # plugin 帶來的 skill 裝好後再轉一次 agent，讓 agent 讀得到它們的路徑
  vibe_run codex_gen_agents

  if ! has_careful_hook; then
    vibe_run careful_hook add
    echo "  已加入防呆：${CODEX_HOOKS_FILE}"
  fi

  write_routing "$CODEX_ROUTING_FILE" '`$ios-dev`'
}

vibe_summary() {
  echo
  if [ "$VIBE_FAILED" -gt 0 ]; then
    echo "vibe 版有 ${VIBE_FAILED} 項沒裝成功，上面有標 ⚠️。把這段輸出貼給 AI，它會帶你補裝。"
  else
    echo "vibe 版需要的東西都裝好了。"
  fi
  if [ "$USE_CLAUDE" -eq 1 ]; then
    echo "  Claude：重新打開 Claude，輸入 /ios-vibe 加上你想做的 app 就能開始。"
  fi
  if [ "$USE_CODEX" -eq 1 ]; then
    echo "  Codex：重新打開 Codex，先輸入 /hooks，把「careful-ios」那一條設為信任（只要做一次），再輸入 \$ios-vibe 加上你想做的 app。"
  fi
}

vibe_check() {
  echo
  echo "vibe 版檢查："
  if [ "${VIBE_SKIP_PREREQ:-0}" = "1" ] || xcodebuild -version >/dev/null 2>&1 || ls -d /Applications/Xcode*.app >/dev/null 2>&1; then
    echo "  ✓ Xcode"
  else
    echo "  ✗ Xcode — 從 App Store 安裝"
  fi
  if python3 -c 'pass' >/dev/null 2>&1; then echo "  ✓ python3"; else echo "  ✗ python3 — 裝好 Xcode 後通常就有"; fi
  if [ "$USE_CLAUDE" -eq 1 ]; then
    if has_claude_cli; then
      if has_xcodebuildmcp; then echo "  ✓ Claude：XcodeBuildMCP"; else echo "  ✗ Claude：XcodeBuildMCP — 沒有也能驗證，只是 AI 不能即時截圖與點擊"; fi
    else
      echo "  - Claude：沒有 claude 指令，略過 XcodeBuildMCP 檢查（桌面 app 用內建的模擬器面板）"
    fi
    if has_routing "$CLAUDE_ROUTING_FILE"; then echo "  ✓ Claude：全域預設路由"; else echo "  ✗ Claude：全域預設路由 — 沒有也能用，只是要每次輸入 /ios-vibe"; fi
  fi
  if [ "$USE_CODEX" -eq 1 ]; then
    if has_plugin_codex build-ios-apps; then echo "  ✓ Codex：build-ios-apps plugin"; else echo "  ✗ Codex：build-ios-apps plugin — 沒有也能驗證，只是 AI 不能即時截圖與點擊"; fi
    if has_careful_hook; then echo "  ✓ Codex：careful-ios 防呆（記得在 /hooks 設為信任）"; else echo "  ✗ Codex：careful-ios 防呆"; fi
    if has_routing "$CODEX_ROUTING_FILE"; then echo "  ✓ Codex：全域預設路由"; else echo "  ✗ Codex：全域預設路由 — 沒有也能用，只是要每次輸入 \$ios-vibe"; fi
  fi
}

# ---------- 主流程 ----------

if [ "$MODE" = "check" ]; then
  [ "$USE_CLAUDE" -eq 1 ] && check_deps claude
  [ "$USE_CODEX" -eq 1 ] && check_deps codex
  [ "$VIBE" -eq 1 ] && vibe_check
  exit 0
fi

if [ "$VIBE" -eq 1 ] && [ "$MODE" = "install" ]; then
  vibe_prereq || exit 2
  vibe_plan
  [ "$DRY" -eq 1 ] && exit 0
  vibe_confirm || exit 1
fi

SKIPPED=0

if [ "$USE_CLAUDE" -eq 1 ]; then
  [ "$MODE" = "uninstall" ] || mkdir -p "$CLAUDE_HOME/skills" "$CLAUDE_HOME/agents"
  echo "Claude（${CLAUDE_HOME}）："
  for dir in "$REPO"/skills/*/; do
    name="$(basename "$dir")"
    if [ "$MODE" = "uninstall" ]; then
      unlink_if_ours "$REPO/skills/$name" "$CLAUDE_HOME/skills/$name"
    else
      link "$REPO/skills/$name" "$CLAUDE_HOME/skills/$name"
    fi
  done
  for file in "$REPO"/agents/*.md; do
    name="$(basename "$file")"
    if [ "$MODE" = "uninstall" ]; then
      unlink_if_ours "$file" "$CLAUDE_HOME/agents/$name"
    else
      link "$file" "$CLAUDE_HOME/agents/$name"
    fi
  done
fi

if [ "$USE_CODEX" -eq 1 ]; then
  [ "$MODE" = "uninstall" ] || mkdir -p "$AGENTS_HOME/skills" "$CODEX_HOME/agents"
  echo "Codex（${AGENTS_HOME}/skills、${CODEX_HOME}/agents）："
  for dir in "$REPO"/skills/*/; do
    name="$(basename "$dir")"
    if [ "$MODE" = "uninstall" ]; then
      unlink_if_ours "$REPO/skills/$name" "$AGENTS_HOME/skills/$name"
    elif [ -e "$CODEX_HOME/skills/$name" ] && ! { [ -L "$CODEX_HOME/skills/$name" ] && [ "$(readlink "$CODEX_HOME/skills/$name")" = "$REPO/skills/$name" ]; }; then
      # Codex 也讀 ~/.codex/skills；那裡已有同名的別的版本，再裝一份會變成兩個同名 skill
      echo "  跳過    ${AGENTS_HOME}/skills/${name}（${CODEX_HOME}/skills 已有同名的別的版本）"
      SKIPPED=$((SKIPPED + 1))
    else
      link "$REPO/skills/$name" "$AGENTS_HOME/skills/$name"
    fi
  done
  if [ "$MODE" = "uninstall" ]; then
    codex_remove_agents
  else
    codex_gen_agents || echo "  ⚠️ agent 轉檔沒成功：Codex 上審查 agent 暫時不能用。"
  fi
fi

if [ "$MODE" = "uninstall" ] && [ "$VIBE" -eq 1 ]; then
  if [ "$USE_CLAUDE" -eq 1 ]; then remove_routing "$CLAUDE_ROUTING_FILE"; fi
  if [ "$USE_CODEX" -eq 1 ]; then
    remove_routing "$CODEX_ROUTING_FILE"
    if has_careful_hook; then careful_hook remove; echo "  已移除防呆：${CODEX_HOOKS_FILE}"; fi
  fi
  echo "  （相依套件、plugin 與 XcodeBuildMCP 可能也被別的工具用到，不會自動移除。）"
fi

if [ "$MODE" != "uninstall" ]; then
  if [ "$VIBE" -eq 1 ]; then
    [ "$USE_CLAUDE" -eq 1 ] && vibe_apply_claude
    [ "$USE_CODEX" -eq 1 ] && vibe_apply_codex
    vibe_summary
  fi
  if [ "$USE_CLAUDE" -eq 1 ] && [ "$CLAUDE_HOME" != "$HOME/.claude" ]; then
    echo
    echo "注意：Claude 的 agent 檔裡寫死 ~/.claude/skills/…，裝到別的位置要自己改那幾個路徑。"
  fi
  if [ "$SKIPPED" -gt 0 ]; then
    echo
    echo "有 ${SKIPPED} 個目標被跳過。跳過的那幾個若不是本 repo 的版本，行為可能對不上。"
  fi
  [ "$USE_CLAUDE" -eq 1 ] && check_deps claude
  [ "$USE_CODEX" -eq 1 ] && check_deps codex
fi
exit 0

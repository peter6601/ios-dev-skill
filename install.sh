#!/bin/bash
# 把本 repo 的 skill 與 agent symlink 進 ~/.claude，然後檢查相依的 skill／plugin 裝了沒。
# 已存在且不是指向本 repo 的目標一律跳過，不覆蓋。
#
#   ./install.sh              安裝＋檢查相依
#   ./install.sh --check      只檢查相依，不動任何檔案
#   ./install.sh --uninstall  移除（只移除指向本 repo 的 symlink）
#   CLAUDE_HOME=/path ./install.sh   裝到別的位置（預設 ~/.claude）
#
# vibe 版（給不讀 code 的使用者，見 VIBE.md）：
#   ./install.sh --vibe --dry-run   列出會做的事，不動任何東西
#   ./install.sh --vibe --yes       照清單全部做完（相依套件、模擬器工具、全域預設路由）
#   ./install.sh --vibe --check     多檢查 vibe 需要的東西
#   ./install.sh --vibe --uninstall 另外移除全域設定裡 ios-vibe 寫入的那一段
#   目前只處理 Claude Code；Codex 版之後加入。
#   測試用：NPX_BIN、CLAUDE_BIN 可換成假指令；VIBE_SKIP_PREREQ=1 略過 Xcode 檢查。

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
NPX_BIN="${NPX_BIN:-npx}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

MODE=install
VIBE=0
YES=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --check) MODE=check ;;
    --uninstall) MODE=uninstall ;;
    --vibe) VIBE=1 ;;
    --yes|-y) YES=1 ;;
    --dry-run) DRY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "不認得的參數：$arg"; usage; exit 2 ;;
  esac
done
if [ "$DRY" -eq 1 ] && [ "$VIBE" -eq 0 ]; then
  echo "--dry-run 只能搭配 --vibe 使用。"
  exit 2
fi

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

# skill 三種安裝形狀都算裝了：
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

check_deps() {
  local missing_required=0 missing_other=0
  echo
  echo "相依檢查（${CLAUDE_HOME}）："
  while IFS='|' read -r tier kind name why; do
    [ -z "$tier" ] && continue
    local ok=1
    if [ "$kind" = "plugin" ]; then has_plugin "$name" || ok=0; else has_skill "$name" || ok=0; fi
    if [ "$ok" -eq 1 ]; then
      echo "  ✓ [$tier] $name"
    else
      echo "  ✗ [$tier] $name — $why"
      if [ "$tier" = "必裝" ]; then missing_required=$((missing_required + 1)); else missing_other=$((missing_other + 1)); fi
    fi
  done <<< "$DEPS"
  echo
  if [ "$missing_required" -gt 0 ]; then
    echo "缺 $missing_required 個必裝相依：/ios-dev 會啟動，但主線走不完。安裝指令在 README「安裝」的第 1 步。"
  elif [ "$missing_other" -gt 0 ]; then
    echo "必裝的都在。另有 $missing_other 個建議／選配沒裝——/ios-dev 進場時會在確認畫面提醒，並改走 router §9 的替代路徑。"
  else
    echo "相依都裝好了。"
  fi
}

# ---------- vibe 版 ----------

ROUTING_BEGIN='<!-- ios-vibe:begin（由 ios-dev-skill 的 install.sh --vibe 寫入；install.sh --vibe --uninstall 會移除） -->'
ROUTING_END='<!-- ios-vibe:end -->'
ROUTING_FILE="$CLAUDE_HOME/CLAUDE.md"
XCODEBUILDMCP_WORKFLOWS='simulator,simulator-management,ui-automation'

# 每列：這組提供的 skill（空白分隔）|npx 參數（Tab 分隔）
VIBE_NPX_GROUPS='
swift-architecture-skill|skills	add	https://github.com/efremidze/swift-architecture-skill	-a	claude-code	-g	-y
swift-concurrency|skills	add	https://github.com/AvdLee/Swift-Concurrency-Agent-Skill	-a	claude-code	-g	-y
swiftui-expert-skill|skills@latest	add	https://github.com/AvdLee/SwiftUI-Agent-Skill	--skill	swiftui-expert-skill	-a	claude-code	-g	-y
swiftui-specialist swiftui-whats-new-27|skills	add	superagents-lab/xcode27-skills	--skill	swiftui-specialist	--skill	swiftui-whats-new-27	-a	claude-code	-g	-y
swiftui-ui-patterns swiftui-view-refactor swiftui-performance-audit bug-hunt-swarm review-swarm orchestrate-batch-refactor|skills	add	https://github.com/Dimillian/Skills	--skill	swiftui-ui-patterns	--skill	swiftui-view-refactor	--skill	swiftui-performance-audit	--skill	bug-hunt-swarm	--skill	review-swarm	--skill	orchestrate-batch-refactor	-a	claude-code	-g	-y
'

has_claude_cli() { command -v "$CLAUDE_BIN" >/dev/null 2>&1; }
has_routing() { [ -f "$ROUTING_FILE" ] && grep -qF 'ios-vibe:begin' "$ROUTING_FILE"; }
has_xcodebuildmcp() { has_claude_cli && "$CLAUDE_BIN" mcp get XcodeBuildMCP >/dev/null 2>&1; }

group_missing() {
  local names="$1" n
  for n in $names; do has_skill "$n" || return 0; done
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
  if [ ! -d "$CLAUDE_HOME" ] && ! has_claude_cli; then
    echo "找不到 Claude Code（沒有 ${CLAUDE_HOME}，也沒有 claude 指令）。請先安裝 Claude 桌面 app 或 Claude Code。"
    return 1
  fi
  return 0
}

vibe_plan() {
  echo "vibe 版會做這些事："
  echo "  - 把本專案的 skill 與 agent 連結到 ${CLAUDE_HOME}（已有的不覆蓋）"
  local names args
  while IFS='|' read -r names args; do
    [ -z "$names" ] && continue
    if group_missing "${names}"; then echo "  - 安裝 skill：${names}"; fi
  done <<< "$VIBE_NPX_GROUPS"
  has_plugin superpowers || echo "  - 安裝 Claude plugin：superpowers（計畫、實作、驗證流程）"
  if has_claude_cli; then
    has_xcodebuildmcp || echo "  - 加入 XcodeBuildMCP（讓 AI 能在模擬器截圖、點擊）"
  fi
  has_routing || echo "  - 在 ${ROUTING_FILE} 加一段：這台電腦的 iOS 需求預設走 ios-vibe（有起訖標記，--vibe --uninstall 會移除）"
  if command -v codex >/dev/null 2>&1; then
    echo "  （偵測到 Codex：Codex 版安裝會在之後的版本加入，這次只處理 Claude。）"
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

vibe_apply() {
  echo
  echo "安裝 vibe 版需要的東西："
  local names args
  while IFS='|' read -r names args; do
    [ -z "$names" ] && continue
    if group_missing "$names"; then
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

  if ! has_routing; then
    mkdir -p "$CLAUDE_HOME"
    {
      [ -s "$ROUTING_FILE" ] && printf '\n'
      printf '%s\n' "$ROUTING_BEGIN"
      printf '%s\n' '## iOS 開發預設走 ios-vibe'
      printf '\n'
      printf '%s\n' '這台電腦的使用者不讀 code。任何 iOS app 的開發需求（做新 app、加功能、改畫面、修 bug）一律用 `ios-vibe` skill 處理，不要直接用 `ios-dev`。使用者明確要求 `/ios-dev` 時例外。'
      printf '%s\n' "$ROUTING_END"
    } >> "$ROUTING_FILE"
    echo "  已寫入全域預設路由：${ROUTING_FILE}"
  fi

  echo
  if [ "$VIBE_FAILED" -gt 0 ]; then
    echo "vibe 版有 ${VIBE_FAILED} 項沒裝成功，上面有標 ⚠️。把這段輸出貼給 AI，它會帶你補裝。"
  else
    echo "vibe 版需要的東西都裝好了。重新打開 Claude，輸入 /ios-vibe 加上你想做的 app 就能開始。"
  fi
}

vibe_remove_routing() {
  [ -f "$ROUTING_FILE" ] || return 0
  has_routing || return 0
  local tmp
  tmp="$(mktemp)"
  awk -v b="ios-vibe:begin" -v e="ios-vibe:end" '
    index($0, b) { skip = 1; next }
    skip && index($0, e) { skip = 0; next }
    !skip { print }
  ' "$ROUTING_FILE" > "$tmp"
  cat "$tmp" > "$ROUTING_FILE"
  rm -f "$tmp"
  echo "  已移除全域預設路由：${ROUTING_FILE}"
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
  if has_claude_cli; then
    if has_xcodebuildmcp; then echo "  ✓ XcodeBuildMCP"; else echo "  ✗ XcodeBuildMCP — 沒有也能驗證，只是 AI 不能即時截圖與點擊"; fi
  else
    echo "  - 沒有 claude 指令，略過 XcodeBuildMCP 檢查（桌面 app 用內建的模擬器面板）"
  fi
  if has_routing; then echo "  ✓ 全域預設路由（${ROUTING_FILE}）"; else echo "  ✗ 全域預設路由 — 沒有也能用，只是要每次輸入 /ios-vibe"; fi
}

if [ "$MODE" = "check" ]; then
  check_deps
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
mkdir -p "$CLAUDE_HOME/skills" "$CLAUDE_HOME/agents"

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

if [ "$MODE" = "uninstall" ] && [ "$VIBE" -eq 1 ]; then
  vibe_remove_routing
  echo "  （相依套件、plugin 與 XcodeBuildMCP 可能也被別的工具用到，不會自動移除。）"
fi

if [ "$MODE" != "uninstall" ]; then
  [ "$VIBE" -eq 1 ] && vibe_apply
  if [ "$CLAUDE_HOME" != "$HOME/.claude" ]; then
    echo
    echo "注意：agent 檔裡寫死 ~/.claude/skills/…，裝到別的位置要自己改那幾個路徑。"
  fi
  if [ "$SKIPPED" -gt 0 ]; then
    echo
    echo "有 $SKIPPED 個目標被跳過。agent 讀的是 ~/.claude/skills/ios-dev 等路徑，"
    echo "跳過的那幾個若不是本 repo 的版本，行為可能對不上。"
  fi
  check_deps
fi

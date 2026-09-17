#!/bin/bash
# 把本 repo 的 skill 與 agent symlink 進 ~/.claude，然後檢查相依的 skill／plugin 裝了沒。
# 已存在且不是指向本 repo 的目標一律跳過，不覆蓋。
#
#   ./install.sh              安裝＋檢查相依
#   ./install.sh --check      只檢查相依，不動任何檔案
#   ./install.sh --uninstall  移除（只移除指向本 repo 的 symlink）
#   CLAUDE_HOME=/path ./install.sh   裝到別的位置（預設 ~/.claude）

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
MODE="${1:-install}"

link() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "  已安裝  $dst"
  elif [ -e "$dst" ] || [ -L "$dst" ]; then
    echo "  跳過    $dst（已存在，不是本 repo 的 symlink；要換請自己先移走）"
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

# skill 可能裝在 skills/ 或 commands/（兩個位置 Claude Code 都會讀）
has_skill() {
  [ -e "$CLAUDE_HOME/skills/$1/SKILL.md" ] || [ -e "$CLAUDE_HOME/commands/$1/SKILL.md" ]
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
選配|skill|app-store-preflight|store-preflight-auditor 的規則庫
選配|skill|xcode-project-analyzer|build-analyzer 用
選配|skill|xcode-compilation-analyzer|build-analyzer 用
選配|skill|spm-build-analysis|build-analyzer 用
'

check_deps() {
  local missing_required=0 missing_other=0
  echo
  echo "相依檢查（$CLAUDE_HOME）："
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
    echo "缺 $missing_required 個必裝相依：/ios-dev 會啟動，但主線走不完。安裝指令在 README 的「先裝相依」。"
  elif [ "$missing_other" -gt 0 ]; then
    echo "必裝的都在。另有 $missing_other 個建議／選配沒裝——/ios-dev 進場時會在確認畫面提醒，並改走 router §9 的替代路徑。"
  else
    echo "相依都裝好了。"
  fi
}

if [ "$MODE" = "--check" ]; then
  check_deps
  exit 0
fi

SKIPPED=0
mkdir -p "$CLAUDE_HOME/skills" "$CLAUDE_HOME/agents"

for dir in "$REPO"/skills/*/; do
  name="$(basename "$dir")"
  if [ "$MODE" = "--uninstall" ]; then
    unlink_if_ours "$REPO/skills/$name" "$CLAUDE_HOME/skills/$name"
  else
    link "$REPO/skills/$name" "$CLAUDE_HOME/skills/$name"
  fi
done

for file in "$REPO"/agents/*.md; do
  name="$(basename "$file")"
  if [ "$MODE" = "--uninstall" ]; then
    unlink_if_ours "$file" "$CLAUDE_HOME/agents/$name"
  else
    link "$file" "$CLAUDE_HOME/agents/$name"
  fi
done

if [ "$MODE" != "--uninstall" ]; then
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

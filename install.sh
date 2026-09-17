#!/bin/bash
# 把本 repo 的 skill 與 agent symlink 進 ~/.claude。
# 已存在且不是指向本 repo 的目標一律跳過，不覆蓋。
#
#   ./install.sh              安裝
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
  echo
  echo "完成。第三方依賴見 README 的「依賴」一節。"
fi

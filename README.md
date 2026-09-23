# ios-dev-skill

給 [Claude Code](https://claude.com/claude-code) 與 [Codex](https://developers.openai.com/codex) 的 iOS／SwiftUI 開發工具組，涵蓋需求規劃、實作、除錯與審查。依你讀不讀程式碼，有兩個入口：

| 你是 | 從這裡開始 |
|---|---|
| **不寫 code，想做出自己的 iPhone app** | 讀 [VIBE.md](VIBE.md)：把一段話貼給 AI 就能安裝，接著用白話說你想做什麼 |
| **iOS 工程師** | 往下讀：用 `/ios-dev` 從需求規劃、實作一路走到審查 |

---

以下給 iOS 工程師。在 Claude Code 輸入需求即可開始（Codex 用 `$ios-dev`，需求寫在同一則訊息）：

```text
/ios-dev 在設定頁新增匯出功能
```

它會依任務選擇需要的 skill（工作指引）與 agent（審查助手），列出流程供你確認，再開始執行。需要改變功能行為時，會先確認架構影響。

本專案整理自作者的日常工作流，已移除公司、專案與個人路徑資訊。

## 安裝

需要 Claude Code 或 Codex（兩個都裝也可以）、Git，以及能執行 `npx` 的 Node.js 環境。安裝程式與量測、測試腳本另需 Python 3。

### 1. 安裝必要套件

本專案會呼叫其他 skill，請先在終端機安裝：

```bash
npx skills add https://github.com/efremidze/swift-architecture-skill -a claude-code -g -y
npx skills add https://github.com/AvdLee/Swift-Concurrency-Agent-Skill -a claude-code -g -y
npx skills@latest add https://github.com/AvdLee/SwiftUI-Agent-Skill --skill swiftui-expert-skill -a claude-code -g -y
```

再到 Claude Code 安裝 Superpowers：

```text
/plugin install superpowers@claude-plugins-official
```

用 Codex 的話，上面三行的 `-a claude-code` 改成 `-a codex`，Superpowers 改用：

```bash
codex plugin add superpowers@openai-curated
```

這四個套件（`swift-architecture-skill`、`swift-concurrency`、`swiftui-expert-skill`、`superpowers`）分別提供架構、並行處理、SwiftUI，以及計畫、測試與驗證指引。缺少任一項，主要流程就無法完整執行。

### 2. 安裝本專案

```bash
git clone https://github.com/peter6601/ios-dev-skill.git
cd ios-dev-skill
./install.sh
```

安裝程式會偵測這台電腦有 Claude Code、Codex 或兩者，每邊各裝一份，並列出缺少的套件：

- **Claude Code**：skill 與 agent 連結到 `~/.claude/skills`、`~/.claude/agents`。
- **Codex**：skill 連結到 `~/.agents/skills`；agent 由 `scripts/gen-codex-agents.py` 轉成 Codex 的 `.toml` 格式放到 `~/.codex/agents`，agent 裡引用的 skill 路徑會換成這台電腦實際的位置。`~/.codex/skills` 已有同名的別的版本時會跳過，避免 Codex 看到兩個同名 skill。

已有的檔案不會被覆蓋；若顯示「跳過」，請確認是否為你要使用的版本。安裝使用符號連結，請保留這個專案目錄。六個審查 agent 開工時會讀 `swiftui-expert-skill`，請確認它已安裝。

<details>
<summary>Codex 上的差異</summary>

- 呼叫方式是 `$ios-dev`，不支援 `/ios-dev <描述>` 這種帶參數的寫法。
- Codex 一般模式沒有選項式提問工具，確認畫面改成列出編號選項，回數字即可；Plan 模式會用 `request_user_input`。
- `careful-ios` 的防呆寫在 skill 設定裡，Codex 會忽略。要在 Codex 擋破壞性指令，用 `./install.sh --vibe` 把同一支檢查腳本掛進 `~/.codex/hooks.json`，再到 Codex 輸入 `/hooks` 設為信任；Codex 只能擋下、不能先問。
- `swiftui-ui-patterns`、`swiftui-view-refactor`、`swiftui-performance-audit` 由官方 Build iOS Apps plugin 提供（`codex plugin add build-ios-apps@openai-curated`，內含 XcodeBuildMCP）。
- review 路線 A（`consensus-review`）的修正步驟要呼叫 Claude 的 CLI，只有 Codex 時不能用，改走路線 B。

</details>

| 指令 | 用途 |
|---|---|
| `./install.sh --check` | 只檢查相依套件 |
| `./install.sh --uninstall` | 只移除本專案裝的連結與產生的檔案 |
| `./install.sh --platform=claude` | 不自動偵測，只裝指定平台（`claude`／`codex`／`both`） |
| `./install.sh --vibe --dry-run` | vibe 版安裝：列出會做的事；加 `--yes` 才執行（見 [VIBE.md](VIBE.md)） |

## 使用方式

在 iOS 專案中開啟 Claude Code，用 `/ios-dev` 描述需求（Codex 用 `$ios-dev`）：

```text
/ios-dev 規劃一個記帳 App
/ios-dev 修正登入後畫面卡住的問題
/ios-dev 改善首頁捲動效能
/ios-dev tickets/T3.md
```

工具會依任務安排流程，不需要自己挑 skill：

| 任務 | 處理方式 |
|---|---|
| 新專案／大功能 | 釐清需求、設計架構，再寫計畫或拆成 ticket |
| 小功能 | 確認需求與架構影響，產出短計畫，確認後再啟動實作 |
| 純畫面調整 | 確認狀態來源，再實作與打磨 |
| 修 bug | 先找出原因，再修正 |
| 效能優化 | 先量測，修改後再比較 |
| 重構 | 記錄現況、釐清責任，逐步修改並驗證 |
| 接手 ticket | 依既有規格實作；缺少的規劃才補上 |

規劃階段只產文件，實作階段才改程式。需要拆分模組時，由 `phase-workflow` 產生 ticket，再用 `/ios-dev tickets/<檔名>.md` 接續開發。完整規則見[流程對照表](skills/ios-dev/references/skill-router.md)。

## 內含工具

**12 個 skill**，分工如下：

| Skill | 用途 |
|---|---|
| [ios-dev](skills/ios-dev/SKILL.md) | 統一入口，選擇流程與工具 |
| [ios-vibe](skills/ios-vibe/SKILL.md) | 給不讀 code 的人的入口：背後照跑 `ios-dev`，只問產品問題，每次給試用卡 |
| [office-hours](skills/office-hours/SKILL.md) | 釐清產品方向與最小可行版本 |
| [phase-workflow](skills/phase-workflow/SKILL.md) | 將需求整理成規格與 ticket |
| [ios-investigate](skills/ios-investigate/SKILL.md) | 找出 bug 原因並驗證修正 |
| [ios-review](skills/ios-review/SKILL.md) | 審查程式碼與修正問題 |
| [ios-distill](skills/ios-distill/SKILL.md) | 簡化 View、狀態與導航結構 |
| [ios-polish](skills/ios-polish/SKILL.md) | 調整間距、對齊、動畫與互動 |
| [ios-critique](skills/ios-critique/SKILL.md) | 檢查介面設計與使用體驗 |
| [ios-harden](skills/ios-harden/SKILL.md) | 補強錯誤處理、多語系與無障礙支援 |
| [localize-strings](skills/localize-strings/SKILL.md) | 將寫死的字串整理到 String Catalog |
| [careful-ios](skills/careful-ios/SKILL.md) | 在破壞性操作前提出警告 |

另附 **9 個唯讀 agent**，負責程式碼、UX、錯誤與邊界狀態、架構、並行處理、效能、追蹤資料、建置與上架檢查。它們只回報問題，不修改程式碼；清單見 [`agents/`](agents/)。

## 進階設定

<details>
<summary>建議與選配套件</summary>

以下套件依需求加裝。缺少時，`/ios-dev` 會說明限制或替代流程。

| 類型 | 套件／來源 | 用途 |
|---|---|---|
| 建議 | [xcode27-skills](https://github.com/superagents-lab/xcode27-skills)：`swiftui-specialist`、`swiftui-whats-new-27` | SwiftUI 實作指引 |
| 建議 | [Dimillian/Skills](https://github.com/Dimillian/Skills)：`swiftui-ui-patterns`、`swiftui-view-refactor`、`swiftui-performance-audit`、`review-swarm`、`bug-hunt-swarm`、`orchestrate-batch-refactor` | 畫面設計、重構、效能與審查 |
| 建議 | [iOS-Accessibility-Agent-Skill](https://github.com/dadederk/iOS-Accessibility-Agent-Skill)：`ios-accessibility` | 無障礙審查標準（`resilience-auditor`、`ios-harden` 讀）；未安裝時只照 `swiftui-expert-skill` 審 |
| 建議 | [mattpocock/skills](https://github.com/mattpocock/skills)：`mattpocock-skills` plugin | 需求訪談；未安裝時改用 Superpowers |
| 建議 | [ai-review](https://github.com/peter6601/ai-review)：`consensus-plan`、`consensus-review` | Codex 文件與程式碼交叉審查 |
| 選配 | [app-store-preflight-skills](https://github.com/truongduy2611/app-store-preflight-skills)：`app-store-preflight-skills` | App Store 送審前檢查 |
| 選配 | [Xcode-Build-Optimization-Agent-Skill](https://github.com/AvdLee/Xcode-Build-Optimization-Agent-Skill)：`xcode-project-analyzer`、`xcode-compilation-analyzer`、`spm-build-analysis`、`xcode-build-fixer` | 建置分析與修正；只分析可不裝 fixer |
| 選配 | [swiftui-agent-skill](https://github.com/twostraws/swiftui-agent-skill)：`swiftui-pro` | `swiftui-reviewer` 的第二套標準，app 主 target ≥ iOS 17 才用；放 `~/.claude/vendor`，**不要**放進 skills 目錄（會在每個專案自動觸發）|
| 選配 | [app-store-connect-cli-skills](https://github.com/rorkai/app-store-connect-cli-skills)：`asc-*` | App Store Connect 發佈流程 |

常用套件安裝指令：

```bash
npx skills add superagents-lab/xcode27-skills --skill swiftui-specialist --skill swiftui-whats-new-27 -a claude-code -g -y
npx skills add https://github.com/Dimillian/Skills --skill swiftui-ui-patterns --skill swiftui-view-refactor --skill swiftui-performance-audit --skill bug-hunt-swarm --skill review-swarm --skill orchestrate-batch-refactor -a claude-code -g -y
npx skills add https://github.com/dadederk/iOS-Accessibility-Agent-Skill --skill ios-accessibility -a claude-code -g -y
git clone https://github.com/twostraws/swiftui-agent-skill ~/.claude/vendor/twostraws-swiftui-agent-skill
```

Claude Code 內安裝訪談工具：

```text
/plugin install mattpocock-skills@claude-plugins-official
```

`-a claude-code` 指定安裝到 Claude Code，`-g` 表示全域安裝。專案專用的 framework skill 可從 [swift-ios-skills](https://github.com/dpearson2699/swift-ios-skills) 挑選，省略 `-g` 即可安裝到專案。

`ai-review` 的指令與參數以其 `main` 分支為準。

</details>

<details>
<summary>規劃文件與個人筆記</summary>

- 未指定 workspace 時，文件存放在 iOS 專案：一般計畫放 `docs/plans/`，模組規劃與 ticket 放 `docs/features/<功能>/`。
- 也可指定外部 workspace 存放文件；不必使用 Obsidian，只有 `board.base` 看板需要它。
- `phase-workflow` 預設只產檔並列出差異；commit、merge 或建立 PR 需要明確指示。
- 流程提到的 `second-brain`、`work-log-writer` 是作者未公開的個人工具，未安裝時可跳過。

</details>

<details>
<summary>量測、測試與流程評測</summary>

在本專案根目錄執行。SwiftUI 量測腳本可獨立使用，統計 View 的 body 行數、`@State` 與 `isPresented` 數量：

```bash
python3 skills/ios-dev/scripts/swiftui-metrics.py path/to/YourApp --top 15
```

本機檢查與測試，不呼叫模型：

```bash
python3 skills/ios-dev/scripts/validate-router.py --workspace . --skill-dir skills/ios-dev
python3 -m unittest discover -s skills/ios-dev/scripts -p "test_*.py"
python3 skills/ios-dev/evals/test_run_evals.py
python3 skills/careful-ios/bin/test_check_careful_ios.py
python3 -m unittest discover -s skills/ios-vibe/scripts -p "test_*.py"
python3 skills/ios-vibe/scripts/check-touchpoints.py
python3 scripts/test_gen_codex_agents.py
python3 test_install_sh.py
bash -n install.sh
./install.sh --check
```

修改流程對照表後，可用 Claude 評測 19 個情境。預設只列計畫，不呼叫模型；以下費用與時間為原版估計：

```bash
python3 skills/ios-dev/evals/run_evals.py                  # 列出計畫與結果是否過期
python3 skills/ios-dev/evals/run_evals.py --probe-sandbox  # 檢查沙箱，約 US$0.05
python3 skills/ios-dev/evals/run_evals.py --run            # 完整評測，約 US$20–25、10–15 分鐘
```

評測使用產生的測試專案與沙箱，結果不納入版控。

</details>

## 致謝與授權

本專案採 MIT 授權。部分 skill 改寫自 [gstack](https://github.com/garrytan/gstack) 與 [Impeccable](https://github.com/pbakaus/impeccable)，並保留原作授權要求。

流程與評測設計另參考 [agent-skills](https://github.com/addyosmani/agent-skills)、[Spec Kit](https://github.com/github/spec-kit)、[mattpocock/skills](https://github.com/mattpocock/skills) 與 [CCPM](https://github.com/automazeio/ccpm)。完整聲明見 [`NOTICE`](NOTICE)、[`LICENSE`](LICENSE) 與 [`LICENSES/`](LICENSES/)。第三方相依套件需另行安裝，本專案未包含其內容。

# ios-dev — iOS 開發工作流的單一入口 skill

給 [Claude Code](https://claude.com/claude-code) 用的 iOS 開發工作流。任何 iOS 需求都從 `/ios-dev` 進：
它先認情境、秀出這次會載入哪些 skill 與派出哪些 agent，你確認一次，再交棒或往下規劃。

這個 repo 是作者自用版本的**去識別化副本**（拿掉了公司、專案與個人路徑），內容與流程照原樣保留。

## 它解決什麼問題

1. **操作型 skill 靠 description 不會自動觸發。** 裝了二十個 iOS skill，實際開工時沒有一個被叫到。
   `/ios-dev` 的 Step 0 把「什麼情境載入什麼」寫成一張表，進場就查表。
2. **架構檢查放在收尾太晚。** 一個 1,700 行的 View 拆過一次、三個月又長回來——因為每次加功能都是
   「先加上去再說」。這裡把架構決策**前移到開發前**：任何會改變行為的任務都先答五個問題，
   結論是「直接擴充／局部整理／模組邊界」三選一。
3. **用 ticket 數決定流程會判錯。** 兩張 ticket 的新模組需要模組設計；沿既有契約加操作的十張 ticket
   不需要。入場由**責任邊界**決定，ticket 數只決定產幾份文件。

## 七個情境

| # | 情境 | 走法（摘要） |
|---|---|---|
| 1 | 新專案／新模組／大功能 | 產品思考 → grill → 架構形狀 → test cases → 切 ticket |
| 2 | 小功能 | 1 輪 grill → 五問 → test cases → 短 plan → 實作 |
| 3 | 純呈現畫面 | 只答第 3 問（會不會多出第二份真相）→ 直接實作 → polish |
| 4 | 修正 | 先找 root cause，沒找到不修 code |
| 5 | 優化 | 先量 → 改 → 再量；沒數字不動 code |
| 6 | 重構 | 基線 → 責任地圖 → 沿**完整行為**切分逐段改 → 對比 |
| 7 | 接 ticket | 契約已備就直接實作，不回流重新規劃 |

完整的組合表、輕／重閘門、三條 review 路線在 [`skills/ios-dev/references/skill-router.md`](skills/ios-dev/references/skill-router.md)。

## 內容

```
skills/
  ios-dev/
    SKILL.md                              入口：Step 0 路由 ＋ Step 1–8 規劃流程
    references/
      skill-router.md                     情境→組合表、輕／重、review 路線、沒裝時的替代
      architecture-impact-check.md        五問、中型觸發條件、presentation 轉移表、async ownership 契約六格、重構路徑
      handoff-checklist.md                交棒後的收尾清單（情境 3–7）
      plan-template.md                    實作計畫模板（含「架構約束」段與中途檢查點）
    scripts/
      swiftui-metrics.py                  量 SwiftUI View 的四個數字（body 行數、@State 數、isPresented 數、onChange 監看 should*/did*）
      test_swiftui_metrics.py             上面那支的 13 個回歸測試
  ios-critique/SKILL.md                   ux-critique agent 的評分準則（10 維度）
  ios-harden/SKILL.md                     resilience-auditor agent 的檢查準則
agents/
  swiftui-reviewer.md  ux-critique.md  resilience-auditor.md      三個 specialist（review 路線 A 的入場券）
  perf-auditor.md  concurrency-auditor.md  architecture-auditor.md  閘門 auditor（全部唯讀）
  trace-analyzer.md  build-analyzer.md  store-preflight-auditor.md  隨叫隨到
```

`ios-critique` 與 `ios-harden` 一起附上，是因為 `ux-critique`、`resilience-auditor` 兩個 agent 開工時
會整份讀它們當尺；少了這兩份，agent 只剩空殼。

## 安裝

> **只裝這個 repo 不夠。** `ios-dev` 是路由器，它自己不做事，做事的是它叫到的 skill。
> 照下面三步裝；第 3 步的腳本會列出你還缺哪些相依。

### 1. 先裝相依（必裝 4 個）

少了這四個，`/ios-dev` 會啟動但主線走不完：

```bash
# superpowers plugin：writing-plans／subagent-driven-development／TDD／verification
# 在 Claude Code 裡輸入
/plugin install superpowers@claude-plugins-official

# Step 4 架構形狀、async ownership 契約
npx skills add https://github.com/efremidze/swift-architecture-skill -a claude-code -g -y
npx skills add https://github.com/AvdLee/Swift-Concurrency-Agent-Skill -a claude-code -g -y

# 6 個 agent 開工必讀它的 references
git clone https://github.com/AvdLee/SwiftUI-Agent-Skill.git ~/.claude/vendor/SwiftUI-Agent-Skill
ln -s ~/.claude/vendor/SwiftUI-Agent-Skill/swiftui-expert-skill ~/.claude/skills/swiftui-expert-skill
```

`npx skills` 一定要帶 `-a claude-code`：互動模式預設勾的那組 agent 不含 Claude Code，裝了也讀不到。

### 2. 建議裝（缺了該情境會降級）

```bash
# SwiftUI：寫、畫面 pattern、拆 View、效能；swarm 系列
npx skills add superagents-lab/xcode27-skills --skill swiftui-specialist --skill swiftui-whats-new-27 -a claude-code -g -y
npx skills add https://github.com/Dimillian/Skills --skill swiftui-ui-patterns --skill swiftui-view-refactor --skill swiftui-performance-audit --skill bug-hunt-swarm --skill review-swarm --skill orchestrate-batch-refactor -a claude-code -g -y

# grill 系列（Step 3 需求訪談），在 Claude Code 裡輸入
/plugin install mattpocock-skills@claude-plugins-official
```

共識審查（review 路線 A）另見下面「共識審查」一節。

### 3. 裝本 repo

```bash
git clone https://github.com/peter6601/ios-dev-skill.git
cd ios-dev-skill
./install.sh
```

`install.sh` 把 `skills/*` symlink 到 `~/.claude/skills/`、`agents/*.md` symlink 到 `~/.claude/agents/`，
目標已存在就跳過、不覆蓋；**裝完會印一張相依檢查表**（必裝／建議／選配各缺哪些、缺了會怎樣）。

```bash
./install.sh --check       # 只檢查相依，不動任何檔案
./install.sh --uninstall   # 只移除指向本 repo 的 symlink
```

agent 檔裡的路徑寫死 `~/.claude/skills/…`，所以請裝在預設位置。

執行時也有一道提醒：`/ios-dev` 進場會檢查這次情境要用的 skill／agent 裝了沒，缺的寫進確認畫面的
「提醒」行並改走 router §9 的替代路徑——不會默默略過。

量測腳本可以單獨用，不需要 Claude：

```bash
python3 skills/ios-dev/scripts/swiftui-metrics.py path/to/YourApp --top 15
```

## 依賴一覽

| 依賴 | 層級 | 誰用它 | 來源 |
|---|---|---|---|
| `swiftui-expert-skill` | 必裝 | 6 個 agent 都讀它的 references；`trace-analyzer` 跑它的 script | [AvdLee/SwiftUI-Agent-Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill) |
| `swift-architecture-skill` | 必裝 | Step 4、`architecture-auditor` | [efremidze/swift-architecture-skill](https://github.com/efremidze/swift-architecture-skill) |
| `swift-concurrency` | 必裝 | async 契約、`concurrency-auditor` | [AvdLee/Swift-Concurrency-Agent-Skill](https://github.com/AvdLee/Swift-Concurrency-Agent-Skill) |
| `swiftui-specialist`、`swiftui-whats-new-27` | 建議 | 實作 SwiftUI | [superagents-lab/xcode27-skills](https://github.com/superagents-lab/xcode27-skills) |
| `swiftui-ui-patterns`、`swiftui-view-refactor`、`swiftui-performance-audit`、`bug-hunt-swarm`、`review-swarm`、`orchestrate-batch-refactor` | 建議 | 畫面、拆 View、效能、重閘門、除錯、批次重構 | [Dimillian/Skills](https://github.com/Dimillian/Skills) |
| `app-store-preflight` | 選配 | `store-preflight-auditor` | [truongduy2611/app-store-preflight-skills](https://github.com/truongduy2611/app-store-preflight-skills) |
| `xcode-project-analyzer`、`xcode-compilation-analyzer`、`spm-build-analysis`、`xcode-build-fixer` | 選配 | `build-analyzer` | [AvdLee/Xcode-Build-Optimization-Agent-Skill](https://github.com/AvdLee/Xcode-Build-Optimization-Agent-Skill) |
| `asc-*` | 選配 | Phase 4 出貨 | [rorkai/app-store-connect-cli-skills](https://github.com/rorkai/app-store-connect-cli-skills) |
| 專案層 framework skill | 選配 | 靠 description 自動載入 | [dpearson2699/swift-ios-skills](https://github.com/dpearson2699/swift-ios-skills)（裝在專案層，不加 `-g`） |

### Plugin

| Plugin | 用到的 skill |
|---|---|
| [superpowers](https://github.com/obra/superpowers) | `subagent-driven-development`、`writing-plans`、`test-driven-development`、`verification-before-completion`、`brainstorming`、`systematic-debugging` |
| [mattpocock/skills](https://github.com/mattpocock/skills) | `/grill-with-docs`、`/grill-me`、`setup-matt-pocock-skills`（三個都只能使用者打字觸發，模型呼叫不到） |

### 共識審查（review 路線 A）

`consensus-plan`、`consensus-review` 與 `ai-review` CLI 在 [peter6601/ai-review](https://github.com/peter6601/ai-review)，
需要 Codex CLI。沒裝的話走路線 B（純 agent）——三條路線的終點都是人工 Code Review，這一站不因路線而省。

### 本 repo 不含的自用 skill

`SKILL.md` 與 router 仍保留這些名字，沒裝時的替代如下（同一張表在 router §9，那份是執行時讀的）：

| 引用的名字 | 角色 | 沒裝時 |
|---|---|---|
| `office-hours` | Phase 0 產品思考 | `superpowers:brainstorming` |
| `phase-workflow` | design doc／PM spec → 根文件＋ticket bundle | `superpowers:writing-plans` 產根文件，人工切 ticket，每張保留「架構約束」段 |
| `ios-investigate` | 五階段除錯 | `superpowers:systematic-debugging` |
| `ios-review` | 兩輪 fix-first review | 派 `swiftui-reviewer`＋`concurrency-auditor`；路線 C 不可用，最低走 B |
| `ios-polish`／`ios-distill` | 出貨前打磨 | 以 `ux-critique` 的 findings 做一次修復 |
| `careful-ios` | 破壞性指令護欄 | 無替代，人工確認 |
| `second-brain`、`work-log-writer`、`localize-strings` | 紀錄、在地化、維護期知識庫 | 跳過 |

## 幾個用詞

- **workspace**：你放跨 repo 規劃文件的地方（筆記庫或獨立的文件 repo）。沒有就用 iOS repo 的 `docs/`。
- **第二大腦**：一個功能的維護期知識庫（Obsidian MOC ＋ wikilink）。沒有就跳過相關步驟，流程寫的是「有才讀」。
- **§0 架構形狀**：Step 4 的產出，四段——pattern 與理由、模組邊界、state 與 presentation 建模、
  async ownership 契約。它是之後每張 ticket 的稽核尺。
- **輕／重**管的是審查強度；**責任邊界**管的是開發前要產出什麼架構決策。兩者不同軸。

## 跑測試

```bash
python3 -m unittest discover -s skills/ios-dev/scripts -p "test_*.py"
```

## License

MIT。第三方 skill 各自有自己的授權，本 repo 只引用名字，不包含它們的內容。

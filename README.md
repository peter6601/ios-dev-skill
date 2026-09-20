# ios-dev-skill

給 [Claude Code](https://claude.com/claude-code) 的 iOS 開發工作流。所有 iOS 需求都從一個指令進：

```
/ios-dev 我要在設定頁加一個匯出功能
```

它先判斷這是哪種工作、列出這次會用到的 skill 與 agent，你確認一次，它才開始。

> 這是作者自用版本的去識別化副本：公司、專案、個人路徑已拿掉，流程照原樣。

## 三個重點

- **進場查表，不靠運氣。** skill 裝再多，靠 description 自動觸發常常叫不到。這裡把「什麼情境用什麼」寫成一張表。
- **架構決策在寫 code 之前。** 任何會改變行為的任務先答五個問題，結論三選一：直接擴充／局部整理／拉出模組邊界。
- **流程看責任邊界，不看 ticket 數。** 兩張 ticket 的新模組要做模組設計；沿既有契約加操作的十張 ticket 不用。

## 安裝

> ⚠️ **只裝這個 repo 不夠。** `ios-dev` 是路由器，實際做事的是它叫到的其他 skill。請照順序裝。

**1. 先裝 4 個必要相依**（少了主線走不完）

```bash
npx skills add https://github.com/efremidze/swift-architecture-skill -a claude-code -g -y
npx skills add https://github.com/AvdLee/Swift-Concurrency-Agent-Skill -a claude-code -g -y
npx skills@latest add https://github.com/AvdLee/SwiftUI-Agent-Skill --skill swiftui-expert-skill -a claude-code -g -y
```

裝完確認 `~/.claude/skills/swiftui-expert-skill/SKILL.md` 讀得到——6 個 agent 開工就是讀這條路徑。

再到 Claude Code 裡輸入：

```
/plugin install superpowers@claude-plugins-official
```

**2. 裝本 repo**

```bash
git clone https://github.com/peter6601/ios-dev-skill.git
cd ios-dev-skill
./install.sh
```

裝完會印一張**相依檢查表**，告訴你還缺什麼、缺了會怎樣。

**3. 依檢查表補裝其餘的**（見下方「相依一覽」）

| 指令 | 作用 |
|---|---|
| `./install.sh` | symlink 進 `~/.claude/skills` 與 `~/.claude/agents`；已存在的不覆蓋 |
| `./install.sh --check` | 只檢查相依，不動任何檔案 |
| `./install.sh --uninstall` | 只移除指向本 repo 的 symlink |

## 七種情境

| # | 情境 | 它會怎麼走 |
|---|---|---|
| 1 | 新專案／大功能 | 產品思考 → 需求訪談 → 架構形狀 → test cases → 切 ticket |
| 2 | 小功能 | 1 輪訪談 → 五問 → test cases → 短計畫 → 實作 |
| 3 | 純畫面 | 只答「會不會多出第二份真相」→ 實作 → 打磨 |
| 4 | 修 bug | 先找 root cause；沒找到不改 code |
| 5 | 優化 | 先量 → 改 → 再量；沒數字不改 code |
| 6 | 重構 | 基線 → 責任地圖 → 沿完整行為逐段改 → 對比 |
| 7 | 接 ticket | 契約已備就直接做，不重新規劃 |

完整規則在 [`skill-router.md`](skills/ios-dev/references/skill-router.md)。

## 裡面有什麼

**11 個 skill**

| 階段 | Skill | 做什麼 |
|---|---|---|
| 入口 | [`ios-dev`](skills/ios-dev/SKILL.md) | 路由 ＋ 規劃流程 ＋ 4 份 reference ＋ SwiftUI 量測腳本 |
| 開工前 | [`office-hours`](skills/office-hours/SKILL.md) | 產品思考：要解決什麼、給誰用、最小版本是什麼。只產 design doc |
| 規劃 | [`phase-workflow`](skills/phase-workflow/SKILL.md) | 把 design doc 或 PM spec 展開成根文件 ＋ ticket；只規劃不寫 code |
| 除錯 | [`ios-investigate`](skills/ios-investigate/SKILL.md) | 五階段除錯；沒找到 root cause 不准改 code。內建 iOS 常見 bug pattern 表 |
| Review | [`ios-review`](skills/ios-review/SKILL.md) | 上線前兩輪 review；機械式的直接修，要判斷的一次問完 |
| 打磨 | [`ios-distill`](skills/ios-distill/SKILL.md) | 去掉不必要的複雜度：View 結構、State、導航層級 |
| 打磨 | [`ios-polish`](skills/ios-polish/SKILL.md) | 出貨前最後一哩：對齊、間距、互動狀態、動畫 |
| 打磨 | [`ios-critique`](skills/ios-critique/SKILL.md) | 設計審查 10 維度（`ux-critique` agent 讀它當尺） |
| 打磨 | [`ios-harden`](skills/ios-harden/SKILL.md) | 邊界狀態、i18n、Accessibility（`resilience-auditor` agent 讀它當尺） |
| 出貨 | [`localize-strings`](skills/localize-strings/SKILL.md) | 掃硬編碼字串，產 `Localizable.xcstrings` 條目 |
| 護欄 | [`careful-ios`](skills/careful-ios/SKILL.md) | 破壞性指令執行前先警告（force-push、刪專案檔、清 Simulator…），附 hook 腳本 |

**9 個 agent**（全部唯讀，只出報告不改 code）

| 類別 | Agent |
|---|---|
| Review 三人組 | `swiftui-reviewer`、`ux-critique`、`resilience-auditor` |
| 品質閘門 | `architecture-auditor`、`concurrency-auditor`、`perf-auditor` |
| 隨叫隨到 | `trace-analyzer`、`build-analyzer`、`store-preflight-auditor` |

**量測腳本可以單獨用**，不需要 Claude——量每個 SwiftUI View 的 body 行數、`@State` 數、`isPresented` 數：

```bash
python3 skills/ios-dev/scripts/swiftui-metrics.py path/to/YourApp --top 15
```

**改完路由表先跑這兩個自我檢查**（做法借鑑 [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) 的 `evals/`）：

```bash
# 1. 引用完整性：§9 列的名字真的裝著嗎？/指令、§N、「標題」、路徑指得到東西嗎？（不呼叫模型，秒回）
python3 skills/ios-dev/scripts/validate-router.py --workspace . --skill-dir skills/ios-dev

# 2. 路由評測：19 個情境 case 用 headless Claude 實跑 Step 0，比對確認畫面的固定欄位＋模型評審
python3 skills/ios-dev/evals/run_evals.py                 # 只列計畫與過期狀態，不花錢
python3 skills/ios-dev/evals/run_evals.py --probe-sandbox # 先確認沙箱擋得住 repo 外的寫入（約 $0.05）
python3 skills/ios-dev/evals/run_evals.py --run           # 全套約 $20–25、10–15 分鐘
```

評測用程式生成的假 iOS repo 當 fixture，被測的 Claude 跑在沙箱裡（Bash 只能寫那個假 repo、無網路，`/Users` 底下的 Edit／Write 一律拒絕），`results/` 不進版控。改了 case、fixture 或 parser，舊結果會自動標成過期。

## 相依一覽

| 層級 | 名稱 | 缺了會怎樣 | 來源 |
|---|---|---|---|
| **必裝** | `swiftui-expert-skill` | 6 個 agent 開工必讀它，品質閘門跑不起來 | [AvdLee/SwiftUI-Agent-Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill) |
| **必裝** | `superpowers`（plugin） | 沒有寫計畫、TDD、完成前驗證 | [obra/superpowers](https://github.com/obra/superpowers) |
| **必裝** | `swift-architecture-skill` | 產不出架構形狀 | [efremidze/swift-architecture-skill](https://github.com/efremidze/swift-architecture-skill) |
| **必裝** | `swift-concurrency` | 沒有 async 契約的依據 | [AvdLee/Swift-Concurrency-Agent-Skill](https://github.com/AvdLee/Swift-Concurrency-Agent-Skill) |
| 建議 | `swiftui-specialist`、`swiftui-whats-new-27` | 寫 SwiftUI 少了指引 | [superagents-lab/xcode27-skills](https://github.com/superagents-lab/xcode27-skills) |
| 建議 | `swiftui-ui-patterns`、`swiftui-view-refactor`、`swiftui-performance-audit`、`review-swarm`、`bug-hunt-swarm`、`orchestrate-batch-refactor` | 對應情境降級 | [Dimillian/Skills](https://github.com/Dimillian/Skills) |
| 建議 | `mattpocock-skills`（plugin） | 需求訪談改用 `superpowers:brainstorming` | [mattpocock/skills](https://github.com/mattpocock/skills) |
| 建議 | `consensus-plan`、`consensus-review` | 沒有 Codex 交叉審查，改走純 agent 路線 | [peter6601/ai-review](https://github.com/peter6601/ai-review) |
| 選配 | `app-store-preflight-skills` | `store-preflight-auditor` 沒有規則庫 | [truongduy2611/app-store-preflight-skills](https://github.com/truongduy2611/app-store-preflight-skills) |
| 選配 | `xcode-project-analyzer`、`xcode-compilation-analyzer`、`spm-build-analysis` | `build-analyzer` 不能用 | [AvdLee/Xcode-Build-Optimization-Agent-Skill](https://github.com/AvdLee/Xcode-Build-Optimization-Agent-Skill) |
| 選配 | `xcode-build-fixer` | `build-analyzer` 照樣能分析，但沒有東西可以接著修 | 同上 |
| 選配 | `asc-*` | 沒有 App Store Connect 出貨流程 | [rorkai/app-store-connect-cli-skills](https://github.com/rorkai/app-store-connect-cli-skills) |

<details>
<summary>建議與選配的安裝指令</summary>

```bash
npx skills add superagents-lab/xcode27-skills --skill swiftui-specialist --skill swiftui-whats-new-27 -a claude-code -g -y
npx skills add https://github.com/Dimillian/Skills --skill swiftui-ui-patterns --skill swiftui-view-refactor --skill swiftui-performance-audit --skill bug-hunt-swarm --skill review-swarm --skill orchestrate-batch-refactor -a claude-code -g -y
```

Claude Code 裡輸入：

```
/plugin install mattpocock-skills@claude-plugins-official
```

`npx skills` 一定要帶 `-a claude-code`：互動模式預設勾選的那組不含 Claude Code，裝了也讀不到。
專案用到的 framework skill 可從 [dpearson2699/swift-ios-skills](https://github.com/dpearson2699/swift-ios-skills) 挑，裝在專案層（不加 `-g`）。

</details>

**執行時也會提醒**：`/ios-dev` 進場會檢查這次要用的 skill 裝了沒，缺的會寫在確認畫面上，不會默默略過。

> **外部契約的基準**：本 repo 寫到的 `ai-review` 指令、旗標與狀態名，以 [peter6601/ai-review](https://github.com/peter6601/ai-review) 的 **main** 為準。要核對請對 main，不要釘某個歷史 commit——`submit-preflight` 這類已退役的指令只存在於舊 commit。

## 沒有公開的 skill

流程裡還會提到兩個作者自用、跟個人筆記庫綁得很深而沒有公開的 skill。它們都是可選步驟，沒裝就跳過：

| 名字 | 用途 | 沒裝時 |
|---|---|---|
| `second-brain` | 維護期知識庫 | 跳過（流程寫的是「有才讀、有才回寫」） |
| `work-log-writer` | 工作紀錄 | 跳過，或用你自己的紀錄方式 |

<details>
<summary>名詞對照</summary>

- **workspace**：**選配**。放跨 repo 規劃文件的地方（建議是 git 管理的 Obsidian vault）。不給的話 `phase-workflow` 就寫進 iOS repo 的 `docs/features/<功能>/`，流程完全一樣。
- **第二大腦**：一個功能的維護期知識庫。沒有就跳過，流程寫的是「有才讀」。
- **§0 架構形狀**：開發前的架構產出，四段——pattern、模組邊界、state 與 presentation、async 契約。之後每張 ticket 都拿它當尺。
- **輕／重**：審查強度。跟「要不要做架構設計」是兩件事。
- **Phase A／B**：A＝初版建構期（規劃＋連續跑 ticket）；B＝之後的修正期，每個 PR 恢復完整把關。
- **紅線檔**：開發期間要保護的既有主檔。可以改，但要最小化、只加不改、向下相容。
- **看板**：`phase-workflow` 產的 `board.base` 需要 Obsidian 才看得到；不用 Obsidian 其餘照常。
- **產出會不會被 commit**：不會。`phase-workflow` 預設只產檔並列出 diff，commit／merge／PR 要你明講。

</details>

## 測試

```bash
python3 -m unittest discover -s skills/ios-dev/scripts -p "test_*.py"   # SwiftUI 量測腳本 ＋ 引用完整性檢查
python3 skills/ios-dev/evals/test_run_evals.py                             # 路由評測的 parser 與 fixture（不呼叫模型）
python3 skills/careful-ios/bin/test_check_careful_ios.py                   # careful-ios 的 hook
python3 test_install_sh.py                                                 # 安裝腳本（含四種 locale）
bash -n install.sh && ./install.sh --check                                 # 語法 + 相依表
```

## 致謝

幾個 skill 是從別人的作品改寫成 iOS／SwiftUI 版本的，完整聲明見 [`NOTICE`](NOTICE)：

- `ios-review`、`ios-investigate`、`careful-ios`、`office-hours` 的骨架來自 [garrytan/gstack](https://github.com/garrytan/gstack)（MIT）
- 路由評測（`skills/ios-dev/evals/`）與引用完整性檢查的做法借鑑 [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)（MIT）的三層 `evals/`；程式碼是獨立實作
- `ios-critique`、`ios-harden`、`ios-distill`、`ios-polish` 改寫自 [pbakaus/impeccable](https://github.com/pbakaus/impeccable)（Apache-2.0）的 `critique`／`harden`／`distill`／`polish`

## License

MIT。改寫自他人作品的 8 個 skill 另受原作授權約束（見 [`NOTICE`](NOTICE) 與 `LICENSES/`）。
「相依一覽」裡的第三方 skill，本 repo 只引用名字，不含它們的內容。

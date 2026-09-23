# Skill Router — `/ios-dev` Step 0 的流程選擇

<!-- touchpoint: none -->
這份文件決定每次任務要載入哪些 skill、派哪些 agent，以及何時詢問使用者。工具介紹與安裝方式見根目錄 `README.md`。

查閱順序：**§0 執行步驟 → §1 任務類型 → §2 架構路線 → §3 審查方式 → §6 確認畫面**。缺少工具時查 §9；交棒後的完整收尾見 `handoff-checklist.md`，計畫格式見 `plan-template.md`。

## 0. Step 0 怎麼跑

依序執行以下八步；`SKILL.md` 以此為準。

<!-- touchpoint: none -->
**選項式提問**：本檔說「問」或「確認」時，用當下平台的選項式提問工具——Claude 是 `AskUserQuestion`；Codex 在 Plan 模式是 `request_user_input`（一般模式沒有這個工具）。都沒有時，把題目與編號選項直接寫在回覆裡，請使用者回數字。

1. **查既有功能**：需求有指名檔案或功能時，搜尋目標檔的相關關鍵字。既有功能改呈現方式（如 alert 改 sheet）算情境 2，確認畫面註明「既有 X → 改為 Y」。
   <!-- touchpoint: ios-dev-043 kind=engineering -->
2. **判斷情境**：依需求、檔案或 ticket 路徑選 §1 的情境。無法判斷才用選項式提問，七種情境分兩題（4＋3）。
3. **判斷內容**：小功能、優化、重構與接 ticket 依 §4 判斷功能／畫面／兩者；無法判斷才問。
4. **檢查前置設定**：情境 1 無 PM spec、或情境 2，檢查 `CLAUDE.md`／`CLAUDE.local.md`／`AGENTS.md` 是否有 `## Agent skills`。沒有就把「先跑一次 `setup-matt-pocock-skills`」列入提醒。
5. **選工具與審查方式**：依 §1 選 skill、agent 與待問事項，依 §3 判定輕重及 Review 路線，依 §9 檢查所需工具。
6. **檢查架構影響**：情境 2–7 先查既有契約，再依下表決定是否補規劃。任何改變行為的任務都要檢查，結論寫入確認畫面。
   <!-- touchpoint: ios-dev-044 kind=gate -->
7. **確認後開始**：用 §6 的選項式提問格式，等使用者選「照這組跑」或「照這組跑，加 Codex 審核」；後者改走 A。需要詢問 body >80 的處理方式時，在這題之後、主流程之前另問一題。
   <!-- touchpoint: ios-dev-045 kind=command -->
8. **執行或交棒**：依下表啟動流程。交棒 `phase-workflow` 時印出 §8 的指令，建議開新 session。

**架構影響檢查**（第 6 步）：

| 既有契約 | 處理方式 |
|---|---|
| ticket／根文件／計畫已有架構約束，且涵蓋本次範圍所需的 owner、注入點、async 生命週期與不變條件 | 留在實作路徑，註明「契約已備（來源：<根文件／ticket>），直接實作」。已規劃的新增模組不需再次規劃 |
| 沒有契約、有缺漏，或超出既有範圍 | 依 `architecture-impact-check.md` 五問，判定「直接擴充／局部整理／模組邊界」。命中中型條件就走 §2；回流只補缺漏，不重跑整套規劃 |

**執行或交棒**（第 8 步）：

| 情境 | 去向 |
|---|---|
| 1 無 PM spec、2 | 留在 `/ios-dev` Step 1–8 |
| 1 有 PM spec | 直接交 `phase-workflow` 入口 B，跳過 `/ios-dev` Step 1–5 |
| 3–7 | 交給該情境的 skill；交棒訊息必須原樣附上 `handoff-checklist.md` 的「開發前」＋「共通收尾」＋該情境段。交棒後 `/ios-dev` 不再介入執行 |

若要求違反流程規則（如改契約遷就 code、直接 commit／push、跳過必要步驟），先說明限制與可行做法，**同一則回覆仍須附確認畫面**。

## 1. 七情境組合表

先選情境，再讀該情境的細節。審查強度與 Review 路線統一由 §3 判斷。

| 情境 | 內容軸 | 主要流程 |
|---|---|---|
| 1 新專案／新模組／大功能 | 不適用 | §2 分流，規劃後接 ticket |
| 2 小功能 | 依 §4 | 確認需求 → 短計畫 → 實作 |
| 3 純呈現畫面 | 畫面 | 狀態檢查 → 實作 → 打磨 |
| 4 修正（bug／issue／維護期） | 不適用 | 找根因 → 修正 → 驗證 |
| 5 優化 | 效能／行為 | 量測 → 修改 → 再量測 |
| 6 重構 | 依 §4 | 基線 → 定邊界 → 分段修改 → 對比 |
| 7 接 ticket | 從 ticket 檔案清單推斷 | 讀契約 → 實作 → 回寫狀態 |

### 情境 1：新專案／新模組／大功能

- **流程與載入**：有 PM spec 直接交 `phase-workflow` 入口 B，不載入前置規劃工具。沒有 PM spec 則載入 `office-hours`、grill（§9）、`swift-architecture-skill`（Step 4）、`swiftui-specialist`、`swift-concurrency`，走 §2。
- **審查**：走重，六個 agent 全上。交 `phase-workflow` 時，確認畫面改寫「依每張 ticket（情境 7）五條件決定」。
  <!-- touchpoint: none -->
- **詢問**：不另問；ticket 數在 Step 5 估。
- **收尾**：留在 `/ios-dev` Step 1–8；交 `phase-workflow` 後，每張 ticket 走情境 7。

### 情境 2：小功能

- **流程**：Step 1 → Step 2（有第二大腦才讀）→ Step 3（一輪訪談）→ Step 5 test cases → Step 6 短 plan → Step 7 `/consensus-plan` → `/subagent-driven-development`。留在 `/ios-dev` Step 1–8；架構檢查依 §0。
- **載入**：功能用專案 framework skill＋`swift-concurrency`；畫面用 `swiftui-specialist`＋`swiftui-ui-patterns`；兩者則全部載入。
- **審查**：預設輕，風險升級依 §3。畫面先派 `architecture-auditor`；功能符合 §4 concurrency 訊號時先派 `concurrency-auditor`。
  <!-- touchpoint: none -->
- **詢問與提醒**：套用下方「畫面共通檢查」。

### 情境 3：純呈現畫面

僅限版面、樣式、動畫。涉及驗證、持久化、連線、ViewModel 狀態、導航或 async，改走小功能或中型路線。

- **流程**：答架構五問的第 3 問（是否新增第二份真相或互斥旗標）→ Phase 2 → `ios-polish`（宣稱完成前用 Xcode MCP `RenderPreview` 附改前改後 Preview 截圖當證據，§11）。
- **載入**：`swiftui-specialist`＋`swiftui-ui-patterns`。
- **審查**：預設輕；先派 `ux-critique`＋`architecture-auditor`，其餘依 §3。
  <!-- touchpoint: none -->
- **詢問與提醒**：套用下方「畫面共通檢查」。收尾見 `handoff-checklist.md` §3。

<!-- touchpoint: ios-dev-046 kind=engineering -->
**畫面共通檢查（情境 2、3）**：body >80 行，問「先用 `swiftui-view-refactor` 拆分，還是直接加？」；已有 ≥1 個 `isPresented` 時不問，確認畫面註明「新 modal 併進 `Identifiable` enum＋`.sheet(item:)`，不新增 Bool」。

### 情境 4：修正

- **流程**：有第二大腦時，先由 `/ios-dev` 讀功能 MOC（遵守 Step 2 的 context budget）→ 使用者裝置上發生、本機重現不了的 crash，先用 Xcode MCP 撈線上 crash log（§11）→ `/ios-investigate` 五階段 → 修正。根因未知或高風險時，回 Step 1「複雜 Bugfix」路徑：repair plan → `/consensus-plan` → 修正 → `/consensus-review`。
- **載入**：`ios-investigate`；crash／regression／flaky 在假設階段啟動 `bug-hunt-swarm`；符合 §4 concurrency 訊號時加 `swift-concurrency`。
- **審查**：五條件定輕重，確認畫面先寫「待定（預判 X，理由）」。重時派五個閘門 agent，省略 `ux-critique`；Review 路線依 §3。
  <!-- touchpoint: none -->
- **詢問**：不另問。收尾見 `handoff-checklist.md` §4。

### 情境 5：優化

- **流程**：先量測 → 修改 → 用同一方式再量測。改前、改後都派 `perf-auditor`；有疑慮先用 `trace-analyzer` 錄 trace。
- **載入**：`swiftui-performance-audit`、`swift-concurrency`、`swiftui-expert-skill/references/performance-patterns.md`。
- **審查**：模組級走重，單畫面可走輕；仍須通過 §3 風險檢查。範圍未確認前寫「待定（預判 X，理由）」。
  <!-- touchpoint: ios-dev-047 kind=mixed -->
- **詢問**：驗收數字，以及範圍是單畫面還是模組。收尾見 `handoff-checklist.md` §5。

### 情境 6：重構

- **流程**：依 `architecture-impact-check.md` 的「既有功能的架構重構路徑」：`architecture-auditor` 出基線 → 責任地圖／狀態與工作清單／行為不變條件＋補測試／目標邊界與遷移順序 → `swift-architecture-skill` Deep Refactor Mode 定目標並記 ADR → 沿完整行為分段修改 → 測試前後通過 → `architecture-auditor` 對比。
- **規劃**：涉及多個 state owner、presentation 流程或 async 生命週期，交 `phase-workflow` 重構規劃模式。
- **載入**：`swift-architecture-skill`；畫面加 `swiftui-view-refactor`，功能加 `swift-concurrency`，>3 檔使用 `orchestrate-batch-refactor` 前先問是否平行。
- **審查**：走重；純畫面重構省略 `concurrency-auditor`。
  <!-- touchpoint: ios-dev-048 kind=engineering -->
- **詢問**：>3 檔是否平行，以及既有測試是否足以作為行為快照。收尾見 `handoff-checklist.md` §6。

### 情境 7：接 ticket

  <!-- touchpoint: ios-dev-049 kind=command -->
- **流程**：讀 ticket、根文件對應段、`CONTEXT.md`／`docs/adr/`、`coordination/implementation-log.md` → `/writing-plans`（只規劃本張，不跑 consensus-plan）→ `/subagent-driven-development` → 審查 → 回寫 ticket 狀態與 implementation-log → 問「接下一張？」。
- **載入**：依內容軸，與情境 2 相同。
- **審查**：五條件定輕重，Review 路線依 §3，預設 B。契約已備且涵蓋本次範圍時，不重跑架構規劃，仍執行本張 ticket 的 `/writing-plans`（§0）。
  <!-- touchpoint: none -->
- **詢問**：不另問；全部 ticket 完成時提醒 Phase 5 worklog 與 Phase 6 second-brain。完整收尾見 `handoff-checklist.md` §7。

## 2. 兩軸分流：工作量 × 責任邊界

**兩件事分開判斷，不要用同一個數字決定。**

- **工作量軸**（ticket 數、檔案數、diff 行數）→ 決定要不要切 ticket、輸出幾份文件、怎麼排 Stage。
- **責任邊界軸**（`architecture-impact-check.md` 的五問）→ 決定**開發前要產出什麼架構決策**。

| 工作種類 | 開發前一定要有的架構產出 | 路線 |
|---|---|---|
| **大功能／跨模組** | 整體分層、依賴方向、共享狀態與生命週期＝§0 架構形狀四段 | 有 PM spec → `phase-workflow` 入口 B；否則 ios-dev Step 1–5 → 入口 A |
| **中功能／新增模組** | 模組邊界與對外契約、state／presentation／async 的 owner、狀態轉移與取消策略 | `phase-workflow` 中型（觸發條件見 `architecture-impact-check.md`，**與 ticket 數無關**）|
| **小功能** | 五問的答案（一句話）＋ 有 async 時的 ownership 契約 | 沿既有架構接入：ios-dev Step 1–7 |
| **修正問題** | 根因 ＋ **被破壞的不變條件**；再決定局部修復或局部架構調整 | `/ios-investigate` → 依結論回流（局部調整＝小功能；牽動邊界＝中型）|
| **純呈現的畫面修改** | 不需架構產出，但仍要答第 3 問（會不會多出第二份真相或互斥旗標）| 直接 Phase 2 → `ios-polish` |
| **涉及狀態／導航／async 的畫面修改** | presentation 轉移表（＋ async 契約）| 當小功能或中功能處理，不走純畫面路徑 |

ticket 數**只決定 `phase-workflow` 的輸出規模**（中型 4 份檔／大型 7 份檔），
**不決定要不要進 phase-workflow**——那由責任邊界決定。只有兩張 ticket 的新模組照樣要中型規劃；
沿既有清楚契約增加操作的十張 ticket 不必進中型。

<!-- touchpoint: ios-dev-050 kind=command -->
<!-- touchpoint: ios-dev-051 kind=mixed -->
```
情境 1（新專案／新模組／大功能）
├─ 有 PM spec？ → 是：立即交 phase-workflow 入口 B（ios-dev Step 1–5 全跳；它的 grill＝唯一一次）
│                        指令：/phase-workflow 入口 B：<PM spec 來源：issue URL 或檔案路徑>（新 session）
│                        → rd-spec.md（含 §0 架構形狀）人審後貼 issue → 切 ticket → 之後每張走情境 7
└─ 否：ios-dev Step 1–5（grill、Step 4 用 swift-architecture-skill 產 §0、test cases）
       → 交 phase-workflow 入口 A（帶 Decision Log＋§0；根文件 overview.md 審一次）
       → 切 ticket；ios-dev Step 6–7 跳過；之後每張走情境 7

情境 2–7 命中中型觸發條件時
└─ 交 phase-workflow 中型（帶五問的答案、轉移表、async 契約當輸入）→ 切 ticket → 每張走情境 7
```

## 3. 輕／重與五條件

分開判斷兩件事：**輕／重決定審查強度，A／B／C 決定 Review 路線**。架構規模由 §2 決定。

### 五條件的適用範圍

| 類別 | 條件 | 適用範圍 |
|---|---|---|
| 風險 1 | 不碰 concurrency、state machine、持久化、網路協定或 migration | 所有情境 |
| 風險 2 | 不改公開契約 | 所有情境 |
| 風險 3 | 本次改動能寫出直接可重現的測試，可在本次補上 | 所有情境；情境 3 改用 Preview 或截圖前後對照 |
| 規模 1 | 範圍單一且清楚 | 定輕重時只套情境 4、7；判斷 C 路線時全部適用 |
| 規模 2 | production diff ≤50 行 | 同上 |

情境 3 的測試例外只限純呈現；碰到狀態、導航或 async 就不適用。

### 判斷輕重

- **任一風險條件不符合 → 重**，所有情境皆同。例如小功能改到持久化，也要走重。
- **風險三條全符合**：小功能、純畫面走輕；單畫面優化可走輕；修正與 ticket 還要符合規模兩條，才走輕。
- **固定走重**：情境 1、模組級優化、重構；交 `phase-workflow` 後，每張 ticket 另依情境 7 判斷。
- **資訊不足 → 待定**：確認畫面寫「待定（預判 X，理由）」，釐清範圍與風險後再定。**自我檢查**：「會問你」裡只要有一題的答案會影響風險三條（例如新頁面要放什麼、會不會存資料、資料送去哪），輕重就必須是待定。
- **完成後重判**：所有情境重查風險三條；情境 4、7 另查規模兩條。不再符合輕量條件時升重，補派該情境的 agent。

情境決定要做的工作；五條件只調整審查強度，不改變任務分類。

### 輕與重各做什麼

<!-- touchpoint: ios-dev-052 kind=code-review -->
<!-- touchpoint: ios-dev-053 kind=code-review -->
| 強度 | 流程 |
|---|---|
| 輕 | 該情境指定的 auditor（若有）→ 合併 findings → `ios-review`（兩輪 fix-first）→ 所選 Review 路線 → 人工 Code Review |
| 重 | 該情境的閘門 agent＋`review-swarm` → 統一修復 → `/ios-polish` → verification → 所選 Review 路線 → 人工 Code Review |

六個閘門 agent 為 `swiftui-reviewer`、`ux-critique`、`resilience-auditor`、`perf-auditor`、`concurrency-auditor`、`architecture-auditor`，全部唯讀；依 §1 的情境調整名單。

其中前三個也是 Review 路線 A、B 的 specialist，輕重都要派；只有 C 不派。輕量流程省略完整閘門組、`review-swarm` 與 Phase 3 統一修復循環。完整收尾順序以 `handoff-checklist.md` 的「共通收尾」為準。

### Review 路線（三選一，預設 B；要不要加 Codex 由使用者在確認畫面決定）

Step 0 先列出路線，再用 §6 選項確認是否加 Codex。

| 路線 | 選用條件 | 流程 |
|---|---|---|
| **A 共識** | 使用者選「加 Codex 審核」，或複雜 Bugfix（根因未知／高風險，強制） | 三個 specialist 各回 JSON → `/consensus-review --profile ios --preflight` → Codex 首輪 → 合併 → 單一 Claude 統一修復 → re-review |
| **B 純 agent** | 預設；未選 A，且不符合 C | 三個 specialist＋該情境 auditor 唯讀審查 → 主 session 統一修復 → `/ios-polish` → `/verification-before-completion` |
| **C 輕量** | 範圍單一、production diff ≤50 行，且風險三條全符合；純設定與文件也一樣 | `ios-review`（兩輪 fix-first）→ `/verification-before-completion` |

- **A 的必要輸入**：`--profile ios` 必須帶 `--preflight`，只接受 `swiftui`／`ux`／`resilience` 三類 JSON。其他 auditor 的 findings 依共通收尾先處理。
- **複雜 Bugfix 降級**：只有 Codex 不可用（`ai-review` 回 529、額度用完、context 過大導致輸出退化）才可從 A 降 B，並在 PR 描述註明。
- **C 不可放寬**：趕時間或使用者要求都不能略過門檻，不提供例外選項。完成後重判；超過 50 行或任一風險條件不符，從 C 升 B。
- **修復分工**：只有 A 有 `init` 前後的修改權限分界；B、C 全程由主 session 統一修復一次，再驗證。
  <!-- touchpoint: ios-dev-054 kind=code-review -->
- **人工審查**：三條路線都要人工 Code Review，A 另有 `approve-code` 硬閘門。B、C 的 PR 描述須標明路線與「未經 Codex 交叉驗證」。

## 4. 內容軸推斷規則

- 描述或 ticket 的檔案清單含 `Views/`、`Components/`，或出現「畫面、sheet、alert、版面、按鈕、動畫、Liquid Glass」→ 畫面
- 含 `ViewModels/`、`Services/`、`Networking/`、`Models/`，或出現「API、串接、儲存、同步、連線、背景工作」→ 功能
- 描述很短、只指到一個 view 時，grep 該 view 裡跟功能名相關的 func：碰 `@AppStorage`／`UserDefaults`／`Service`／`connection`／網路呼叫 → 加上「功能」
  <!-- touchpoint: ios-dev-055 kind=engineering -->
- 兩邊都有 → 兩者；都沒有 → 問一題（選項：功能／畫面／兩者）
- **concurrency 訊號**（決定要不要載 `swift-concurrency`／派 `concurrency-auditor`）：描述提到 task／actor／data race／Sendable，**或**症狀是 crash 加間歇（「有時」「偶爾」「flaky」），**或**範圍在連線／stream／Combine 層

## 5. 門檻（數字寫死，改要改這裡）

> 這些數字是**工作量與風險訊號**，用來決定審查強度與要不要先拆；
> **不能代替責任邊界判斷**（那是 §2 與 `architecture-impact-check.md` 的事）。

| 門檻 | 值 | 用在 |
|---|---|---|
| 目標 view body 行數 | >80 → 問先拆或直接加 | 情境 2、3 |
| 平行重構檔數 | >3 → 問是否 `orchestrate-batch-refactor` | 情境 6 |
| 優化鐵律 | 改前沒有 `perf-auditor`、trace 或線上效能數字（`GetTopFieldPerformanceIssues`，§11）不動 code；改後同一把尺再量寫進 PR | 情境 5 |
| 重構護欄 | 目標範圍無測試覆蓋 → 先用 SDD 補行為快照測試再動 | 情境 6 |
| architecture-auditor 四閘門 | body >80、`@State` >5、`isPresented:` >1、`onChange` 監看 `should*/did*` | 所有派它的情境；腳本是 `ios-dev` skill 目錄下的 `scripts/swiftui-metrics.py` |
| ticket 數 | **只決定 `phase-workflow` 的輸出規模**（1–8 張中型 4 份檔／>8 張大型 7 份檔），**不決定要不要進去**——入場看責任邊界（§2） | phase-workflow Step 4 |
| production diff 行數 | >50 行 → 不算輕（規模兩條之一，§3） | **只有情境 4 與情境 7**；小功能與純畫面不套 |

<!-- touchpoint: ios-dev-056 kind=gate -->
## 6. 確認畫面格式（選項式提問，一題）

<!-- touchpoint: ios-dev-057 kind=command -->
<!-- touchpoint: ios-dev-058 kind=mixed -->
```
題目：情境＝<情境名>（內容＝<功能／畫面／兩者／不適用>）<既有功能時加：既有 X → 改為 Y>。這次會：
  載入：<skill a>、<skill b>、<skill c>
  Phase 3 派：<agent d>、<agent e>（<輕／重／待定（預判 X，理由）>）
  Review 路線：<B 純 agent（預設）／C 輕量（很小且風險三條全綠）／A 共識（複雜 Bugfix 強制）>（<一句理由>）
  架構結論：<契約已備（來源：根文件／ticket）直接實作／直接擴充／局部整理（範圍）／模組邊界（命中哪條觸發條件）>；<要不要產轉移表／async 契約>
  已讀：<只有情境 7 必填，出確認畫面前讀完：ticket、根文件對應段（寫出 §）、`CONTEXT.md`、`docs/adr/`、`coordination/implementation-log.md`；沒有的寫「無」，不要省略>
  交棒：<第一個 skill 或指令；情境 1 無 PM spec 與情境 2 寫「留在 /ios-dev Step 1」；交棒 phase-workflow 寫指令＋「建議新 session」>
  會問你：<該情境的詢問事項，或「不問」>
  提醒：<§0 前置檢查或硬規則，沒有就省略此行>
選項：
  1. 照這組跑（Recommended）
  2. 照這組跑，加 Codex 審核（review 改走 A 共識）
  3. 我要調整（用 Other 說明要加減什麼）

複雜 Bugfix 已強制走 A，省略選項 2。
```

## 7. 不進表、永遠生效

- `careful-ios`：破壞性指令護欄，靠 description 自動觸發
- `verification-before-completion`：任何「完成」宣稱前
- Phase 5：結束時問要不要 `work-log-writer`（現行規則不變）
- 專案層 framework skill（例如 `dpearson2699/swift-ios-skills` 裡對到你專案所用 framework 的那幾個）：靠 description 自動載入，不列入 bundle

<!-- touchpoint: ios-dev-059 kind=command -->
## 8. 交棒到 phase-workflow 一律開新 session

phase-workflow 自己要做 codebase grounding、產 4–7 份文件、跑一輪 Codex 根文件審查。印出指令並說明「建議開新 session 執行」：

```
入口 A（無 PM spec）：/ios-dev 完成 Step 1–5，把 design doc、Decision Log、§0 寫進功能資料夾後印
  /phase-workflow <design doc 路徑>
入口 B（有 PM spec）：/ios-dev 不做 Step 1–5，直接印
  /phase-workflow 入口 B：<PM spec 來源：GitHub issue URL 或檔案路徑>
```

<!-- touchpoint: ios-dev-060 kind=command -->
之後每張 ticket 各自 `/ios-dev tickets/<T>.md` 開新 session。這是「同 session 交棒」的唯一例外。

## 9. 本表引用的名字與沒裝時的替代

安裝指令與來源見 repo 根目錄 `README.md`。進場時只檢查 §1 對應情境需要的工具。
skill 下列任一位置存在就算裝了，依你所在的平台查：

```
Claude：~/.claude/skills/<name>/SKILL.md
        ~/.claude/commands/<name>/SKILL.md
        ~/.claude/commands/<name>.md
Codex： ~/.agents/skills/<name>/SKILL.md
        ~/.codex/skills/<name>/SKILL.md
        ~/.codex/plugins/cache/*/*/*/skills/<name>/SKILL.md（plugin 附帶的 skill）
```

agent：Claude 查 `~/.claude/agents/<name>.md`，Codex 查 `~/.codex/agents/<name>.toml`（由 `install.sh` 從同名 `.md` 轉出）。缺的照下表替代，並寫進確認畫面的「提醒」行。
**第三方 skill 沒有替代**：缺了就在提醒行列出名字、指向 README「安裝」的第 1 步；其中
`swiftui-expert-skill` 缺時 6 個 agent 的必讀檔不存在，先裝再跑 Phase 3。

- **本 repo 附的**：skill `ios-dev`、`phase-workflow`、`office-hours`、`ios-investigate`、`ios-review`、`ios-polish`、`ios-distill`、`ios-critique`、`ios-harden`、`careful-ios`、`localize-strings`；agent `swiftui-reviewer`、`ux-critique`、`resilience-auditor`、`trace-analyzer`、`perf-auditor`、`concurrency-auditor`、`architecture-auditor`、`store-preflight-auditor`、`build-analyzer`
- **第三方 skill**（`npx skills add … -g` 安裝：Claude 加 `-a claude-code`，Codex 加 `-a codex`；`npx skills update -g` 更新。Codex 上 `swiftui-ui-patterns`、`swiftui-view-refactor`、`swiftui-performance-audit` 改由官方 Build iOS Apps plugin 提供）：`swift-architecture-skill`、`swift-concurrency`、`swiftui-specialist`、`swiftui-whats-new-27`、`swiftui-ui-patterns`、`swiftui-view-refactor`、`swiftui-performance-audit`、`bug-hunt-swarm`、`review-swarm`、`orchestrate-batch-refactor`、`swiftui-expert-skill`、`app-store-preflight-skills`、`xcode-project-analyzer`、`xcode-compilation-analyzer`、`spm-build-analysis`、`xcode-build-fixer`（前三個是 `build-analyzer` 讀的，第四個只有真的要修 build 才需要）、`ios-accessibility`（dadederk）、`asc-*`
- **vendor**（`~/.claude/vendor`，**不要**放進 skills 目錄，只給 agent 按路徑讀、不會自動觸發；`git clone https://github.com/twostraws/swiftui-agent-skill ~/.claude/vendor/twostraws-swiftui-agent-skill` 安裝、`git pull` 更新）：`swiftui-pro`（twostraws，app 主 target ≥ iOS 17 時由 `swiftui-reviewer` 讀，每條建議先過 agent 裡的版本表；放 skills 會在任何專案自動觸發，而它預設新專案是 iOS 26；沒裝就跳過）
- **共識審查**（`consensus-plan`、`consensus-review` 與 `ai-review` CLI）：[peter6601/ai-review](https://github.com/peter6601/ai-review)
  <!-- touchpoint: ios-dev-061 kind=command -->
- **plugin**：`superpowers:subagent-driven-development`、`superpowers:writing-plans`、`superpowers:test-driven-development`、`superpowers:verification-before-completion`；mattpocock 的 `/grill-with-docs`、`/grill-me`、`setup-matt-pocock-skills` 是 **user-invoked**（只能使用者打字觸發，模型呼叫不到），模型端能呼叫的只有 `mattpocock-skills:grilling`。Step 3 要 grill 時：印出「請輸入 `/grill-with-docs`」等使用者；使用者不在時用 `mattpocock-skills:grilling` 頂替，但它不會長出 `CONTEXT.md`／`docs/adr/`，要自己補。**沒裝 mattpocock plugin**（`grilling` 也在同一個 plugin 裡，一樣沒有）：改用 `superpowers:brainstorming` 做需求訪談，同樣自己補 `CONTEXT.md`／`docs/adr/`
- **同名兩份時一律用無前綴的本機版**（例如 plugin 帶了同名的 `verification-before-completion`）

**本 repo 不含、作者自用未公開的 skill**——表裡仍保留名字，沒裝就走替代：

<!-- touchpoint: ios-dev-062 kind=command -->
| 引用的名字 | 它在流程裡的角色 | 沒裝時的替代 |
|---|---|---|
| `second-brain` | Phase 6 維護期知識庫（功能 MOC） | 跳過；「有第二大腦才讀」「有才回寫」本來就是條件式 |
| `work-log-writer` | Phase 5 工作紀錄 | 跳過，或請使用者用自己的紀錄方式 |

本 repo 附的 skill 若被使用者自己移除，退回這些通用替代：`office-hours`→`superpowers:brainstorming`；
`ios-investigate`→`superpowers:systematic-debugging`；`ios-review`→派 `swiftui-reviewer`＋`concurrency-auditor`
（此時 review 路線 C 不可用，最低走 B）。

<!-- touchpoint: ios-dev-063 kind=engineering -->
MCP 不是 skill，不在本節的安裝檢查範圍（user 範圍，`claude mcp list` 可查；分工見 §11）：`xcode`（`xcrun mcpbridge`，Apple 官方，隨 Xcode 27）、`XcodeBuildMCP`（社群開源，Sentry 維護）。Codex 要另外在 `~/.codex/config.toml` 加 `[mcp_servers.xcode]`（`command = "xcrun"`、`args = ["mcpbridge"]`）。沒裝時：缺 XcodeBuildMCP 改用 Bash 跑 `xcodebuild`／`xcrun simctl`；缺 Xcode MCP 就跳過 §11 那幾項——Preview 證據改用模擬器截圖、線上 crash 請使用者從 Organizer 匯出

## 10. 輔助 skill 的介入時機（輸入 → 產出）

| skill／agent | 什麼時候進場 | 輸入 | 產出 |
|---|---|---|---|
| `swift-architecture-skill` | **開發前**，決定邊界 | 五問的答案、既有 §0（有的話）| 模組邊界、owner、適用 pattern＝§0 架構形狀四段 ＋ feature PR checklist |
| `swift-concurrency` | **新增或改變非同步工作前** | 該工作的用途與觸發點 | ownership 契約六格（持有者／生命週期／清理／重入／舊結果失效／isolation）|
| `swiftui-specialist`＋`swiftui-ui-patterns` | 實作呈現與互動時 | 已定案的架構契約 | View 實作；**不自行改變模組責任** |
| `swiftui-view-refactor` | 拆 View 時 | 責任地圖、目標邊界 | 子 View 接必要的資料與操作，不接整個 ViewModel |
| `architecture-auditor` | **第一段有意義的實作完成時**＋最終收尾 | §0／PR checklist、上一次基線 | 契約有沒有被守住（數字只是線索）|
| `concurrency-auditor` | 同上，有 async 工作時 | ownership 契約六格 | 實作有沒有破壞契約 |
| `swiftui-reviewer` 的第二套標準 `swiftui-pro` | Phase 3，**app 主 target ≥ iOS 17**，建議先過版本表 | 要審的 View 檔 | 依檔案分組、附行號與改前改後的 finding；專案結構類主張不當 finding |
| `ios-accessibility` | `resilience-auditor`、`ios-harden` 處理無障礙時 | 畫面檔、deployment target | 無障礙 finding 與「需實測清單」（VoiceOver 以外也涵蓋 Voice Control、Switch Control、Full Keyboard Access）|

兩條規則：

- **專案已確認的架構契約優先於各 skill 的預設風格。** 衝突時以 §0／`docs/adr/` 為準，並在報告裡明講衝突的是哪一條——不要讓兩個 skill 各套一套架構。
- **不要每個任務都無差別載入全部 skill 或派全部 agent。** 載入清單照 §1 對應情境，agent 照 §3 的輕／重與情境裁法。

## 11. MCP 工具分工（Xcode 27+）

兩個 MCP 同時存在，依能力分工，不依「官方優先」：

| 用途 | 用哪個 | 工具 |
|---|---|---|
| 模擬器 build／run／UI 自動化（點擊、截圖、讀 UI 樹）、跑測試、覆蓋率 | XcodeBuildMCP | `build_run_sim`、`test_sim`、`snapshot_ui` 等 |
| SwiftUI Preview 截圖 | Xcode MCP | `RenderPreview` |
| 線上 crash／效能資料（Apple 後台） | Xcode MCP | `GetTopCrashIssues`、`GetCrashIssueLogs`、`GetTopFieldPerformanceIssues` |
| 單檔編譯錯誤／警告（不整包 build） | Xcode MCP | `XcodeRefreshCodeIssuesInFile` |
| String Catalog 讀寫 | Xcode MCP（要先載入 Xcode 的 `xcode-integration` plugin，見 `localize-strings`） | `StringCatalogRead`／`StringCatalogEdit`／`LocalizationPlanner` |

- **同一台模擬器同時只給一個 MCP 用**：兩邊都會 build 並裝到模擬器，一起跑會互搶，跑出的結果不能信。
- Xcode MCP 要先 `XcodeOpenWorkspace` 開專案才能用；只為了 build／run 不要開它。
- 前提：`xcode-select -p` 指向 Xcode 27；指向 Command Line Tools 時兩個 MCP 都會 build 失敗。

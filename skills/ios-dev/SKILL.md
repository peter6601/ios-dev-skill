---
name: ios-dev
description: iOS 開發工作流的唯一入口 skill。任何 iOS 開發需求都從這裡進：Step 0 先認七種情境（新專案／大功能、小功能、純畫面、修正、優化、重構、接 ticket）與內容軸（功能／畫面），秀出這次會載入的 skill 與派出的 agent 讓使用者確認一次，再交棒或走 Phase 0（產品思考）→ Phase 1（規劃）。任何會改變行為的任務**開發前都要做架構影響檢查**（五問 → 直接擴充／局部整理／模組邊界）；命中模組邊界的工作交 phase-workflow 切 ticket（與 ticket 數無關），之後每張 ticket 用 `/ios-dev tickets/<T>.md` 接回來開發。觸發場景：「我要開發 XXX 功能」、「新增 XXX 需求」、「開始做 XXX」、「修 XXX bug」、「優化 XXX」、「重構 XXX」、「接 T3」、「做下一張 ticket」。
metadata:
  user-invokable: true
  args:
    - name: feature
      description: 功能或需求的簡短描述（選填，也可以在對話中說明）
      required: false
---

> 呼叫方式：`/ios-dev [功能或需求的簡短描述 | ticket 路徑]`。描述是選填的，也可以在對話中再說明。

# iOS Dev — 工作流入口

## 你的任務

作為 iOS 開發工作流的**唯一入口**：先認情境（Step 0），秀出這次會載入的 skill 與派出的 agent 讓使用者確認一次，再依情境交棒或往下走。

規劃類情境（新專案／大功能、小功能）留在本 skill 的 Step 1–8，**產出是計畫，不寫 code**。其他情境（純畫面、修正、優化、重構、接 ticket）在 Step 0 交棒後由該 skill 執行，本 skill **不再介入執行，但仍持有收尾清單**。

## 四份 reference

| 檔案 | 什麼時候讀 |
|---|---|
| `references/skill-router.md` | 每次進場。Step 0 的流程、七情境組合表、兩軸分流、輕／重與門檻，全在那裡 |
| `references/architecture-impact-check.md` | **任何會改變行為的任務，開發前**。五問、中型觸發條件、presentation 轉移表、async ownership 契約、重構路徑 |
| `references/handoff-checklist.md` | 交棒情境 3–7 時。把該情境那一段原樣印進交棒訊息 |
| `references/plan-template.md` | Step 6 寫實作計畫時。含重閘門的 agent 清單與統一修復規則 |

---

## Step 0：情境路由（所有進場都先過這裡）

**流程的單點真相是 `references/skill-router.md` §0——先讀它，照它的七個步驟跑**，這裡不重述，以免兩份漂移。

只有三件事寫在這裡：

- **交棒後誰持有收尾**：情境 1（無 PM spec）與情境 2 留在本 skill 往 Step 1；情境 1 有 PM spec 立即交棒 `phase-workflow` 入口 B；情境 3–7 交棒給下游 skill 執行，但交棒訊息**一定要附上 `references/handoff-checklist.md` 該情境那一段**——下游 skill 不知道還有輕／重閘門、review 路線與回寫。
- **開發前一定要有架構結論**：情境 2–7 在確認畫面就要講出這次是「直接擴充／局部整理／模組邊界」，依據是 `references/architecture-impact-check.md` 的五問。命中中型觸發條件就改走 router §2 的中型路線，**與 ticket 數無關**。
- `careful-ios` 與 `verification-before-completion` 不進 bundle、永遠生效。
- 同名兩份的 skill 一律用無前綴的本機版（router §9）。
- 引用到的 skill／agent 沒裝時，照 router §9 的替代表走，並在確認畫面的「提醒」行講出來——不要默默略過。

---

## Step 1：確認功能描述

如果用戶還沒說清楚要做什麼，先問：
- 要做什麼功能？（一句話描述）
- 在哪個專案？（repo 名稱或路徑）
- 這個功能的規模？（Step 0 已認出情境時不再問；小功能／大功能的分界在 Step 5 估 ticket 數）

### 共識入口路由表

先看「Code 現在存在嗎」，再決定共識入口：

| 起始狀態 | 路由 |
|---|---|
| 功能文件已成形、還沒有 Code | `consensus-plan`（唯讀文件審查）→ **人工改文件** → `re-review` |
| 已有實作或 SDD 已完成的 Code | 預設 `consensus-review --profile ios`（路線 A）；Codex 不可用或改動極小時走 router §3 的 B／C |
| 低風險 Bug | `ios-investigate` → 修正 → 依所選 review 路線收尾（小改動可走 C） |
| Root cause 未知或高風險 Bug | `ios-investigate`，先停下來取證與決策，再走對應共識路由 |

共識入口看「Code 在不在」，不看「流程走到哪」：還沒有 Code 時審的是**文件**
（`consensus-plan` 唯讀，產出 findings，不改文件也不寫 code），既有 Code 走
`references/skill-router.md` §3 選定的 review 路線（預設 `consensus-review`）。文件審查沒有核准這件事——改文件的是人，Codex 的 `PASS` 只是
一次仔細的閱讀，不是放行。

根據情境決定要走哪些 Step（修正情境已在 Step 0 交棒給 `/ios-investigate`，這裡只剩規劃類）：
- **小功能（情境 2）**：Step 2（有第二大腦才讀）→ Step 3 的 grill 縮成 1 輪 → **Step 4 精簡版（五問；有 async 補 ownership 契約、有流程補轉移表）** → Step 5 → Step 6（短 plan）→ Step 7；閘門走輕
- **大功能（情境 1，無 PM spec）**：走完整 Step 2–5（Step 3 由使用者輸入 `/grill-with-docs`）；Step 4 的責任邊界結論是**模組邊界**（或本來就是跨模組大功能）→ 交 `phase-workflow` 入口 A（帶 Decision Log 與 §0，Step 6–7 跳過）；沿既有契約增加操作 → Step 6–7。ticket 數只決定 phase-workflow 產幾份檔
- **大功能（情境 1，有 PM spec）**：不走這裡，Step 0 已交棒 `phase-workflow` 入口 B；§0 由它的 Step 3B 產在 rd-spec.md
- **複雜 Bugfix**（`/ios-investigate` 認定 root cause 未知或高風險時會回到這裡）：repair plan 文件 → `/consensus-plan`
  （唯讀文件審查，findings 交回人工改文件，需要再一輪就 `re-review`）→ 依文件修正
  → `/consensus-review`（複雜 Bugfix 一律走路線 A）→ 人工 Code Review；人工核准前不得 commit、push、merge 或建立 PR

閘門走輕的五條件見 `references/skill-router.md` §3，不在這裡複述——改門檻只改那一處。

---

## Step 2：讀取相關第二大腦（有 context budget）

先讀專案產品 MOC 的索引（例如 `<產品名>-產品MOC.md`），不遞迴展開全部 wikilink。
只選最多三個與本任務直接相關的來源，優先順序：
1. 架構紅線與 ownership。
2. 近期踩坑與既有 invariant。
3. 本功能直接涉及的 code path。

**交付物是 `--source` 候選清單**，不是 manifest 檔：每個來源寫成
`"/絕對路徑.md#精確標題"`（`consensus-plan` 只吃 Markdown 章節錨點，最多 5 個、
16,000 token 預算，它在 `init` 前會再跟使用者確認一次）。已檢查但未選入的來源與
理由記進 Step 3 的 Decision Log——`consensus-plan` 沒有這個欄位，寫給它會掉。

第二大腦與 code/test 衝突時，以可執行證據為準。

---

## Step 3：需求訪談與 Decision Log（以 `/grill-with-docs` 執行）

請使用者輸入 `/grill-with-docs`（repo 內；尚無 repo 用 `/grill-me`）——這兩個是 mattpocock plugin 的 user-invoked skill，模型呼叫不到；使用者不在時用 `mattpocock-skills:grilling` 頂替，但要自己補 `CONTEXT.md`／`docs/adr/`。它做審訊式訪談：
它把設計畫成決策樹，分輪問出目前能問的所有決策、每題附建議答案；
事實自己派 sub-agent 查，只把**決策**交給使用者。涵蓋面要包含：問題與使用情境、
現有與預期行為、scope/out-of-scope、可接受取捨、架構限制、邊界與錯誤狀態、
適用的 UX/i18n/accessibility、驗收條件、測試方式與裝置限制。

每個回答記錄為：
問題 → 使用者回答 → 最終決策 → 對 Plan 的影響

grill 同時長出 repo 的 `CONTEXT.md`（純術語 glossary）與 `docs/adr/`
（只記難逆轉＋沒脈絡看不懂＋真有取捨的決策）——這兩份是術語與「為什麼」的真相來源，
Claude/Codex 共識閘門兩邊都讀；Phase 6 第二大腦 MOC 只連結不複製。

規則：**同一功能只 grill 一次**；時間預算 3 輪或 30 分鐘，未收斂的標記為未知事項。
grill 結束後提醒使用者：「需要再跑一次 `/brainstorming` 發散當保險嗎？」（備選，預設不跑）。
前置：repo 首次使用前跑一次 `setup-matt-pocock-skills`（需 `mattpocock-skills` plugin）。

只有必要問題都有答案、未知事項被標記，且使用者確認需求摘要後，
才能寫實作 Plan。

整理出一份簡短的 Design Doc（落檔位置見 Step 6）：
```
## 功能名稱
## 解決的問題
## 目標用戶
## MVP 範圍（這次要做的）
## Out of Scope（這次不做的）
## 成功標準（怎麼知道做好了）
```

如果答案不清楚，**必須停下來詢問用戶**，不要假設。

---

## Step 4：架構規劃（篇幅隨規模，但**不能跳過**）

| 規模 | 這一步要產出什麼 |
|---|---|
| 大功能／跨模組 | 完整「§0 架構形狀」四段 ＋ feature PR checklist |
| 中功能／新增模組 | 模組邊界與對外契約、三種 owner、狀態轉移表、async 契約——然後交 `phase-workflow` 中型 |
| 小功能 | `architecture-impact-check.md` 的五問答案（一句話寫進 plan）；有 async 補契約、有流程補轉移表 |
| 純呈現畫面 | 只答第 3 問（會不會多出第二份真相或互斥旗標）|

呼叫 `swift-architecture-skill`：新功能用 Quick Recommendation Mode，既有模組改造用 Deep Refactor Mode。它會先跑決策矩陣（state 複雜度、單向流需求、非同步編排、既有慣例、學習成本）再選主從組合；預設落點是 **Clean 分層 ＋ MVVM 或 MVI 當 presentation**，SOLID 體現在 protocol DI 與 state ownership。它的護欄照守：小功能不換架構、不引入 TCA 除非使用者接受、取最小改動。

**產出寫成「§0 架構形狀」四段**，放進 Design Doc；交 phase-workflow 時原樣填進 overview.md 的 §0：

1. **Pattern 與理由**：主從組合＋決策矩陣裡決定它的 2–3 個因素
2. **模組邊界**：每個模組誰 own 什麼 state、對外 protocol、注入點（composition root）。**資料夾結構與各層職責寫在這一段**，由 skill 依選定的 pattern 產出——本 skill 不預設任何資料夾模板，因為矩陣可能沒有選 MVVM
3. **State 與 presentation 建模**：誰是互斥呈現的**單一管理者**；sheet／alert／navigation／toast 的優先序；**關閉開始 vs 關閉完成**各掛什麼副作用；ViewModel 只暴露狀態（`phase`、`route`），不用 `should*`／`did*` 旗標指揮 View。涉及流程時附一張轉移表（`architecture-impact-check.md` 的四欄格式）。純局部開關保留 Bool，**只有互斥才**整合成 `Identifiable` enum ＋ `.sheet(item:)`
4. **非同步工作的 ownership 契約**：每一項工作填六格（啟動者與持有者／生命週期／結束與清理／重入策略／舊結果如何失效／isolation 與逾時）。優先 structured concurrency（`.task(id:)`、`async let`、task group）；需要 handle 才存 `Task`，存了就寫清楚誰 cancel、何時 cancel。**不為了符合規則把工作硬搬到 Service，也不要求全部塞進單一 `run()`**——Task 的數量與位置是線索，不是判準。Combine 只在邊界

外加 skill 產出的 **feature 專屬 PR checklist**（5–8 條）——它就是 Phase 3 `architecture-auditor` 對這個功能每張 ticket 的稽核尺。

---

## Step 5：TDD Test Cases 規劃（`superpowers:test-driven-development` 精神）

根據 Design Doc 和架構，列出 Test Cases。**先列 test cases，讓用戶審核後才進入實作。**
列完順便估 ticket 數（一個 ticket ≈ 一組可獨立驗收的 test cases）。**ticket 數不決定要不要進 phase-workflow**（那是 Step 4 的責任邊界結論），它只決定進去之後產幾份檔：1–8 張中型 4 份、>8 張大型 7 份。

格式：

### ViewModel Tests
```swift
// MARK: - Happy Path
@Test func fetchData_success_updatesItems() async { }
@Test func submitForm_validInput_transitionsToSuccess() async { }

// MARK: - Edge Cases
@Test func fetchData_emptyResponse_showsEmptyState() async { }
@Test func submitForm_networkError_showsError() async { }

// MARK: - Error States
@Test func fetchData_unauthorized_redirectsToLogin() async { }
@Test func fetchData_timeout_showsRetryOption() async { }
```

### Service Tests（如果有）
```swift
@Test func fetchData_apiReturns200_parsesCorrectly() async { }
@Test func fetchData_apiReturns404_throwsNotFoundError() async { }
```

**列出後暫停，詢問用戶：**
「以上是初步規劃的 test cases，有需要調整或新增嗎？確認後我們進入實作計畫。」

---

## Step 6：產出實作計畫（`/writing-plans` 精神）

**先分叉**（router §2）：

- **責任邊界命中中型或大型觸發條件**（router §2；新模組／多畫面流程／多 async 協調／要先拆 View 才加得進去）→ 不產整體 plan。Design Doc、Decision Log、§0 寫進 workspace（你放跨 repo 規劃文件的地方：筆記庫或獨立的文件 repo；沒有就用 iOS repo 的 `docs/features/`）的功能資料夾 `Projects/<專案>/<功能>/`，印出 `/phase-workflow <design doc 路徑>` 並建議開新 session 執行；Step 6–7 跳過。之後每張 ticket 用 `/ios-dev tickets/<T>.md` 接回來（情境 7）。
- **沿既有清楚契約增加操作**（不論幾張 ticket）→ 文件落在**目標 iOS repo 內**，沿用既有命名：
  - Design Doc：`docs/plans/YYYY-MM-DD-<feature>-design.md`
  - 實作計畫：`docs/plans/YYYY-MM-DD-<feature>.md`
  - Step 7 呼叫 `consensus-plan` 時 `--repo` 就是這個 iOS repo（`--doc` 必須在 `--repo` 內）；走 phase-workflow 的那條路 `--repo` 才是 workspace。

Test cases 確認後，用 `/writing-plans` 產出完整的實作計畫，格式與 Phase 3 的 agent 清單見
`references/plan-template.md`。

Phase 3 品質閘門的輕／重照 `references/skill-router.md` §3 判，流程與收尾照
`references/handoff-checklist.md` 的「共通收尾」跑——這裡不重畫一次。
Phase 3 的產物就是 Code，所以收尾一律走 §3 的 review 路線（預設 `consensus-review`）；
沒有另一條依 Plan 收尾的路。

---

## Step 7：文件共識閘門（還沒有 Code 時；只在**沒有**交 phase-workflow 的路徑）

走 phase-workflow 的功能，根文件（overview.md／rd-spec.md）已由它的 Step 4.5／3.5B 審過，這步跳過，不重複審。

呼叫 `/consensus-plan`，一次一份文件、一把尺，**尺照文件種類綁死，不臨場判**：

| 文件 | lens |
|---|---|
| Design Doc（`-design.md`） | `direction`——方向對不對、foreclose 了什麼、有沒有更便宜的做法 |
| 實作計畫（`docs/plans/<feature>.md`） | `implementation`——對不對得上既有 code 的名字、契約、呼叫點 |
| PM／RD 需求 spec | `requirement`（由 phase-workflow 的入口 B 處理，不在這裡） |

它做的是**唯讀文件審查**：Codex 讀完這份文件、寫完 findings 就停在
`AWAITING_HUMAN_DOC_REVIEW`，**不改文件、不寫 code、也不產生可核准的 Plan run**。

findings 就是交付物：人讀完自己改文件，改完用 `ai-review re-review` 跑下一輪
（文件沒動會被拒）。Codex 的 `PASS` 只是一次仔細的閱讀，不是核准——這道閘門沒有
簽章、沒有核准指令，文件收斂到什麼程度才開工由使用者說了算。

## Step 8：Code 審核閘門（Code 出現之後）

實作完成後——不論是這份文件展開的 SDD 產物、既有 branch，還是已修好的 Bug——先選一條
review 路線（`references/skill-router.md` §3 的三選一），預設是 A。

**A 共識**：呼叫 `/consensus-review`。它的 iOS profile 在 `init` 就用 `--preflight` 收下三個
specialist 的 findings（見 `references/handoff-checklist.md`），Codex 首輪之後直接合併進
單一 Claude 統一修復，**中途不停**。

**B 純 agent**：三個 specialist 唯讀跑完 → 主 session 一次統一修復 → `/ios-polish` →
`/verification-before-completion`，不呼叫 `ai-review`。用在 Codex 不可用或這次不想耗共識額度時。

**C 輕量**：`ios-review` 的兩輪就是全部。門檻是 router §3 的**風險三條全綠**（不碰
concurrency／持久化／網路協定／migration、不改公開契約、測得出來）；趕時間不能當理由。

B 與 C 沒有外部模型交叉驗證，PR 描述要註明。三條路線的終點都是人工 Code Review，
但**核准的形式不同**。

**只在 A 路線成立的規則**：`--preflight` 對 `--profile ios` 必填，且只認 `swiftui`／`ux`／
`resilience` 三個 category，所以走 A 時**輕重都要派這三個 specialist**——`ios-review`、
`perf-auditor`、`architecture-auditor` 那些的產出餵不進去，必須在 `init` 前就修掉（輕省下
的是 6 個閘門 agent 與統一修復循環，不是 specialist）。run 在第一次 PASS 或第六輪結束時
停在 `AWAITING_HUMAN_CODE_REVIEW`，**人工 `approve-code` 前不得 commit、push、merge
或建立 PR**。

**B 與 C 不建立 ai-review run**，所以沒有 `approve-code` 可跑，也不會出現
`AWAITING_HUMAN_CODE_REVIEW`：改成使用者讀完 diff 口頭確認，確認前一樣不得 commit、
push、merge 或建立 PR。這條規則綁的是「人看過」，不是綁那一道指令。

---

## 交接

計畫產出後，告訴用戶：

> 計畫已就緒。接下來必須依序：
> - 先執行 `/consensus-plan` 對這份文件做唯讀審查（lens 照 Step 7 的表綁），等 findings 出來。
> - 由使用者讀 findings、自己改文件；需要再跑一輪就用 `ai-review re-review`。
> - 文件收斂後，才執行 `/subagent-driven-development` 開始實作（每個 Task 一個 agent）。
> - 實作 SwiftUI 時：寫用 `swiftui-specialist`（Apple）、審用 `swiftui-expert-skill`（先查 latest-apis.md 避免過時 API）；架構層以 Step 4 產出的 §0 為準
> - 遇到 bug 時呼叫 `/ios-investigate`；效能問題先 `perf-auditor`，需要證據再用 `trace-analyzer` 錄 trace
> - **不要等所有 Task 做完才驗架構**：照計畫的「中途架構檢查點」，在每一段完整行為走通時就對照架構約束段驗一次。發現偏離先判是哪一種——**實作違約就修實作**並重驗（不准改契約遷就程式碼）；**契約確實不適用**才寫下理由、更新設計決策與測試後繼續。
> - 所有 Task 完成後，執行 Phase 3 品質閘門（輕／重照 router §3，收尾照 handoff-checklist）。
> - 走 phase-workflow 的功能：每張 ticket 用 `/ios-dev tickets/<T>.md` 開新 session 接手（情境 7），做完回寫看板再接下一張。
> - 再依所選的 review 路線收尾（預設 `/consensus-review`；Codex 不可用或改動極小時走 router §3 的 B／C），最後一定交給使用者人工 Code Review。
> - Step 3 長出的 `CONTEXT.md`／`docs/adr/` 隨實作維護；Phase 6 建第二大腦時 MOC 連結過去，不複製。

固定順序是：`consensus-plan（唯讀文件審查）→ 人工改文件 → implementation →
review 路線（A／B／C）→ 人工 Code Review`。文件還沒審過就不要啟動 SDD——這條由工作流
自己守，工具端沒有閘門會擋。不要自動開始實作，讓用戶決定何時執行。

Code 已經存在（既有 branch、SDD 產物、已修好的 Bug）時，直接從 Step 8 選一條 review
路線進場，終點一樣是人工 Code Review。

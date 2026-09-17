# Skill Router — `/ios-dev` Step 0 的情境→組合表

> 這份是**執行時**讀的 mapping。每個 skill／agent「做什麼、從哪裡裝」寫在 repo 根目錄的
> `README.md`，這裡只寫「什麼情境載入什麼、何時問」。
> 表裡引用的 skill 與 agent 沒裝時，照 §9 的替代表走。
> 同資料夾另有兩份：`handoff-checklist.md`（情境 3–7 交棒後的收尾）與
> `plan-template.md`（Step 6 的實作計畫模板與重閘門 agent 清單）。

## 0. Step 0 怎麼跑

這一節是 Step 0 的**單點真相**，`SKILL.md` 不重述、只指向這裡。順序就是執行順序：

1. **先查既有**：描述有指名檔案或功能名時，對目標檔 grep 一次關鍵字（例如「改名」→ `rename`）。已存在的功能換呈現形式（alert 改 sheet）仍算情境 2，但確認畫面要註明「既有 X → 改為 Y」；使用者可能不知道它已存在。
2. **認情境**：從使用者描述、附的檔案路徑、ticket 路徑推斷七情境之一（§1）。推不出才問（AskUserQuestion，七情境分兩題：4＋3）。
3. **認內容軸**（只有小功能／優化／重構／接 ticket 需要）：依 §4 推斷；推不出才問。
4. **前置檢查**（情境 1 無 PM spec、情境 2）：repo 若沒有 `## Agent skills` 區塊（`CLAUDE.md`／`CLAUDE.local.md`／`AGENTS.md`）代表沒跑過 `setup-matt-pocock-skills`，把「先跑一次」寫進下一步確認畫面的「提醒」行。
5. **組 bundle**：查 §1 該列，得到「主 session 載入」「派 agent」「何時問」「收尾」。
6. **架構影響檢查**（情境 2–7，任何會改變行為的任務都要）：
   **先看既有契約**——手上的 ticket／根文件／計畫有沒有「架構約束」段，而且涵蓋得了這次要做的事（owner、注入點、async 生命週期、不變條件都在）？
   - **有且涵蓋得了**（情境 7 接 ticket 最常見）→ **留在實作路徑，不要因為它命中「新增模組」之類的觸發條件就轉走**；那條觸發正是它被規劃出來的原因。確認畫面寫「契約已備（來源：<根文件／ticket>），直接實作」。
   - **沒有、有缺漏、或這次範圍超出它** → 照 `architecture-impact-check.md` 的五問判出**直接擴充／局部整理／模組邊界**；命中中型觸發條件就改走 §2 的中型路線，**回流時只帶缺的那幾格**，不重跑整套規劃。
   結論寫進下一步的確認畫面。
7. **確認一次**：用 §6 的格式出一題 AskUserQuestion；使用者選「照這組跑」才往下。§5 的門檻問題（body >80）在這一題之後、進主流程之前用第二題問。
8. **交棒**：依「主流程」欄啟動第一個 skill。情境 1（無 PM spec）與情境 2 留在 `/ios-dev` 走 Step 1–8；情境 1 有 PM spec 立即交棒 `phase-workflow` 入口 B（Step 1–5 全跳）；情境 3–7 交棒後 `/ios-dev` 不再介入執行，但**要把 `handoff-checklist.md` 該情境那一段原樣印進交棒訊息**——下游 skill 不知道還有收尾。交棒到 `phase-workflow` 時一律印指令、建議開新 session（§8）。

## 1. 七情境組合表

**輕／重只決定 Phase 3 做多少工**（派幾個 auditor、要不要統一修復循環）；**誰當第二雙眼睛由 §3 的 review 路線決定**，兩者正交。
**輕**＝該情境指定的單一 auditor（有的話）先跑、findings 併入 → `ios-review`（兩輪，fix-first）→ 依所選路線收尾 → 人工 Code Review。
**重**＝先派閘門 agent（依情境裁，全部唯讀）＋`review-swarm` → 統一修復 → `/ios-polish` → verification → 依所選路線收尾 → 人工 Code Review。三個 specialist 是 `--profile ios` 的入場券（`--preflight` 必填，且只認 `swiftui`／`ux`／`resilience` 三個 category），輕重都免不了；輕省下的是 6 個閘門 agent、`review-swarm` 與 Phase 3 的統一修復循環。完整順序以 `handoff-checklist.md` 的共通收尾為準。

| 情境 | 內容軸 | 主流程 | 主 session 載入 | 派 agent | 何時問 | 收尾 |
|---|---|---|---|---|---|---|
| **1 新專案／新模組／大功能** | 不問（填「不適用」） | §2 分流樹 | **無 PM spec**：`office-hours`、grill（使用者輸入 `/grill-with-docs`，見 §9）、`swift-architecture-skill`（Step 4）、`swiftui-specialist`、`swift-concurrency`。**有 PM spec**：不載入，立即交棒入口 B | 重：6 個全上（`swiftui-reviewer`、`ux-critique`、`resilience-auditor`、`perf-auditor`、`concurrency-auditor`、`architecture-auditor`）。交棒 phase-workflow 的分支，確認畫面寫「依每張 ticket（情境 7）五條件決定」 | 不問（ticket 數在 Step 5 估） | 留在 `/ios-dev` Step 1–8；交 phase-workflow 的分支，之後每張 ticket 走情境 7 |
| **2 小功能** | 問 | Step 1 → Step 2（有第二大腦才讀）→ Step 3 縮 1 輪 → Step 5 test cases → Step 6 短 plan → Step 7 `/consensus-plan` → `/subagent-driven-development` → 輕 | 功能：專案層 framework skill（自動）＋`swift-concurrency`；畫面：`swiftui-specialist`＋`swiftui-ui-patterns`；兩者都載 | 輕，外加一個先跑：畫面→`architecture-auditor`；功能且符合 §4 concurrency 訊號→`concurrency-auditor` | 目標 view body >80 行：先 `swiftui-view-refactor` 再加，還是直接加。目標 view 已有 ≥1 個 `isPresented`：不問，確認畫面加一句「新 modal 併進 `Identifiable` enum＋`.sheet(item:)`，不新增 Bool」 | 留在 `/ios-dev` Step 1–8 |
| **3 純呈現畫面**（只動版面、樣式、動畫；一碰驗證、持久化、連線、VM 狀態、導航或 async 就**不是**這一列）| 固定畫面 | 答架構五問的第 3 問（會不會多出第二份真相或互斥旗標）→ 直接 Phase 2 → `ios-polish` → 輕 | `swiftui-specialist`＋`swiftui-ui-patterns` | 輕＋先跑 `ux-critique`＋`architecture-auditor` | 同上 body >80 與 isPresented 規則 | `handoff-checklist.md` §3 |
| **4 修正**（bug／issue／維護期） | 不問（填「不適用」） | 有第二大腦先由 `/ios-dev` 讀該功能 MOC（Step 2 的 context budget）→ `/ios-investigate` 五階段 → 修 → 輕或重。root cause 未知或高風險時回 `/ios-dev` Step 1 的「複雜 Bugfix」路徑（repair plan → `/consensus-plan` → 修 → `/consensus-review`） | `ios-investigate`；crash／regression／flaky 在假設階段起 `bug-hunt-swarm`；符合 §4 concurrency 訊號→`swift-concurrency` | 五條件定輕重，確認畫面寫「待定（預判 X，理由）」；重時派 5 個（裁掉 `ux-critique`） | 不問 | `handoff-checklist.md` §4 |
| **5 優化** | 問（效能／行為） | 先量 → 改 → 再量對比 → 重（單畫面改輕） | `swiftui-performance-audit`、`swift-concurrency`、`swiftui-expert-skill/references/performance-patterns.md` | 改前 `perf-auditor` 必跑（疑慮→`trace-analyzer` 錄 trace）；改後 `perf-auditor` 再跑 | 驗收數字是什麼；範圍單畫面還是模組 | `handoff-checklist.md` §5 |
| **6 重構** | 問 | 照 `architecture-impact-check.md`「既有功能的架構重構路徑」：`architecture-auditor` 出基線 → 四項產出（責任地圖／狀態與工作清單／行為不變條件＋補測試／目標邊界與遷移順序）→ `swift-architecture-skill` Deep Refactor Mode 定目標形狀（記 ADR）→ **沿完整行為切分**逐段改 → 測試前後綠 → `architecture-auditor` 對比 → 重。涉及多個 state owner／presentation 流程／async 生命週期時走 `phase-workflow` 重構規劃模式 | `swift-architecture-skill`、`swiftui-view-refactor`（畫面）、`swift-concurrency`（功能）、`orchestrate-batch-refactor`（>3 檔） | 前後 `architecture-auditor`；結束重（純畫面重構省 `concurrency-auditor`） | >3 檔是否平行；既有測試夠不夠當行為快照 | `handoff-checklist.md` §6 |
| **7 接 ticket** | 從 ticket 檔案清單推斷 | 讀 ticket＋根文件對應段＋`CONTEXT.md`／`docs/adr/`＋`coordination/implementation-log.md` → `/writing-plans`（只為這張，不跑 consensus-plan）→ `/subagent-driven-development` → 五條件定輕重 → `/consensus-review` → 回寫 ticket 狀態與 implementation-log → 問「接下一張？」 | 同小功能那列，依內容軸 | 五條件定輕重 | 不問；全部 ticket 完成時提醒 Phase 5 worklog 與 Phase 6 second-brain | `handoff-checklist.md` §7（完整流程在那裡，SKILL.md 不另寫） |

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

> 這一節管的是**審查強度**（收尾要派幾個 agent、走哪條 review 路線），
> **不是架構規模**。責任邊界由 §2 與 `architecture-impact-check.md` 決定，兩者不同軸：
> 一個純畫面可以「輕」卻需要一張 presentation 轉移表。

- 輕：小功能、純畫面（這兩個只受風險三條約束）；以及風險三條全綠**且**規模兩條符合的修正與 ticket
- 重：情境 1、模組級優化、重構，以及**任何踩到風險三條的情境**
- **五條件拆成兩類，適用範圍不同**（這是「兩套答案」的唯一解法）：
  - **風險三條——所有情境、初判與重判都適用**：不碰 concurrency／state machine／持久化／網路協定／migration；不改公開契約；有直接可重現的測試。**踩到任何一條就是重**，不論情境是什麼——小功能改持久化就是重。
  - **規模兩條——只用在情境 4（修正）與情境 7（接 ticket）**：範圍單一且清楚；production diff ≤50 行。小功能與純畫面本來就可能超過 50 行，不套這兩條。
- **判定優先序**：情境決定工作流程（載哪些 skill、派哪些 agent），五條件只決定審查強度。
- **實作完成後重判一次（所有情境）**：只看風險三條——實作過程中碰到持久化、改了公開契約、或測不出來，就從輕升重，補派該情境的閘門 agent 再收尾；情境 4、7 另加規模兩條。

### Review 路線（三選一，`/consensus-review` 是預設不是唯一）

輕／重決定做多少工，這一欄決定**誰當第二雙眼睛**。在 Step 0 的確認畫面就講出這次走哪條。

| 路線 | 怎麼跑 | 什麼時候選 |
|---|---|---|
| **A 共識**（預設） | 三個 specialist 各回 JSON → `/consensus-review --profile ios --preflight` → Codex 首輪 → 合併 → 單一 Claude 統一修復 → re-review | 改動會進 main、想要 Codex 這個外部模型的第二意見、額度正常 |
| **B 純 agent** | 三個 specialist ＋ 該情境的 auditor（唯讀）→ 主 session 一次統一修復 → `/ios-polish` → `/verification-before-completion` | Codex 不可用（529／額度用完／context 過大導致輸出退化）、或這次不想耗一次共識額度 |
| **C 輕量** | `ios-review`（兩輪 fix-first）→ `/verification-before-completion` | **風險三條全綠**的小改動、純設定或文件。趕時間**不是**理由：踩到風險三條的改動一律不得走 C，至少走 B |

- 三條路線的終點都是**人工 Code Review**，這一站不可省；A 路線另有 `approve-code` 的硬閘門。
- **B、C 沒有外部模型交叉驗證**，PR 描述要註明走的是哪條路線，讓 reviewer 知道這份 diff 沒被 Codex 看過。
- 選了 A 才有「`init` 前／後誰能改 code」的分界；B、C 全程由主 session 修，但一樣只修一次、修完就驗證。

## 4. 內容軸推斷規則

- 描述或 ticket 的檔案清單含 `Views/`、`Components/`，或出現「畫面、sheet、alert、版面、按鈕、動畫、Liquid Glass」→ 畫面
- 含 `ViewModels/`、`Services/`、`Networking/`、`Models/`，或出現「API、串接、儲存、同步、連線、背景工作」→ 功能
- 描述很短、只指到一個 view 時，grep 該 view 裡跟功能名相關的 func：碰 `@AppStorage`／`UserDefaults`／`Service`／`connection`／網路呼叫 → 加上「功能」
- 兩邊都有 → 兩者；都沒有 → 問一題（選項：功能／畫面／兩者）
- **concurrency 訊號**（決定要不要載 `swift-concurrency`／派 `concurrency-auditor`）：描述提到 task／actor／data race／Sendable，**或**症狀是 crash 加間歇（「有時」「偶爾」「flaky」），**或**範圍在連線／stream／Combine 層

## 5. 門檻（數字寫死，改要改這裡）

> 這些數字是**工作量與風險訊號**，用來決定審查強度與要不要先拆；
> **不能代替責任邊界判斷**（那是 §2 與 `architecture-impact-check.md` 的事）。

| 門檻 | 值 | 用在 |
|---|---|---|
| 目標 view body 行數 | >80 → 問先拆或直接加 | 情境 2、3 |
| 平行重構檔數 | >3 → 問是否 `orchestrate-batch-refactor` | 情境 6 |
| 優化鐵律 | 改前沒有 `perf-auditor` 或 trace 數字不動 code；改後同一把尺再量寫進 PR | 情境 5 |
| 重構護欄 | 目標範圍無測試覆蓋 → 先用 SDD 補行為快照測試再動 | 情境 6 |
| architecture-auditor 四閘門 | body >80、`@State` >5、`isPresented:` >1、`onChange` 監看 `should*/did*` | 所有派它的情境；腳本 `~/.claude/skills/ios-dev/scripts/swiftui-metrics.py` |
| ticket 數 | **只決定 `phase-workflow` 的輸出規模**（1–8 張中型 4 份檔／>8 張大型 7 份檔），**不決定要不要進去**——入場看責任邊界（§2） | phase-workflow Step 4 |
| production diff 行數 | >50 行 → 不算輕（規模兩條之一，§3） | **只有情境 4 與情境 7**；小功能與純畫面不套 |

## 6. 確認畫面格式（AskUserQuestion，一題）

```
題目：情境＝<情境名>（內容＝<功能／畫面／兩者／不適用>）<既有功能時加：既有 X → 改為 Y>。這次會：
  載入：<skill a>、<skill b>、<skill c>
  Phase 3 派：<agent d>、<agent e>（<輕／重／待定（預判 X，理由）>）
  Review 路線：<A 共識（預設）／B 純 agent／C 輕量>（<一句理由>）
  架構結論：<契約已備（來源：根文件／ticket）直接實作／直接擴充／局部整理（範圍）／模組邊界（命中哪條觸發條件）>；<要不要產轉移表／async 契約>
  交棒：<第一個 skill 或指令；情境 1 無 PM spec 與情境 2 寫「留在 /ios-dev Step 1」；交棒 phase-workflow 寫指令＋「建議新 session」>
  會問你：<何時問欄的內容，或「不問」>
  提醒：<§0 前置檢查或硬規則，沒有就省略此行>
選項：
  1. 照這組跑（Recommended）
  2. 我要調整（用 Other 說明要加減什麼）
```

## 7. 不進表、永遠生效

- `careful-ios`：破壞性指令護欄，靠 description 自動觸發
- `verification-before-completion`：任何「完成」宣稱前
- Phase 5：結束時問要不要 `work-log-writer`（現行規則不變）
- 專案層 framework skill（例如 `dpearson2699/swift-ios-skills` 裡對到你專案所用 framework 的那幾個）：靠 description 自動載入，不列入 bundle

## 8. 交棒到 phase-workflow 一律開新 session

phase-workflow 自己要做 codebase grounding、產 4–7 份文件、跑一輪 Codex 根文件審查。印出指令並說明「建議開新 session 執行」：

```
入口 A（無 PM spec）：/ios-dev 完成 Step 1–5，把 design doc、Decision Log、§0 寫進功能資料夾後印
  /phase-workflow <design doc 路徑>
入口 B（有 PM spec）：/ios-dev 不做 Step 1–5，直接印
  /phase-workflow 入口 B：<PM spec 來源：GitHub issue URL 或檔案路徑>
```

之後每張 ticket 各自 `/ios-dev tickets/<T>.md` 開新 session。這是「同 session 交棒」的唯一例外。

## 9. 本表引用的名字與沒裝時的替代

安裝指令與來源見 repo 根目錄 `README.md`。進場時用 Glob 檢查 `~/.claude/skills/<name>/SKILL.md`
與 `~/.claude/agents/<name>.md`；缺的照下表替代，並寫進確認畫面的「提醒」行。

- **本 repo 附的**：skill `ios-dev`、`ios-critique`、`ios-harden`；agent `swiftui-reviewer`、`ux-critique`、`resilience-auditor`、`trace-analyzer`、`perf-auditor`、`concurrency-auditor`、`architecture-auditor`、`store-preflight-auditor`、`build-analyzer`
- **第三方 skill**（`~/.claude/skills`，`npx skills update -g` 更新）：`swift-architecture-skill`、`swift-concurrency`、`swiftui-specialist`、`swiftui-whats-new-27`、`swiftui-ui-patterns`、`swiftui-view-refactor`、`swiftui-performance-audit`、`bug-hunt-swarm`、`review-swarm`、`orchestrate-batch-refactor`、`swiftui-expert-skill`、`app-store-preflight`、`asc-*`
- **共識審查**（`consensus-plan`、`consensus-review` 與 `ai-review` CLI）：[peter6601/ai-review](https://github.com/peter6601/ai-review)
- **plugin**：`superpowers:subagent-driven-development`、`superpowers:writing-plans`、`superpowers:test-driven-development`、`superpowers:verification-before-completion`；mattpocock 的 `/grill-with-docs`、`/grill-me`、`setup-matt-pocock-skills` 是 **user-invoked**（只能使用者打字觸發，模型呼叫不到），模型端能呼叫的只有 `mattpocock-skills:grilling`。Step 3 要 grill 時：印出「請輸入 `/grill-with-docs`」等使用者；使用者不在時用 `mattpocock-skills:grilling` 頂替，但它不會長出 `CONTEXT.md`／`docs/adr/`，要自己補
- **同名兩份時一律用無前綴的本機版**（例如 plugin 帶了同名的 `verification-before-completion`）

**本 repo 不含、作者自用未公開的 skill**——表裡仍保留名字，沒裝就走替代：

| 引用的名字 | 它在流程裡的角色 | 沒裝時的替代 |
|---|---|---|
| `office-hours` | Phase 0 產品思考，產 Design Doc | `superpowers:brainstorming` |
| `phase-workflow` | 把 design doc／PM spec 展開成根文件＋ticket bundle | `superpowers:writing-plans` 產根文件，人工切 ticket；每張 ticket 保留「架構約束」段（`plan-template.md`） |
| `ios-investigate` | 五階段除錯，沒有 root cause 不修 code | `superpowers:systematic-debugging` |
| `ios-review` | 兩輪 fix-first 的 pre-landing review | 派 `swiftui-reviewer`＋`concurrency-auditor`，主 session 一次修復；review 路線 C 因此不可用，最低走 B |
| `ios-polish`／`ios-distill` | 出貨前打磨／去蕪存菁 | 以 `ux-critique` 的 findings 為準做一次修復；沒有就跳過並註明 |
| `careful-ios` | 破壞性指令護欄 | 無替代；破壞性指令前人工確認 |
| `second-brain`、`work-log-writer`、`localize-strings` | Phase 4–6 的紀錄、在地化與維護期知識庫 | 跳過；回寫步驟本來就是「有才寫」 |

## 10. 輔助 skill 的介入時機（輸入 → 產出）

| skill／agent | 什麼時候進場 | 輸入 | 產出 |
|---|---|---|---|
| `swift-architecture-skill` | **開發前**，決定邊界 | 五問的答案、既有 §0（有的話）| 模組邊界、owner、適用 pattern＝§0 架構形狀四段 ＋ feature PR checklist |
| `swift-concurrency` | **新增或改變非同步工作前** | 該工作的用途與觸發點 | ownership 契約六格（持有者／生命週期／清理／重入／舊結果失效／isolation）|
| `swiftui-specialist`＋`swiftui-ui-patterns` | 實作呈現與互動時 | 已定案的架構契約 | View 實作；**不自行改變模組責任** |
| `swiftui-view-refactor` | 拆 View 時 | 責任地圖、目標邊界 | 子 View 接必要的資料與操作，不接整個 ViewModel |
| `architecture-auditor` | **第一段有意義的實作完成時**＋最終收尾 | §0／PR checklist、上一次基線 | 契約有沒有被守住（數字只是線索）|
| `concurrency-auditor` | 同上，有 async 工作時 | ownership 契約六格 | 實作有沒有破壞契約 |

兩條規則：

- **專案已確認的架構契約優先於各 skill 的預設風格。** 衝突時以 §0／`docs/adr/` 為準，並在報告裡明講衝突的是哪一條——不要讓兩個 skill 各套一套架構。
- **不要每個任務都無差別載入全部 skill 或派全部 agent。** 載入清單照 §1 該列，agent 照 §3 的輕／重與情境裁法。

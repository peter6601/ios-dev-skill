---
name: phase-workflow
description: 把 design doc（入口 A）或 PM 給的 SPEC（入口 B）展開成可分散 dispatch 的 reference 文件 + 可執行 ticket bundle，**只規劃不寫 code**。觸發場景：使用者說「跑 phase-workflow」、「做功能文件規劃」、「我要做新功能 X」、「做功能 workflow」、「新專案 kickoff」、「展開 ticket / 生 reference 文件」；入口 B：「吃 PM spec」、「把 PM spec 轉 RD spec」、「比照 android 列 spec」、「PM spec 切 ticket」。產出：入口 A 依規模分流的 4-7 份 markdown 文件 + tickets/ 資料夾 + ai-prompts.md；入口 B 先產 rd-spec.md（RD Spec living doc，人審後貼 GitHub issue comment）再展開 ticket。寫到 workspace project 資料夾底下。除對根文件的唯讀文件審查（入口 A Step 4.5／入口 B Step 3.5B）外，不自動接下游 skill。
metadata:
  type: workflow
  template-source: 一個已出貨的大型 iOS 功能的實際文件，變數化 @ 2026-06-01
  rd-spec-source: 一個 PM-spec 功能的實際 RD spec，變數化 @ 2026-09-01
  obsidian-integration: frontmatter + Bases board + GitHub-callouts + lint (link syntax = relative, GitHub-safe)
---

# Phase Workflow — 新功能 / 新專案文件 + Ticket Scaffolding

> **本 skill 只做規劃，不寫 code**。職責邊界：把已通過 Phase 0（office-hours / brainstorming）收斂的 design doc，展開成可分散 dispatch 的 reference 文件 + ticket bundle。下游（`/writing-plans` → 實作）由使用者手動接續；唯一自動接的下游是對**根文件**跑一次 `/consensus-plan` 唯讀審查——入口 A 在 Step 4.5 審 overview.md、入口 B 在 Step 3.5B 審 rd-spec.md（理由見各流程圖下方）。

---

## 何時用

**入場由責任邊界決定，不由 ticket 數決定**；ticket 數只決定輸出幾份檔（見「規模分流邏輯」）。

| 場景 | 是否用本 skill |
|---|---|
| 大型功能（跨模組、多 Stage）| ✅ 必用 |
| 公司功能、PM 給 SPEC（不論規模）| ✅ 走入口 B（PM-spec 入口）|
| **命中中型觸發條件的任何工作** | ✅ 用簡版（4 份檔）。四條觸發：①新增獨立模組，需要對外契約與注入點 ②涉及多畫面的導航、互斥呈現或狀態轉移 ③多種非同步工作需要協調取消、重入與生命週期 ④需要先拆既有 View／ViewModel 才加得進去。**只有兩張 ticket 也算**（判準見 `ios-dev/references/architecture-impact-check.md`）|
| 沿既有清楚契約增加操作 | ❌ 不用，`/ios-dev` 情境 2（Step 6 短 plan），不論幾張 ticket |
| Bug fix | ❌ 不用，`/ios-dev` 情境 4（→ `/ios-investigate`）；除非根因是責任邊界壞掉，那就當中型進來 |
| 重構 | 範圍單純 → `/ios-dev` 情境 6 局部重構；**涉及多個 state owner、presentation 流程或 async 生命週期 → ✅ 走本 skill 的重構規劃模式**（見下）|

**前置條件**：使用者已有 design doc（手寫 PRD 或 `/office-hours` 產出）。沒有 doc 時 skill 會 fallback 問你補（一次列長 list），但 skill 不取代 Phase 0 產品思考。

**入口 B 例外**：PM 已給 SPEC 的公司功能不需 design doc 也不需 Phase 0（視為 PM 已完成產品思考），直接走下方「處理流程 — 入口 B」。

---

## 入口分流

| 入口 | 適用 | 輸入 | Step 3 人審產物 |
|---|---|---|---|
| **A**（現行） | 自家功能，已過 Phase 0（office-hours / grill） | design doc | overview.md + sprint-roadmap.md 大綱 |
| **B**（PM-spec） | 公司功能，PM 給 SPEC | PM spec（HTML / 任意格式）；呼叫格式 `/phase-workflow 入口 B：<GitHub issue URL 或 spec 檔路徑>` | rd-spec.md（RD Spec living doc；過 Step 3.5B 唯讀審查後才貼 issue） |

入口 B 的 Phase 0 視為 PM 已完成；grill 內建於流程（＝該功能唯一一次 grill，不另跑 office-hours / grill-with-docs）。

入口 A 從 `/ios-dev` 交棒過來時（design doc 旁有 Decision Log 與「§0 架構形狀」）：Step 2 intake 只問 Decision Log 沒答到的項目、不重 grill；Step 3 overview.md 的 §0 直接從交棒的 §0 填。domain 由 `/ios-dev` 帶入，不再問。

---

## 處理流程 — 入口 A：design doc（6 步，現行）

```
Step 1. Intake
  ├─ 讀 design doc（path 或內容）
  ├─ 識別 project 名稱 + feature 名稱
  └─ 確認輸出位置 <workspace>/Projects/<Project>/<feature-folder>/（workspace 定義見「Obsidian 整合」）

Step 1.5. Codebase Grounding ⭐（有既有 codebase 時【必做】，全新專案跳過）
  ├─ 跑 references/codebase-grounding.md 的整合面盤點
  ├─ 從 design doc + intake 列「整合面」= feature 會碰/引用的既有符號
  │   （要實作的 protocol / 被取代或 mirror 的主檔 / 注入點 composition root /
  │     紅線檔 / Delta 會改的既有檔 / 既有 test+mock / build config）
  ├─ grep-find 定位每個符號 → 主檔（protocol / 被 mirror 的 service / 注入點）**完整 Read**
  ├─ 建「verified facts」表：真實類名 / 簽名 / 屬性名 / 檔路徑 / 常數值 / 檔是否存在
  ├─ iOS domain：派 `architecture-auditor` 對整合面模組跑一次（四個量化閘門＋pattern），結果進 verified facts 的「現況形狀」欄——ticket 才知道要不要先拆再加
  └─ ⚠️ **design doc 的前瞻假設 ≠ 現況** — 凡 doc 寫「X 改成 Y」「加 Z 檔」都要對「當前 code」重新 grep 驗證，查無就標 (新建) 或 stop+問，不照抄

Step 2. 完整性檢查
  ├─ 跑 references/intake-long-list.md 的 8 項 checklist
  ├─ 識別已涵蓋項 ✅ + 缺項 ❓（item 4 模組 / item 5 reuse 策略 依賴 Step 1.5 verified facts）
  └─ 缺項 priority-batched 列長 list 問使用者一次補完
      ├─ Critical batch: feature 一句話 / 頁面數 / 模組數 / 規模 / ticket 前綴選用範圍
      └─ Secondary batch: 風險 / descope / 跨團隊 deps / 既有系統 reuse 策略

Step 3. 出大綱（先 2 份檔）
  ├─ overview.md      ← 從 design doc + intake 答案 + Step 1.5 verified facts fill template
  │   └─ iOS domain：「§0 架構形狀」段由 `swift-architecture-skill` 填（`/ios-dev` 交棒時已有 §0 → 直接貼；否則此時跑 Quick Recommendation Mode）；§0 在 overview.md 裡，所以 Step 4.5 的根文件審查一併審架構
  ├─ sprint-roadmap.md ← 從規模 + 模組數推 Stage 切分
  └─ STOP，等使用者 review 大綱
  ⚠️ overview 的「技術模組清單 / 紅線檔 / reuse 策略」只能用 verified facts，不用未驗證符號名

Step 4. 確認規模
  ├─ 使用者確認 stage 數 + ticket 預估數
  ├─ 規模分流（只決定輸出幾份檔）：1-8 ticket = 中型 / >8 ticket = 大型
  └─ STOP，等使用者 ack「繼續展開」

Step 4.5. 根文件審查 ⭐（唯讀，本 skill 唯一自動接的下游；入口 B 的對應落點是 Step 3.5B）
  ├─ 對「根文件」跑一次 `/consensus-plan`（Codex 一輪唯讀文件審查，不改文件）
  │   └─ 根文件 = 其他東西從它展開的那一份；入口 A 就是 overview.md
  ├─ lens 多半落在 `requirement`（overview 是需求面文件），但判哪把尺、跟使用者確認，
  │   都由 `/consensus-plan` 自己走，本 skill 不代它決定、也不代它問
  ├─ 拿到 findings 後照 severity 分三種走法：
  │   ├─ verdict `PASS`，或 findings 全是 `minor`／`info` → 繼續 Step 5
  │   ├─ 有 `major` → 不自動往下，把報告交使用者判斷「先改文件還是照原樣展開」
  │   └─ 有 `blocker` → **STOP**，把報告路徑（`status` 的 `summary_path`）交給使用者
  │       └─ 文件由使用者自己改（Codex 唯讀，本 skill 也不代改），改完跑 `re-review`
  └─ 只自動審這一份；context / architecture / 個別 ticket 要審，由使用者指定哪一份再跑

Step 5. 展開其餘檔（依規模）
  中型輸出（4 份 + 看板）：
    overview.md / context.md / tickets/（README + 每 ticket 一檔 + board.base）/ ai-prompts.md
  大型輸出（7 份 + 看板）：
    overview.md / sprint-roadmap.md / architecture/ / context.md /
    tickets/（README + 每 ticket 一檔 + board.base）/ coordination/ / ai-prompts.md

  其中：
  ├─ tickets/ 切到「Stage 1 + Stage 2」即可（後續 Stage 等規格進一步收斂再補）
  │   └─ **一個 ticket = 一個 .md 檔**（frontmatter 驅動 board.base）+ tickets/README.md 索引 + tickets/board.base
  ├─ ⚠️ **每個 ticket 的 Files/Refs 寫進去前**，對其中每個既有符號（類名/檔路徑/屬性/常數）用 Step 1.5 verified facts 核對；新東西標 (新建)，未驗證的查無就 grep 補驗
  ├─ ai-prompts.md 用 variable substitution（intake 收的變數直接代入）
  └─ context.md 列「核心原則 + 已決事項 + 既有系統保護規則」

Step 6. 收尾
  ├─ 跑 lint／引用／frontmatter／孤兒文件檢查
  ├─ 在規劃 worktree commit 所有產出
  ├─ 實際整合該 commit 回 workspace repo 的 main（cherry-pick 或 merge；workspace 不是 git repo 就跳過這三行）
  │   ├─ main 有未提交變更時，先以可回復方式保留，不得覆寫或丟棄
  │   └─ 整合後驗證 main 包含產出、必要檔案存在、git status 符合預期
  ├─ 將 main 上的整合 commit SHA 回報給使用者
  ├─ 提醒目前在 Phase A（初版建構期，見「兩階段」）；commit／push 的授權照使用者或團隊的規則，本 skill 不碰 PR
  ├─ 提醒下游：每張 ticket 用 `/ios-dev tickets/<T>.md` 開新 session 接手（情境 7：writing-plans → SDD → 閘門 → consensus-review → 回寫看板）；本 skill 不自動接
  └─ STOP
```

> [!IMPORTANT]
> **根文件審查是「不自動接下游 skill」的唯一例外（入口 A 在此，入口 B 在 Step 3.5B），而且只有一個理由。** 其餘 reference 檔、所有 ticket、之後的實作，全都從根文件長出來；根文件帶著一個錯往下走，等於把同一個錯複製進七份文件和一疊 ticket。所以它值得在任何東西從它展開之前，先花一輪 Codex 唯讀審查。例外只到根文件為止——`/writing-plans`、`/subagent-driven-development` 一律還是使用者手動接。
> **也只審這一份。** 4-7 份全審＝4-7 個連續 Codex session（一小時起跳），而且 findings 大量重複；其餘文件要審，使用者指定哪一份再跑。

> [!IMPORTANT]
> **worktree commit 不是完工。** 除非使用者明確要求保留在隔離 branch，規劃的完工條件是「文件已實際整合回 workspace `main`」。不得只提供 commit SHA／合併指令就宣告完成。若因權限或衝突無法整合，明確回報 blocker 並繼續保留可恢復狀態。

---

## 處理流程 — 入口 B：PM spec → rd-spec → ticket

> 模板：`references/template-rd-spec.md`。

```
Step 1B. Intake
  ├─ 讀 PM spec（HTML 先抽純文字）＋對應 GitHub issue
  ├─ 查同功能他平台 issue comments 是否已有 RD spec / 拆解 → 有則先吃其「前提定案」當已知事實
  └─ 確認輸出位置（同入口 A）

Step 1.5 Codebase Grounding（同入口 A，必做）
  └─ 功能已動工時加盤點「已完成進度」：branch、commit 快照（as-of）、測試覆蓋、
      與定案前提的偏離點（可派 read-only agent 對照他平台 T 卡逐項盤點）

Step 2B. Grill（取代入口 A Step 2 的長 list）
  ├─ 審訊式多輪 frontier：每輪編號提問、每題附推薦答案，等使用者答完再下一輪
  ├─ 上限 3 輪或 30 分鐘；只問 RD 答得了的決策，事實自己查
  └─ 需 PM/PO/後端拍板的 → 不硬追，收進 rd-spec「待 PO 決定」區
  └─ grill 定案中「難逆轉＋沒脈絡看不懂＋真有取捨」的寫 repo `docs/adr/`、新術語寫 `CONTEXT.md`（與入口 A 的 grill-with-docs 同一份真相來源；情境 7 接 ticket 時會讀）

Step 3B. 產 rd-spec.md（取代 overview.md + sprint-roadmap.md，這兩份不產）
  ├─ iOS／macOS domain：rd-spec 的「§0 架構形狀」段由 `swift-architecture-skill`（Quick Recommendation Mode）填——入口 B 沒有 `/ios-dev` Step 4，這裡是唯一產 §0 與 feature PR checklist 的地方；隨 Step 3.5B 一起被審，`architecture-auditor` 之後拿它當尺
  ├─ 章節依 template-rd-spec.md：版本 changelog / 設計稿對照 / 前提定案表（含本平台落地現況）/
  │   現況總覽 / M×T 卡（未完的開完整卡，已完成壓縮成證據表）/ 本平台特有技術修復 /
  │   PR 拆分 / Out of Scope / 待 PO 決定
  ├─ Ticket ID 用 M/T；他平台已有拆解時**沿用其 T 編號**（同義同號），本平台特有從尾號續編
  └─ STOP，等使用者人審

Step 3.5B. rd-spec 審查 ⭐（唯讀，貼 issue 前的最後一道）
  ├─ 對 rd-spec.md 跑一次 `/consensus-plan`（Codex 一輪唯讀文件審查，不改文件）
  │   └─ rd-spec 就是入口 B 的根文件：ticket、sub-issue、PM／QA 的理解全從它長出來
  ├─ lens 多半落在 `requirement`（rd-spec 是需求面文件），但判哪把尺、跟使用者確認，
  │   都由 `/consensus-plan` 自己走，本 skill 不代它決定、也不代它答 Codex 的問題
  ├─ 拿到 findings 後照 severity 分三種走法：
  │   ├─ verdict `PASS`，或 findings 全是 `minor`／`info` → 繼續 Step 4B 發佈
  │   ├─ 有 `major` → 不自動往下，把報告交使用者判斷「先改文件還是照原樣貼」
  │   └─ 有 `blocker` → **STOP**，把報告路徑（`status` 的 `summary_path`）交給使用者
  │       └─ 文件由使用者自己改（Codex 唯讀，本 skill 也不代改），改完跑 `re-review`
  └─ 審在 Step 4B 之前，不在之後 ⚠️ 一旦貼上 issue，PM／QA 就開始照它辦事、ticket 也跟著切下去；
      那之後才到的 findings 追不回已經拆散出去的東西

Step 4B. 發佈
  ├─ 經使用者核可後貼 GitHub issue comment（去 frontmatter；gh issue comment --body-file）
  └─ 改版：新 comment 標「vN 取代 vN-1」（舊 comment 請使用者刪除或收合），vault 源檔同步 bump

Step 5B. 展開 ticket（同入口 A Step 5，規模分流照舊）
  ├─ 產 context.md / tickets/（一張 T 卡一檔）/ ai-prompts.md
  ├─ ticket frontmatter：`ticket` = T 編號（如 "T12"）、`type` 照常填 S/U/D/I（降為欄位、不進 ID）
  └─ GitHub sub-issue：使用者逐張挑要上的，套公司 ticket 模板，T 編號→實際 issue 編號

Step 6B. 收尾（同入口 A Step 6）
```

> [!IMPORTANT]
> **Step 3.5B 和入口 A 的 Step 4.5 是同一個例外的兩個落點：根文件在任何東西從它展開之前，先花一輪 Codex 唯讀審查。** 入口 B 的根文件是 rd-spec.md，而它比 overview.md 更難回頭——貼上 issue 之後，它同時是 PM 的驗收依據、QA 的測試依據、sub-issue 的切卡依據；到那時才發現需求有洞，要收的不只是一份文件，是已經發散出去的一整排 ticket 和三方的認知。所以審查卡在 Step 4B 之前，而不是發佈之後。
> **一樣只審這一份。** ticket、context.md 要審，由使用者指定哪一份再跑；`/writing-plans`、`/subagent-driven-development` 一律還是使用者手動接。

---

## 完整性 checklist（Step 2 用）

詳見 `references/intake-long-list.md`。8 項：

| # | 項目 | 用來生 |
|---|---|---|
| 1 | Feature 一句話描述 | overview.md § 一句話 |
| 2 | 使用者流程（ASCII 圖） | overview.md § 流程 |
| 3 | 頁面清單（新建 / 修改既有 / 共用元件） | overview.md § 頁面 + tickets |
| 4 | 技術模組清單（Service / Repository / Model 新增） | overview.md § 技術模組 + tickets |
| 5 | 既有系統 reuse 策略（iOS = 紅線檔）| overview.md § 複用 + context.md 保護規則 |
| 6 | Descope 清單（不做什麼）| overview.md § 不做 + context.md 已決事項 |
| 7 | 風險點（至少 3 個）| sprint-roadmap.md § 風險 |
| 8 | Ticket 前綴選用範圍（S / U / D / I 哪幾種）| ai-prompts.md § 9.2 + tickets/README |

---

## Ticket 格式

**ID 規則**：`{stage}-{type}{n}`

| Type letter | 涵義 | 對應 handoff template |
|---|---|---|
| `S` | Service / API / Model / Protocol | § 3.1 |
| `U` | UI / View / Component | § 3.2 |
| `D` | Delta / 改既有 / 紅線檔附近 | § 3.3 |
| `I` | Integration / 導航串接 | § 3.4 |

範例：`4-S1`、`4-U2`、`5-D1`、`6-I1`

**入口 B 例外**：ID 用 M/T（`M{階段}`＋`T{n}`，對齊 rd-spec 拆解；跨平台同義工作沿用對方 T 編號）。S/U/D/I 不進 ID、降為 frontmatter `type` 欄位——board 分組與 handoff template 對應（§ 3.1-3.4）不變。

**一個 ticket = 一個 .md 檔**（用 `references/template-ticket-single.md`）：frontmatter + 鎖死 5 section（純技術 / 無 user-visible 行為的 ticket 可標 `<skip ...>` 跳特定 section）。frontmatter 必含 `ticket / stage / type / status / estimate` + `tags: [phase-ticket]`，驅動 `board.base` 看板。

---

## 🔗 Obsidian 整合（4 項，2026-06-01 加入）

> **workspace**＝你放跨 repo 規劃文件的地方，建議是一個 git 管理的 Obsidian vault（`newLinkFormat: relative`）；不用 Obsidian 也行，只是沒有看板。文件**同時要在 GitHub render**（overview 是給同事的 kickoff），所以**link 語法保持 relative markdown `[text](./x.md)`，不用 wikilink**。

### 1. Frontmatter（每份檔頂都加）

Reference 文件：
```yaml
---
type: phase-doc
feature: {FEATURE_NAME}
doc: {overview|sprint-roadmap|context|ai-prompts|architecture}
status: active
updated: {TODAY}
---
```

Ticket 檔：見 `template-ticket-single.md` frontmatter（`ticket / stage / type / status / estimate / owner / pr / deps / tags:[phase-ticket]`）。

> frontmatter 在 GitHub 上隱形或 render 成表，無害；在 Obsidian 驅動 Bases / Dataview。

### 2. Bases 看板（= 使用者最早想要的 Jira dev board）

產 `tickets/board.base`（複製 `references/template-tickets-board.base`）。三個 view：
- **🗂️ 看板**：cards，依 `status` 分欄（backlog / in-progress / review / done / blocked）
- **📋 全部 ticket**：table，依 `stage` 分組
- **🚧 進行中/卡住**：filter status ∈ {in-progress, review, blocked}

ticket `status` 改值 → 看板自動移欄。這就是 in-vault 的輕量 dev board，不需外部工具。

### 3. GitHub 標準 callouts（兩邊都 render）

只用這 5 個（Obsidian + GitHub 都認）：
| Callout | 用途 |
|---|---|
| `> [!WARNING]` | 紅線檔 / 絕不修改 / regression 風險 |
| `> [!IMPORTANT]` | 已決事項 / 核心策略定案 |
| `> [!NOTE]` | 一般補充 |
| `> [!TIP]` | 實作提示 |
| `> [!CAUTION]` | 高風險操作 |

❌ 不用 Obsidian 自訂 callout（`[!decision]` 等）— GitHub 不 render。

### 4. Lint

reference 檔標 `type: phase-doc`、ticket 檔標 `tags:[phase-ticket]`，讓 lint 挑得出來檢查（broken Refs / 孤兒 ticket / frontmatter 缺欄 / stale）；你有自己的 vault 健檢排程就接上去，沒有就手動跑。規則見 `references/lint-rules.md`。Phase A → B 切換前跑一次。

### Graph view

relative link 已驗證會出現在 Obsidian graph（全部 resolve）。不需改 link 語法就有 graph + backlinks。

---

## 規模分流邏輯

**先分清楚兩件事**：**要不要進來**由責任邊界決定（見「何時用」的四條觸發）；
**進來後產幾份檔**才由工作量決定。

| 規模 | 條件（只管輸出規模）| 輸出檔 |
|---|---|---|
| 中型 | 1-8 ticket，1-3 Stage | overview / context / tickets / ai-prompts |
| 大型 | >8 ticket，4+ Stage，含 Service 層大改動 | + sprint-roadmap / architecture / coordination |

**規模在 Step 4 確認**。如果 Step 3 出大綱時不確定，預設假設大型，使用者 ack 時可下修。
**不要因為只切得出 2 張 ticket 就把中型退回短 plan**——它是不是中型，看的是責任邊界。

### 中型／大型一定要寫進根文件的架構決策

不論幾份檔，overview.md（或 rd-spec.md）的 §0 架構形狀都要答完：

- 模組邊界、對外契約與注入點，依賴方向。
- **state owner／presentation owner／async owner** 各是誰。
- 涉及流程時附 **presentation 轉移表**（目前狀態／事件／下一狀態／副作用），
  並講清楚「關閉開始 vs 關閉完成」各掛什麼副作用。
- 每項非同步工作的 **ownership 契約六格**（持有者／生命週期／清理／重入／舊結果失效／isolation）。
- 每張 ticket 帶著它適用的那幾條當「架構約束」，收尾時 `architecture-auditor` 拿它當尺。

格式與判準見 `ios-dev/references/architecture-impact-check.md`，不在這裡重寫一份。

### 重構規劃模式

重構走本 skill 時，Step 3 的大綱換成四項產出：**責任地圖**、**狀態與工作清單**、
**行為不變條件（＋先補的測試）**、**目標邊界與遷移順序**；ticket 依**完整行為**切分
（一段＝一條行為的狀態、事件、副作用與測試），不按檔案逐一搬移。
本次範圍內可自由新增／拆分／搬移檔案與型別，不必逐檔問。

**入口 B**：rd-spec.md 不分規模一律產出（跨團隊溝通物）；ticket 展開才按上表分流。

---

## 跨領域支援（iOS default）

預設 iOS 專案。domain 決定「要不要套 domain 專屬段」，其餘步驟（intake、grounding、overview、ticket、看板、lint）與平台無關：

| Domain | 行為 | 架構 skill（填 overview §0）|
|---|---|---|
| iOS（default）| 自動套既有系統紅線檔保護規則（見下）、SwiftUI MVVM、Figma node 規範；Step 1.5 派 `architecture-auditor`、Step 3 用架構 skill 填 §0 | `swift-architecture-skill` |
| macOS | 同 iOS，Figma 規範略過 | `swift-architecture-skill` |
| web / 純後端 / 其他 | 跳過 iOS-specific section（紅線檔、SwiftUI、Figma、auditor）；§0 四段照填但由使用者或通用推理回答 | 未定：進第一個該 domain 專案時再選，標準＝pattern 決策框架＋反模式修法＋checklist，不要框架參考書 |

**domain 推斷**（不問）：repo 有 `.xcodeproj`／`Package.swift` 且 target 為 iOS → iOS；macOS target → macOS；`package.json` → web；推不出才在 intake 問一題。`/ios-dev` 交棒過來時 domain 已知，直接帶入。

第一版只測試 iOS path；其他 domain 暫只移除 iOS-specific section，不替換為 domain-specific 內容。

**紅線檔規則**：紅線檔＝本 feature 開發期間要保護的既有系統主檔。不是絕對禁止碰，但改動必須**最小化、additive、向下相容**，不動既有 method body。形態優先序：①additive overload（既有 callsite 0 改動）②帶預設值的 optional 參數 ③在新檔 scope 加 extension。動之前先列「為何新建路徑不行」＋改動範圍（行數、影響 callsite 數）給使用者確認；動完報那幾個檔的 diff 行數。

**兩階段**：**Phase A 初版建構**＝規劃＋連續跑 ticket（dispatch-friendly）；**Phase B rolling 修正**＝初版完工後的 bug fix／Delta／polish，每個 PR 恢復完整 gate（review＋實機驗證）。切換點由使用者宣告。本 skill 是 Phase A 的規劃工具。

---

## Resume 支援

Skill 被觸發時，**先檢查 feature folder 是否已存在**：

| 已存在的檔 | 推進度 | 行為 |
|---|---|---|
| 無檔（folder 不存在） | Step 0 | 從 Step 1 開始 |
| 只有 rd-spec.md（入口 B） | 過 Step 3B | 依序問「Step 3.5B 審查跑過了嗎？→ 已貼 issue？→ 要進 Step 5B 展開嗎？」；快照過舊先重盤點 bump vN |
| 只有 overview.md | 過 Step 3，未到 Step 4 | 列出「已寫 overview」+ 問「要進 Step 4 確認規模嗎？」 |
| overview + sprint-roadmap | 過 Step 4，未展開 | 問「要進 Step 4.5 根文件審查 → Step 5 展開嗎？」 |
| 多份檔 + tickets/ 部分 | 過 Step 5 部分 | 列出「已寫的 / 未寫的」，問從哪續 |
| 7 份檔齊 + board.base，但尚未整合 main | Step 6 未完 | 先 commit／整合／驗證 main，不得宣告完工 |
| 7 份檔齊 + board.base，且 main 已包含 | 完工 | 回報 main 整合 SHA，再提醒下游手動跑 + 開 board.base 看看板 |

Resume 不另建狀態檔，狀態完全從檔案存在性推。

---

## 變數清單（ai-prompts.md 用）

Step 2 intake 時收以下變數，Step 5 寫 `ai-prompts.md` 時自動代入：

| 變數 | 範例 | 詢問時機 |
|---|---|---|
| `{PROJECT_NAME}` | `TodoApp` | 從 design doc 或 cwd 推 |
| `{FEATURE_NAME}` | `共享清單` | intake 必問 |
| `{FEATURE_FOLDER}` | `2.0-SharedLists` | intake 必問 |
| `{FEATURE_FOLDER_FULL_PATH}` | `<workspace>/Projects/TodoApp/2.0-SharedLists` | 自動組 |
| `{STAGE_COUNT}` | `6` | Step 4 確認 |
| `{TICKET_PREFIX_SET}` | `S, U, D, I` | intake 必問 |
| `{DOMAIN}` | `iOS` | intake 必問（預設 iOS）|
| `{EXISTING_SYSTEM_LABEL}` | `1.x 既有系統` | 預設填「既有系統」，使用者可改 |
| `{REDLINE_FILES}` | `ListDetailView, ListSyncManager, ...` | iOS 必問 |

---

## 與其他 skill / memory 的關係

| 對象 | 關係 |
|---|---|
| `/office-hours` | 上游（產出 design doc 餵給本 skill；入口 A）|
| `/ios-dev` | 上游（情境 1 交棒：design doc＋Decision Log＋§0，建議新 session）與下游（情境 7 接 ticket：`/ios-dev tickets/<T>.md`）；路由表在 `skills/ios-dev/references/skill-router.md` |
| PM spec（公司功能） | 入口 B 上游：PM 文件直接餵入，Phase 0 視為 PM 已完成 |
| mattpocock grilling | 入口 B Step 2B 的詢問形式（多輪 frontier、3 輪上限）|
| `/brainstorming` | 上游（同上） |
| `/consensus-plan` | 每個入口自動接一次（唯讀審根文件）：入口 A Step 4.5 審 overview.md、入口 B Step 3.5B 審 rd-spec.md（貼 issue 前）；blocker 就停、findings 交使用者改文件，改完 `re-review` |
| `/writing-plans` | 下游（本 skill 完工後使用者手動接續）|
| `/subagent-driven-development` | 下游（Phase A 期間連續跑 ticket）|
| 兩階段（Phase A／B）| 本 skill 是 Phase A「規劃階段」工具；產出的 ticket 在 Phase A 期間連續 dispatch。本 skill 不碰 PR |
| 紅線檔規則 | 本 skill 在 context.md 寫入紅線檔保護規則（定義見「跨領域支援」）|

---

## Templates 索引

所有實際 template 內容在 `references/`：

| 檔案 | 對應產出 |
|---|---|
| `references/template-rd-spec.md` ⭐ | rd-spec.md（入口 B RD Spec living doc）|
| `references/template-overview.md` | overview.md |
| `references/template-sprint-roadmap.md` | sprint-roadmap.md |
| `references/template-architecture.md` | architecture/<protocol>.md |
| `references/template-context.md` | <feature>-context.md |
| `references/template-tickets-readme.md` | tickets/README.md |
| `references/template-ticket-single.md` ⭐ | tickets/<id>.md（一 ticket 一檔，frontmatter）|
| `references/template-ticket-parent.md` | （備用）narrative grouping in README / 不用 board 時 |
| `references/template-tickets-board.base` ⭐ | tickets/board.base（Obsidian Bases 看板）|
| `references/template-coordination-readme.md` | coordination/README.md |
| `references/template-ai-prompts.md` | ai-prompts.md |
| `references/lint-rules.md` ⭐ | Phase-doc lint 規則 |
| `references/codebase-grounding.md` ⭐ | Step 1.5 整合面盤點（寫文件前驗證既有符號）|
| `references/intake-long-list.md` | Step 2 完整性檢查 prompt 模板 |

Template source = 一個已出貨大型功能的實際文件變數化。
Obsidian 整合 = frontmatter + Bases 看板 + GitHub callouts + lint（link 語法保持 relative）。

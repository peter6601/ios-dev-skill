---
name: phase-workflow
description: 把已收斂的 design doc 或 PM SPEC 展開成功能規劃文件與 ticket，**只規劃不寫 code**。**只在 `/ios-dev` 明確交棒、或使用者直接點名 phase-workflow 時使用**——「我要做新功能 X」這種一般需求要先走 `/ios-dev`，由它判責任邊界後才交棒過來。使用者直接點名的說法：「跑 phase-workflow」、「做功能文件規劃」、「展開 ticket / 生 reference 文件」、「新專案 kickoff」；PM spec 入口：「吃 PM spec」、「把 PM spec 轉 RD spec」、「PM spec 切 ticket」。
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
| **A**（現行） | 自家功能，已過 Phase 0（office-hours / grill） | design doc | overview.md（Step 4 確認是大型後，才補 sprint-roadmap.md 大綱）|
| **B**（PM-spec） | 公司功能，PM 給 SPEC | PM spec（HTML / 任意格式）；呼叫格式 `/phase-workflow 入口 B：<GitHub issue URL 或 spec 檔路徑>` | rd-spec.md（RD Spec living doc；過 Step 3.5B 唯讀審查後才貼 issue） |

入口 B 的 Phase 0 視為 PM 已完成；grill 內建於流程（＝該功能唯一一次 grill，不另跑 office-hours / grill-with-docs）。

入口 A 從 `/ios-dev` 交棒過來時（design doc 旁有 Decision Log 與「§0 架構形狀」）：Step 2 intake 只問 Decision Log 沒答到的項目、不重 grill；Step 3 overview.md 的 §0 直接從交棒的 §0 填。domain 由 `/ios-dev` 帶入，不再問。

---

## 處理流程 — 入口 A：design doc（6 步，現行）

```
Step 1. Intake
  ├─ 讀 design doc（path 或內容）
  ├─ 識別 project 名稱 + feature 名稱
  └─ 決定 output_root（**第一個持久化決策，之後所有路徑都從它長出來**）：
      預設 <ios-repo>/docs/features/<feature-folder>/
      使用者明確給了 external workspace 才用 <workspace>/Projects/<Project>/<feature-folder>/
      （workspace 與看板是選配，定義見「Obsidian 整合」；沒有 workspace 不影響任何一步）

Step 1.5. Codebase Grounding ⭐（這次會改到或引用**任何**既有檔就【必做】，範圍可以只有那幾個檔；repo 裡沒有任何會被碰到的既有 code 才跳過）
  ├─ 跑 references/codebase-grounding.md 的整合面盤點
  ├─ 從 design doc + intake 列「整合面」= feature 會碰/引用的既有符號
  │   （要實作的 protocol / 被取代或 mirror 的主檔 / 注入點 composition root /
  │     紅線檔 / Delta 會改的既有檔 / 既有 test+mock / build config / 驗證指令＝真實的 scheme 與 test target）
  ├─ grep-find 定位每個符號 → 主檔（protocol / 被 mirror 的 service / 注入點）**完整 Read**
  ├─ 建「verified facts」表：真實類名 / 簽名 / 屬性名 / 檔路徑 / 常數值 / 檔是否存在——Step 3 寫進 overview.md「現況盤點」段（入口 B 放 context.md），不要只留在記憶裡
  ├─ iOS domain：派 `architecture-auditor` 對整合面模組跑一次（四個量化閘門＋pattern），結果進 verified facts 的「現況形狀」欄——ticket 才知道要不要先拆再加
  └─ ⚠️ **design doc 的前瞻假設 ≠ 現況** — 凡 doc 寫「X 改成 Y」「加 Z 檔」都要對「當前 code」重新 grep 驗證，查無就標 (新建) 或 stop+問，不照抄

Step 2. 完整性檢查
  ├─ 跑 references/intake-long-list.md 的 8 項 checklist
  ├─ 識別已涵蓋項 ✅ + 缺項 ❓（item 4 模組 / item 5 reuse 策略 依賴 Step 1.5 verified facts）
  └─ 缺項 priority-batched 列長 list 問使用者一次補完
      ├─ Critical batch: feature 一句話 / 頁面數 / 模組數 / 規模 / 行為清單與優先序
      └─ Secondary batch: 風險 / descope / 跨團隊 deps / 既有系統 reuse 策略

Step 3. 出大綱（只產 overview.md；這時規模還沒確認，不產 sprint-roadmap.md）
  ├─ overview.md      ← 從 design doc + intake 答案 + Step 1.5 verified facts fill template
  │   ├─ 「✅ 這次要做」每條給穩定編號 FR1、FR2…（沒有畫面的需求也編）——這份就是 Step 5 切 ticket 的行為清單，也是涵蓋檢查的分母
  │   │   └─ **一條 FR 只寫一件可以單獨 demo 的事**。design doc 的一句話並列兩件（「看到清單，點一列進詳情」）→ 這裡就拆成兩條 FR。
  │   │       判準是**要不要獨立的入口或獨立的機制**：要 → 另一條 FR。不要 → 留在同一條，寫成驗收條件：
  │   │       同一個操作的結果（「重開 app 後還在」「另一頁的狀態同步更新」）、同一個控制項的反向操作（愛心再點一次取消）都不拆。
  │   │       Step 5 才發現的，回來把那條 FR 拆開（新的往後編，純文字拆分不用重審），不要一條 FR 配兩張 ticket——那樣涵蓋檢查抓不到「只做了一半」
  │   └─ iOS domain：「§0 架構形狀」段由 `swift-architecture-skill` 填（`/ios-dev` 交棒時已有 §0 → 直接貼；否則此時跑 Quick Recommendation Mode）；§0 在 overview.md 裡，所以 Step 4.5 的根文件審查一併審架構
  │   ├─ Stage 切分草案寫在「時程與里程碑」段、風險寫在「最重要的風險點」段
  │   ├─ 跨 ticket 的未決問題寫在「開放問題」段；會擋 Stage 1–2 ticket 的，這次 STOP 就一併問使用者
  │   └─ **交棒來的 §0 比模板薄時不自行推導**：對照模板要的格子（模組表、三種 owner、每項 async 的六格、
  │       涉及流程的轉移表、5–8 條 PR checklist）列出缺哪幾格 → 跑 `swift-architecture-skill` 補，或問使用者。
  │       模板格子以外的契約缺口（多訂閱者語意、漏掉的變更怎麼補、錯誤模型）一樣算缺格。
  │       標「推導」的格子不得送 Step 4.5——送審的 §0 每一格都要是使用者或架構 skill 定的
  └─ STOP，等使用者 review 大綱
  ⚠️ overview 的「技術模組清單 / 紅線檔 / reuse 策略」只能用 verified facts，不用未驗證符號名

Step 4. 確認規模
  ├─ 先草切一遍（只列 ID／type／標題／估計，不寫檔）：跑「Foundation 放多少」那幾題，得到 ticket 預估數；
  │   有壓線的型別（估 0.4–0.6 人天）就把兩種切法各會串行幾張一起列出來
  ├─ 使用者確認 stage 數 + ticket 預估數（＋壓線型別選哪種切法）
  ├─ 規模分流（只決定輸出幾份檔）：1-8 ticket = 中型 / >8 ticket = 大型
  ├─ 確認後把 `scale: medium|large` 寫進 overview.md 的 frontmatter（Resume 靠它分辨過沒過 Step 4）
  ├─ **大型**：這時才產 sprint-roadmap.md 大綱（Stage 切分從 overview 的草案展開）
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
  ├─ 產哪些檔**照「規模分流邏輯 → Output manifest」那張表**，這裡不另列一份
  └─ 產完逐檔檢查：所有非外部連結的目標都在 manifest 上，且檔案真的存在

  其中：
  ├─ **切法照「Ticket 切法與格式」**：行為清單（FR#）→ Foundation → Prefactor → 每條行為一張 Behavior；不按技術層切
  ├─ tickets/ 切到「Stage 1 + Stage 2」即可（後續 Stage 等規格進一步收斂再補）
  │   ├─ **一個 ticket = 一個 .md 檔**（frontmatter 驅動 board.base）+ tickets/README.md 索引 + tickets/board.base
  │   └─ 還沒切到的 FR# 在 tickets/README.md 的需求涵蓋表標 `deferred: Stage N`——算已處理，不算漏
  │       （deferred 的 Stage 不計入這次的規模分流；之後補切時總量超過中型上限，再升大型補那三份檔）
  ├─ ⚠️ **產完先跑 `python3 scripts/lint-tickets.py <feature-folder>`，有 🔴 不進 Step 6**（規則在 `references/lint-rules.md`；腳本判不了的兩條——標題語意、模組相不相依——自己對）：
  │   ├─ 涵蓋：每個 FR# 至少一張 ticket 的 `covers` 列到，或標 deferred／列在「不做」
  │   ├─ 依賴：`deps` 都對得到檔、無循環、無前向依賴
  │   └─ 同檔重疊與拆分訊號：命中的列給使用者，排序／合併／註記理由放行
  ├─ ⚠️ **切 ticket 時才發現的契約層未決決策**（protocol 形狀、通知形式、錯誤模型）不寫進 ticket 當待辦：
  │   回 Step 3 補進 §0（使用者定案）；已過 Step 4.5 就告訴使用者根文件變了，由他決定要不要 `re-review`
  ├─ ⚠️ **每個 ticket 的 Files/Refs 寫進去前**，對其中每個既有符號（類名/檔路徑/屬性/常數）用 Step 1.5 verified facts 核對；新東西標 (新建)，未驗證的查無就 grep 補驗
  ├─ ai-prompts.md：變數代入＋處理每一個 `{IF_LARGE：…}` 條件段（中型整段刪掉，大型拿掉標記留內容）；其他模板同樣處理
  └─ context.md 列「核心原則 + 已決事項 + 既有系統保護規則 + 驗證指令（Step 1.5 盤出來的真實 scheme／test target）」

Step 6. 收尾
  ├─ 逐項對「出口檢查」（見文末），每項要有證據
  ├─ 再跑一次 `python3 scripts/lint-tickets.py <feature-folder>`，把輸出貼進回報（0 個 🔴 才算過；🟡 逐條寫處置）
  ├─ 列出產出的檔案清單與 diff 給使用者看，**預設到此為止：不 commit、不 merge、不 push**
  ├─ 使用者明確要求才進 git（照他指定的方式：worktree commit／直接 commit／開 PR）
  │   ├─ 目標 branch 有未提交變更時，先以可回復方式保留，不得覆寫或丟棄
  │   └─ 動完驗證產出在位、必要檔案存在、git status 符合預期，並回報 commit SHA
  ├─ 提醒目前在 Phase A（初版建構期，見「兩階段」）；commit／push 的授權照使用者或團隊的規則——沒講就是不自行 commit、不自行 push，
  │   講了也只覆蓋他明講的那個動作（說了 commit 不等於可以 push）；本 skill 不碰 PR
  ├─ 提醒下游：每張 ticket 用 `/ios-dev tickets/<T>.md` 開新 session 接手（情境 7：writing-plans → SDD → 閘門 → review 路線（預設 B，可選加 Codex）→ 回寫看板）；本 skill 不自動接
  └─ STOP
```

> [!IMPORTANT]
> **根文件審查是「不自動接下游 skill」的唯一例外（入口 A 在此，入口 B 在 Step 3.5B），而且只有一個理由。** 其餘 reference 檔、所有 ticket、之後的實作，全都從根文件長出來；根文件帶著一個錯往下走，等於把同一個錯複製進七份文件和一疊 ticket。所以它值得在任何東西從它展開之前，先花一輪 Codex 唯讀審查。例外只到根文件為止——`/writing-plans`、`/subagent-driven-development` 一律還是使用者手動接。
> **也只審這一份。** 4-7 份全審＝4-7 個連續 Codex session（一小時起跳），而且 findings 大量重複；其餘文件要審，使用者指定哪一份再跑。

> [!IMPORTANT]
> **完工條件是「檔案都產出來、lint 過、使用者看過 diff」，不是「已經進 git」。**
> 本 skill **預設不碰 git**：不 commit、不 merge、不 push、不開 PR——每個 repo 的分支與審查規則不一樣，
> 那是使用者或團隊的決定。要進 git 由使用者明確指示，並指定方式；動完要驗證並回報 SHA，
> 不得只丟一句合併指令就宣告完成。

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
  │   **需求對照** / 現況總覽 / M×T 卡（未完的開完整卡，已完成壓縮成證據表）/ 本平台特有技術修復 /
  │   PR 拆分 / Out of Scope / 待 PO 決定
  ├─ **需求對照表**：PM spec 每個條目給 FR#＋PM spec 章節 → 對到哪張 T 卡 → 狀態（已涵蓋／Out of Scope＋理由／待 PO）。
  │   PM spec 的條目在轉 rd-spec 時掉了，只有這張表抓得到；任何一列空著就不進 Step 3.5B
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
  └─ 改版：新 comment 標「vN 取代 vN-1」（舊 comment 請使用者刪除或收合），`<output_root>` 的源檔同步 bump

Step 5B. 展開 ticket（同入口 A Step 5，規模分流照舊）
  ├─ 產 context.md / tickets/（一張 T 卡一檔）/ ai-prompts.md
  ├─ ticket frontmatter：`ticket` = T 編號（如 "T12"）、`type`／`layers`／`covers`／`deps` 照常填（不進 ID）
  ├─ 沿用他平台 T 編號的卡不重切；本平台特有的卡照「Ticket 切法與格式」切
  └─ GitHub sub-issue：使用者逐張挑要上的，套公司 ticket 模板，T 編號→實際 issue 編號

Step 6B. 收尾（同入口 A Step 6）
```

> [!IMPORTANT]
> **Step 3.5B 和入口 A 的 Step 4.5 是同一個例外的兩個落點：根文件在任何東西從它展開之前，先花一輪 Codex 唯讀審查。** 入口 B 的根文件是 rd-spec.md，而它比 overview.md 更難回頭——貼上 issue 之後，它同時是 PM 的驗收依據、QA 的測試依據、sub-issue 的切卡依據；到那時才發現需求有洞，要收的不只是一份文件，是已經發散出去的一整排 ticket 和三方的認知。所以審查卡在 Step 4B 之前，而不是發佈之後。
> **一樣只審這一份。** ticket、context.md 要審，由使用者指定哪一份再跑；`/writing-plans`、`/subagent-driven-development` 一律還是使用者手動接。

---

## 完整性 checklist（Step 2 用）

詳見 `references/intake-long-list.md`。核心 8 項如下；該檔另有輔助項（規模估計、時程目標、Domain、跨團隊 deps、iOS 紅線檔、ai-prompts 變數），引用時用項目名稱，不用編號：

| # | 項目 | 用來生 |
|---|---|---|
| 1 | Feature 一句話描述 | overview.md § 一句話 |
| 2 | 使用者流程（ASCII 圖） | overview.md § 流程 |
| 3 | 頁面清單（新建 / 修改既有 / 共用元件） | overview.md § 頁面 + tickets |
| 4 | 技術模組清單（Service / Repository / Model 新增） | overview.md § 技術模組 + tickets |
| 5 | 既有系統 reuse 策略（iOS = 紅線檔）| overview.md § 複用 + context.md 保護規則 |
| 6 | Descope 清單（不做什麼）| overview.md § 不做 + context.md 已決事項 |
| 7 | 風險點（至少 3 個）| overview.md § 最重要的風險點（大型另展開到 sprint-roadmap.md § 風險）|
| 8 | 行為清單與優先序（使用者看得到的行為逐條列，P1＝最短可 demo 的主流程）| overview.md § 這次要做（FR#）+ ticket 切法 + 需求涵蓋表 |

---

## Ticket 切法與格式

### 切法：先地基、再一條一條行為

**切分單位是「一條使用者看得到的行為，從 Model 到畫面到導航到測試一次打通」，不是技術層。**
切得對不對只問一句：**在它的 `deps` 與 Demo 行註明的前置都完成的前提下，這張做完能不能上實機 demo 或單獨驗證？**「Service 全做完」不能，所以不是一張 ticket。

| `type`（ID 字母）| 是什麼 | 判準 | 排序 |
|---|---|---|---|
| `Foundation`（`F`）| 契約（protocol）、共用 Model、注入點、mock；共用型別的實作放多少見下方「Foundation 放多少」 | **≥2 條行為都依賴，而且不先定就無法平行**。判準不是「屬於 Service 層」——只有一條行為用到的 Service 不是地基，放進那條行為 | 最前 |
| `Prefactor`（`P`）| 先拆既有 View／ViewModel 才加得進去的整理；紅線檔附近的搬移；**讓既有的 build／test 指令跑得起來**（Step 1.5 實跑發現壞的）| 行為不變；開工前先有行為快照測試（build 修復以「指令跑得過」為準）| Foundation 之後、需要它的行為之前 |
| `Behavior`（`B`）| 一條行為切片 | 標題寫成「使用者能……」；單獨做完可 demo | 依優先序，P1＝最短可 demo 的主流程 |

**切的順序**：列行為清單（＝根文件的需求清單 `FR#`）→ ≥2 條行為共用的東西切成 Foundation → 要先整理既有 code 的切成 Prefactor → 其餘每條行為一張 Behavior。

**Foundation 放多少**——對技術模組清單上的每個型別依序問三題（以**型別**為粒度，不是以方法）：

0. **先過前置條件：這個型別的契約定了嗎？**（只問這次要切的 ticket 會碰到的型別。只被 deferred 的 FR# 用到的型別跳過這題：缺口記進開放問題，等補切那個 Stage 時再問。）
   - **§0 有空格**（方法清單對不上 §0 的描述、async 六格填不出來、通知形式沒定）→ **停，不切 ticket**。回 Step 3 補完 §0 再回來——不要切一份「暫定、補完要重切」的 ticket，也不要把地基標 `blocked` 先出貨。
   - **契約卡在外部**（等後端、等 PM，現在補不了）→ 這個型別只給簽名＋mock，方法本體跟行為走；ticket 的 Refs 指到開放問題的 Q 編號。
1. **幾條行為用到它？**（「這次要做」的每條 FR# 都算，deferred 的也算。）只有一條 → 放進那條行為的 ticket，再小也不進地基；那條行為還沒切（deferred）就記在 README 涵蓋表那一列。
2. **它是不是某個畫面自己的 View／ViewModel？** 是 → 歸第一條**新建或動到**這個畫面的行為；後面的行為用 `deps` 接著往上加。畫面不進地基。Tab／導航殼這種畫面容器一樣，歸第一條需要它的行為；**注入點**（composition root 裡建 store、往下傳）才是地基。
3. **（只問有方法本體的實作型別；Model 與 protocol 本身就是簽名，過了第 1 題就整份進地基。）整個型別的實作連同單元測試，估多少？** ≤0.5 人天 → **整份進 Foundation**，這次切的 Behavior 只用它、不再編輯那個檔。＞0.5 人天 → Foundation 只放簽名＋空骨架＋mock，方法本體跟行為走、`deps` 串行。**估在 0.4–0.6 之間算壓線**：不要自己定，Step 4 的 STOP 列給使用者（附兩種切法各會串行幾張）。

其他限制：整份進地基的型別，單元測試必須在同一張 ticket。Foundation 照樣受拆分訊號約束（production 檔 >5 或 estimate >0.5 人天就拆成 `1-F1`、`1-F2`；彼此沒有依賴才可平行，有就寫 `deps`）。實作時發現超過半天就停：只留 P1 行為會用到的方法，其餘移回對應行為的 ticket 並回寫。

- **層沒有消失，只是降了一級**：Service／UI／Delta／Integration 變成 frontmatter 的 `layers` 欄（這張穿過哪幾層，用來組 handoff prompt，見 `ai-prompts.md` § 3）與 ticket 內 Tasks 的施工順序（Model → Service → View → 導航 → 測試）。
- **導航屬於需要它的那條行為**，不得集中到最後一個 Stage 才第一次串。
- **代價是同檔重疊**：大的共用型別（第 3 題 ＞0.5 人天）與畫面自己的 ViewModel，會被多張 Behavior 輪流改。Foundation 先把骨架建好（後面各行為只做加法）；Files 重疊的 ticket 用 `deps` 串行（`references/lint-rules.md` § H 抓沒排序的）。

### ID 規則：`{stage}-{F|P|B}{n}`

範例：`1-F1`、`2-P1`、`2-B1`、`3-B4`。

**入口 B 例外**：ID 用 M/T（`M{階段}`＋`T{n}`，對齊 rd-spec 拆解；跨平台同義工作沿用對方 T 編號）。**沿用他平台 T 編號的卡不重切**（同義同號的約定優先）；上面的切法只套用在本平台特有、從尾號續編的卡。`type`／`layers` 照常填，不進 ID。

**舊值相容**：2026-09-20 之前產出的功能資料夾用 `{stage}-{S|U|D|I}{n}` 與 `type: Service／UI／Delta／Integration`。**不遷移**，lint 照收。

### 檔案格式

**一個 ticket = 一個 .md 檔**（用 `references/template-ticket-single.md`）：frontmatter＋固定段落（Refs／Files／架構約束／Tasks／Acceptance Criteria／Verification／實作筆記；純技術、無 user-visible 行為的 ticket 可標 `<skip ...>` 跳特定段）。frontmatter 必含 `ticket / stage / type / layers / status / estimate / covers / deps` + `tags: [phase-ticket]`，驅動 `board.base` 看板與 lint。

- `covers`：這張涵蓋根文件的哪幾條需求（`[FR1, FR3]`）。只有 Foundation／Prefactor 可以是空的。
- `deps`：YAML list（`["1-F1", "2-B1"]`）。只能指向同資料夾真的存在、且不在更後面 Stage 的 ticket。**只放「不先 merge 就無法開工」的**：程式碼依賴、同檔排序。只是 demo 時需要資料的前置（清單頁要先有辦法收藏才看得到東西）**不進 `deps`**，寫在 Demo 行（「需 2-B1 已 merge，或用 debug seed」）——否則檔案上可以平行的 ticket 會被白白串起來。
- **拆分訊號**（命中任一條就考慮再拆；Step 4／5 回報給使用者，可註記理由放行；**都是警告，不是硬上限**）：production 檔 >5、estimate >0.5 人天、驗收條件 >4、Behavior 標題並列兩件以上的事（看語意——用頓號、逗號繞過字面比對不算過；Foundation 不適用這條）、跨兩個不相依模組（＝技術模組清單裡彼此沒有依賴的兩個）。

---

## 🔗 Obsidian 整合

**這一整節是選配。** 預設 output_root 是 `<ios-repo>/docs/features/<feature>/`，不需要 Obsidian、不需要 vault；`board.base` 照產，沒有 Obsidian 只是看不到看板。
**workspace**＝你另外放跨 repo 規劃文件的地方（建議是 git 管理的 Obsidian vault）；只有你在 Step 1 明確指定它，產出才會寫到 `<workspace>/Projects/…`。
四項約定：**frontmatter**（reference 檔 `type: phase-doc`、ticket 檔 `tags: [phase-ticket]`）、**Bases 看板**（`tickets/board.base`，依 `status` 分欄）、
**只用 GitHub 標準 callout**（WARNING／IMPORTANT／NOTE／TIP／CAUTION，標記獨佔一行）、**lint**（`scripts/lint-tickets.py`）。**link 一律 relative markdown，不用 wikilink。**
細節與 frontmatter schema 見 `references/obsidian-integration.md`，Step 5 寫檔前讀。

---

## 規模分流邏輯

**先分清楚兩件事**：**要不要進來**由責任邊界決定（見「何時用」的四條觸發）；
**進來後產幾份檔**才由工作量決定。

| 規模 | 條件（只管輸出規模）| 輸出檔 |
|---|---|---|
| 中型 | 1-8 ticket，1-3 Stage | overview / context / tickets / ai-prompts |
| 大型 | **>8 ticket**（判準只有這一條；通常也是 4+ Stage、含 Service 層大改動）| + sprint-roadmap / architecture / coordination |

**規模在 Step 4 確認**。如果 Step 3 出大綱時不確定，預設假設大型，使用者 ack 時可下修。
**不要因為只切得出 2 張 ticket 就把中型退回短 plan**——它是不是中型，看的是責任邊界。

### Output manifest（唯一真相；模板不得連到不在自己這一欄的檔）

```
中型（4 份 + 看板）
  overview.md                     ← 中型的跨 ticket 未決問題寫在這份的「開放問題」段
  context.md                      ← 就叫 context.md，不要加 feature 前綴
  tickets/README.md               ← 逐 ticket 索引
  tickets/<id>.md                 ← 一個 ticket 一檔
  tickets/board.base
  ai-prompts.md

大型（＝中型全部，再加）
  sprint-roadmap.md
  architecture/<topic>.md         ← 主題由 Step 3 決定，沒有固定檔名
  coordination/README.md
  coordination/open-questions.md
  coordination/open-questions-resolved-archive.md
  coordination/backend-requirements.md
  coordination/pm-decisions.md
  coordination/branch-tracker.md      ← commit 後回寫
  coordination/implementation-log.md  ← 選項決策與踩坑回寫
```

> [!WARNING]
> **中型模板不得引用大型專屬檔。** `sprint-roadmap.md`、`architecture/`、`coordination/` 只有大型才產；
> 中型的 `tickets/README.md` 連到 `../sprint-roadmap.md` 就是一開就斷的連結。
> 中型需要回寫時，寫進 ticket 檔自己的 frontmatter 與內文。
>
> **不在這張表上的檔一律不得引用**——`pages/*.md`、`stage-1-foundation.md`、`module-c-*.md`
> 都不是本 skill 的產物，ticket 的 Refs 要指的是 `overview.md`／`context.md`／`architecture/<topic>.md`
> 的**章節**，不是不存在的檔。
>
> **link 一律 relative markdown**（`[text](./x.md)`），**不用 wikilink**——產出同時要在 GitHub render。

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

**例外：爆炸半徑橫跨整個 codebase 的機械式改動**（改名一個到處被用的型別、換掉共用簽名）切不出能單獨綠燈的行為切片，
改用 expand–contract 三段：先新舊並存（一張）→ 依模組分批搬呼叫端（每批一張，都依賴第一張）→ 沒有呼叫端後刪舊（一張，依賴所有搬移批次）。

**入口 B**：rd-spec.md 不分規模一律產出（跨團隊溝通物）；ticket 展開才按上表分流。

---

## 跨領域支援（iOS default）

預設 iOS 專案。domain 決定「要不要套 domain 專屬段」，其餘步驟（intake、grounding、overview、ticket、看板、lint）與平台無關：

| Domain | 行為 | 架構 skill（填 overview §0）|
|---|---|---|
| iOS（default）| 自動套既有系統紅線檔保護規則（見下）、Figma node 規範；架構 pattern **依 §0 選型**（不預設 MVVM）；Step 1.5 派 `architecture-auditor`、Step 3 用架構 skill 填 §0 | `swift-architecture-skill` |
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
| 只有 overview.md，frontmatter 沒有 `scale` | 過 Step 3，未到 Step 4 | 列出「已寫 overview」+ 問「要進 Step 4 確認規模嗎？」 |
| overview.md 有 `scale`（大型另有 sprint-roadmap.md），沒有其他檔 | 過 Step 4，未展開 | 問「要進 Step 4.5 根文件審查 → Step 5 展開嗎？」 |
| 多份檔 + tickets/ 部分 | 過 Step 5 部分 | 列出「已寫的 / 未寫的」，問從哪續 |
| 檔齊 + board.base，但 lint 沒跑 | Step 6 未完 | 先跑 lint 與連結檢查，再列 diff 給使用者 |
| 檔齊 + board.base + lint 過 | 完工 | 列產出清單，提醒下游手動跑；有 workspace 才提 board.base 看板 |

Resume 不另建狀態檔，狀態完全從檔案存在性推。

---

## 變數清單（ai-prompts.md 用）

Step 2 intake 時收以下變數，Step 5 寫 `ai-prompts.md` 時自動代入：

| 變數 | 範例 | 詢問時機 |
|---|---|---|
| `{PROJECT_NAME}` | `TodoApp` | 從 design doc 或 cwd 推 |
| `{FEATURE_NAME}` | `共享清單` | intake 必問 |
| `{FEATURE_FOLDER}` | `2.0-SharedLists` | intake 必問 |
| `{FEATURE_FOLDER_FULL_PATH}` | `<output_root>`，預設 `<ios-repo>/docs/features/2.0-SharedLists` | 自動組（Step 1 決定）|
| `{STAGE_COUNT}` | `6` | Step 4 確認 |
| `{TEST_COMMAND}` | `xcodebuild test -scheme MyApp -destination '…'` | 不問；Step 1.5 grounding 第 8 類盤出來。Step 1.5 跳過時（全新專案）才向使用者要，並在 context.md 照實寫「來源：使用者提供，未對 repo 驗證」|
| `{BUILD_COMMAND}` | `xcodebuild build -scheme MyApp -destination '…'` | 同上 |
| `{DOMAIN}` | `iOS` | 從 repo 推斷（見「跨領域支援」）；推不出才問一題 |
| `{EXISTING_SYSTEM_LABEL}` | `1.x 既有系統` | 用 design doc 對既有系統的叫法；沒有就填「既有系統」 |
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

## 出口檢查（Step 6 逐項對；每項要有證據，不是打勾了事）

- [ ] 沒寫任何 production code
- [ ] 根文件審查跑過；`blocker` 已清，或使用者裁定照原樣展開
- [ ] 每個 `FR#` 有 ticket 接、或標 deferred／不做（lint § F）
- [ ] 每張 ticket 有 Acceptance Criteria、Verification、架構約束；Files 裡的既有符號都對過 verified facts（Step 1.5 真的跳過時，Files 不得出現「編輯」既有檔）
- [ ] 每張 Behavior 寫得出 Demo 行；沒有「一整層一張」的 ticket
- [ ] `deps` 無循環、無前向依賴；同檔重疊已排序或已註明不可平行（lint § G／H）
- [ ] 拆分訊號命中的都處理了，或註記了放行理由
- [ ] `scripts/lint-tickets.py` 0 個 🔴，🟡 逐條有處置（這一條涵蓋 frontmatter、連結、wikilink、殘留 `{IF_…}`、callout、涵蓋、deps、同檔重疊）
- [ ] 產出清單與 diff 已列給使用者；使用者要求進 git 的，commit SHA 已回報

### Red Flags（出現任一條就回頭重切）

- 有一張 ticket 叫「全部 Service」「所有 Model」「UI 元件」
- 最後一個 Stage 才第一次串導航
- Behavior 的標題是元件名或檔名，不是「使用者能……」
- Foundation 裡塞了只有一條行為用到的東西
- 為了湊平行度，拆出互相編輯同一個檔、卻沒有 `deps` 的 ticket

### 常見藉口

| 藉口 | 實際上 |
|---|---|
| 「Service 一次寫完比較有效率」 | 契約猜錯要到最後一張接 UI 時才爆，而且那時每一層都已經照錯的寫完了。唯一的例外是「Foundation 放多少」第 3 題：≥2 條行為共用、契約已定、整份 ≤0.5 人天的型別——賭錯的代價被壓在半天內 |
| 「契約還沒穩，先不接 UI」 | 契約穩不穩，只有接了 UI、走通一條行為才知道。P1 行為就是拿來驗契約的 |
| 「這條行為太小，不值得一張」 | 小不是問題，不能單獨 demo 才是。真的要合併，合併後必須還是**一條**行為、一句話講得完；變成兩件事並列就是不該合 |
| 「先全部切完再看依賴」 | 同檔重疊與前向依賴是切法造成的，切完才看就是整批重切 |

---

## Templates 索引

所有實際 template 內容在 `references/`：

| 檔案 | 對應產出 |
|---|---|
| `references/template-rd-spec.md` ⭐ | rd-spec.md（入口 B RD Spec living doc）|
| `references/template-overview.md` | overview.md |
| `references/template-sprint-roadmap.md` | sprint-roadmap.md |
| `references/template-architecture.md` | architecture/<protocol>.md |
| `references/template-context.md` | context.md |
| `references/template-tickets-readme.md` | tickets/README.md |
| `references/template-ticket-single.md` ⭐ | tickets/<id>.md（一 ticket 一檔，frontmatter）|
| `references/template-ticket-parent.md` | （備用）narrative grouping in README / 不用 board 時 |
| `references/template-tickets-board.base` ⭐ | tickets/board.base（Obsidian Bases 看板）|
| `references/template-coordination-readme.md` | coordination/README.md |
| `references/template-ai-prompts.md` | ai-prompts.md |
| `references/lint-rules.md` ⭐ | Phase-doc lint 規則；哪幾條由腳本跑、哪幾條要自己對，寫在該檔開頭 |
| `scripts/lint-tickets.py` ⭐ | 上面那份規則的腳本版（§ A／B／C／F／G／H）；Step 5 產完與 Step 6 收尾各跑一次。測試：`scripts/test_lint_tickets.py` |
| `references/obsidian-integration.md` | 選配：frontmatter schema、Bases 看板、callout、graph（Step 5 寫檔前讀）|
| `references/codebase-grounding.md` ⭐ | Step 1.5 整合面盤點（寫文件前驗證既有符號）|
| `references/intake-long-list.md` | Step 2 完整性檢查 prompt 模板 |

Template source = 一個已出貨大型功能的實際文件變數化。
Ticket 切法（2026-09-20）參考 github/spec-kit、mattpocock/skills `to-tickets`、addyosmani/agent-skills、automazeio/ccpm（皆 MIT）；只借做法，文字自寫。

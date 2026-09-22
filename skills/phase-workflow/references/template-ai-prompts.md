---
type: phase-doc
feature: {FEATURE_NAME}
doc: ai-prompts
status: active
updated: {TODAY}
---

# AI Prompt Guide — {FEATURE_NAME}

> **專屬於 {PROJECT_NAME} {FEATURE_NAME} 的 AI prompt 指南**
> 通用 iOS 工作流見 `/ios-dev`（`~/.claude/skills/ios-dev/SKILL.md`）
> **這份文件補充的是「{FEATURE_NAME} 專屬 context + negative constraints」**

---

## 核心哲學

> **AI 像新人一樣，進場第一件事是「通盤理解專案」，不是直接動 code**

人類新工程師加入大專案時會：
1. 讀 README 知道專案在做什麼
2. 讀架構圖理解分層
3. 參加 kickoff 會議知道 scope / descope
4. 看 ticket 清單知道自己要做什麼
5. 確認理解後才打地基（model → protocol → service → UI）

**AI 也應該這樣做**。不可以看一個 ticket 就開始寫 code — 那會讓它「自以為推理出 scope 外的東西」。

---

## 🎯 使用情境

<!-- touchpoint: phase-workflow-053 kind=command -->
### 情境 A：**新 session 第一次開工** → 走 § 1 Full Onboarding
### 情境 B：**同一 session 繼續做下一個 ticket** → 走 § 3 Ticket Handoff

---

<!-- touchpoint: none -->
## 1. Onboarding（新 session 必跑）

**目的**：讓 AI 在動任何 code 之前，完整理解 {FEATURE_NAME} 的專案全貌、架構、scope、descope、風險。

### 1.1 Onboarding Prompt — Lite 版（省 token）

> **為什麼是 Lite**：Full 版把所有 `tickets/*.md` parent / 詳細 class/method 都讀完，會佔掉大量 context。Lite 版只讀「架構總覽 + scope + 風險 + 後端協定總覽 + 行為準則」，tickets / pages 細節等拿到 ticket 才按需讀。

### 複製以下整段給 AI：

<!-- touchpoint: phase-workflow-054 kind=gate -->
<!-- touchpoint: phase-workflow-055 kind=mixed -->
```
你是 {PROJECT_NAME} team 的工程師，我們要開始 {FEATURE_NAME} 的開發。

在你動任何 code 之前，請先「**Lite onboarding**」理解專案骨架。

## Lite 必讀

1. {FEATURE_FOLDER_FULL_PATH}/overview.md
   → 全文 — {FEATURE_NAME} 全貌

{IF_LARGE：整個第 2 項只有大型才留；中型刪掉並把後面的編號往前補}
2. {FEATURE_FOLDER_FULL_PATH}/sprint-roadmap.md
   → 只讀以下章節：
     - § 1 架構分層圖
     - § 2 Stage 規劃
     - § 3 人力分工
     - § 4 Descope 清單
     - § 5 風險與緩解
     - § 6 Workflow

{IF_LARGE：3. {FEATURE_FOLDER_FULL_PATH}/architecture/<topic>.md（主題由 Step 3 決定，沒有固定檔名）
   → 全文 — 後端協定總覽}

4. {FEATURE_FOLDER_FULL_PATH}/context.md
   → 全文 — AI 行為準則 / 已決事項 / Skill 使用 / Branch 健康 / 完工回寫 / 遇到情況表

5. {FEATURE_FOLDER_FULL_PATH}/tickets/README.md
   → 全文 — tickets 索引

{IF_LARGE：6. {FEATURE_FOLDER_FULL_PATH}/coordination/README.md（如有跨團隊）
   → 全文 — 三份跨團隊文件 master/filter 關係}

## 🚫 Lite 版不讀（按需才讀）

- ❌ `ai-prompts.md` 本身（使用者的 prompt 模板庫，AI 不需要讀）
- ❌ `tickets/<id>.md`（拿到 ticket 才讀那一份）
{IF_LARGE：- ❌ `architecture/<topic>.md`（ticket Refs 指到才讀對應章節）}
{IF_LARGE：- ❌ `sprint-roadmap.md § 7+`（Stage 細節按需讀）}

---

讀完後，請向我報告：

- 【一句話 {FEATURE_NAME} 目標】
- 【頁面清單】
- 【Stage 順序】
- 【3 個 descope 的重要項目】
- 【3 個最高風險點】
- 【已決事項列出 5 條範例】
- 【本次唯一的核心行為原則是什麼】
- 【本次讀了哪些檔案 / 哪些章節】

我會驗收你的理解，確認無誤後才讓你動 code。

讀完不懂的地方請直接問我，不要自己推理。
```

### 1.2 Onboarding 完成的驗收標準

AI 回報後，應該檢查它是否理解以下要點：

| 驗收項 | 正確答案要點 |
|---|---|
| {FEATURE_NAME} 目標 | {ONE_LINE_DESCRIPTION} |
| 頁面清單 | {PAGE_LIST_SUMMARY} |
| Stage 順序 | {STAGE_NAMES_LIST} |
| Descope 重點 | {DESCOPE_KEY_ITEMS} |
| 最高風險 | {KEY_RISK_ITEMS} |
| 已決事項範例 | {KEY_DECISIONS_LIST} |
| 核心行為原則 | 「不清楚就問，不要自己推理」 |

---

## 3. Ticket Handoff Prompt

> 一張 ticket 的 prompt ＝ **§ 3.0 共同骨架** ＋ 它 frontmatter `layers` 列到的那幾個**層段落**（§ 3.1–3.4）。
> ticket 是依行為切的（Foundation／Prefactor／Behavior），一張 Behavior 通常穿過好幾層，所以不是「一種 ticket 一份範本」。

### 3.0 共同骨架（每張都用）

<!-- touchpoint: phase-workflow-056 kind=engineering -->
<!-- touchpoint: phase-workflow-057 kind=gate -->
<!-- touchpoint: phase-workflow-058 kind=gate -->
```
繼續 {FEATURE_NAME} 開發。

這次要做的 ticket：{ticket_id} {ticket_title}
type：{Foundation|Prefactor|Behavior}｜layers：{這張 ticket 的 layers}

請先讀以下 context（本 session 讀過的可以跳過）：

0. 核心原則 + 已決事項（**每次 ticket 都快速 skim**）：
   {FEATURE_FOLDER_FULL_PATH}/context.md

1. 這張 ticket（整份讀）：
   {FEATURE_FOLDER_FULL_PATH}/tickets/{ticket_id}.md

2. ticket 的 Refs 指到的章節：
   overview.md § {SECTION}（§0 架構形狀、這張涵蓋的 FR#）
   → 未決問題看 overview.md「開放問題」段的 Q 編號
   {IF_LARGE：→ 大型另有 architecture/<topic>.md 的對應 § X.X、coordination/open-questions.md 的 Q 編號}

3. 依賴確認：ticket `deps` 列的前置 ticket 是否都已 merge？還沒有請先告訴我。

{接上 layers 對應層段落的「加讀」}

讀完後，請向我報告：
- 【這張 ticket 的 scope 是什麼；它涵蓋哪幾條 FR#】
- 【要改／新建哪些檔案】
- 【架構約束段裡哪幾條跟這張有關，打算怎麼守】
- 【有沒有碰到已決事項任一條，怎麼處理】
- （Behavior）【這條行為從哪個入口觸發、穿過哪些層、在哪裡結束；走通後怎麼 demo】
- （Foundation）【哪幾張 Behavior 會依賴它；哪些型別整份實作（≥2 條行為共用、契約已定、≤0.5 人天）、哪些只給簽名＋骨架，各自為什麼】
- （Prefactor）【行為不變怎麼證明——先補哪些行為快照測試】
{接上 layers 對應層段落的「回報」}
- 【你建議的實作計畫（3-5 步，依層施工：Model → Service → View → 導航 → 測試）】

我確認後你才能開始寫 code。

走 `/ios-dev tickets/{ticket_id}.md`（情境 7）：/writing-plans → /subagent-driven-development → 閘門與 review 路線 → /verification-before-completion；
收尾照 ticket 的 Verification 段跑（測試指令、build、實機走一遍）。commit／push 等我明講。
```

### 3.1 層段落：Service（`layers` 含 Service）

```
加讀：
- 契約的來源：overview.md 的技術模組清單＋§0 模組邊界；Foundation ticket 定下的 protocol
- {IF_LARGE：Backend API 規格（如涉及）：{FEATURE_FOLDER_FULL_PATH}/architecture/<topic>.md → ticket Refs 標的章節}

回報：
- 【哪些欄位／方法名是根文件或 Foundation 契約已定義的（不能自己發明）】
```

### 3.2 層段落：UI（`layers` 含 UI）

```
加讀：
- {IF_FIGMA：Figma node ID（在 SPEC 中會標示，請回報給我確認能 open）}
- 既有共用元件（若 ticket 用到）：
  - {SHARED_COMPONENT_LIST}
  請讀該元件的檔案後再開始

回報：
- {IF_FIGMA：【Figma 規範的樣式重點（顏色、圓角、padding、font size）】；沒有設計稿改成【版面打算怎麼排、依據是什麼】}
- 【要複用哪些既有元件 vs 新建什麼】
- 【Accessibility Level 1 baseline 打算怎麼做】

流程加一步：新建元件時，/writing-plans 的計畫裡先列元件的 API（輸入、狀態、a11y label）給我看。
```

### 3.3 層段落：Delta（`layers` 含 Delta；改既有 code）⭐

```
⚠️ 這張會改 {EXISTING_SYSTEM_LABEL} 既有 view / code，regression 風險高。

加讀：
- **{EXISTING_SYSTEM_LABEL} 既有 code（完整讀進來）**：
  → ticket Files 區塊標「編輯」的每個既有檔都要用 Read tool 讀一遍
  → 不要只 grep，要完整讀過該 view 的 body 結構
- Negative Constraints：context.md § {EXISTING_SYSTEM_LABEL} 既有 code 保護

回報：
- 【要改哪個既有檔案；原本的 code 結構是什麼（以便判斷 regression 風險）】
{IF_REDLINE：下面的「改動策略選擇」與文末的「保護鐵律」只在這個 feature 有紅線檔、reuse 策略是「新建替代」時留著；既有檔本來就要改的專案（全新 app 的骨架）兩段都刪掉}
- 【改動策略選擇】：
  - 策略 A：新建 outer view / VM 獨立業務邏輯（推薦）
  - 策略 B：共用 VM + View 加 `mode` parameter + 條件渲染
  - 策略 C：新建 view 複用既有 sub-components
  - → 你打算走哪條？理由？
- 【影響的呼叫 site / 既有測試】
- 【regression test 計畫】

⚠️ **{EXISTING_SYSTEM_LABEL} 保護鐵律**：
- 優先走策略 A（新建），不動既有
- 若必須改既有 view/class 簽名，加 optional parameter 預設值向下相容
- 既有 body 邏輯不動，只加條件渲染或透過注入改行為

流程加一步：實作後、進 review 路線前做**手動 {EXISTING_SYSTEM_LABEL} regression**。
```

### 3.4 層段落：Integration（`layers` 含 Integration；這條行為要接導航）

```
加讀：
- 上下游頁面的規格：overview.md 頁面清單＋§0 的 presentation 規則（互斥呈現、轉移表）
- 既有 navigation pattern：{EXISTING_SYSTEM_LABEL} root container / coordinator
  （請先搜尋專案找到正確檔案）

回報：
- 【這條行為要串接哪兩個（或多個）頁面】
- 【navigation 是 push / sheet / fullScreenCover？為什麼】
- 【要動哪些既有 coordinator / root container 檔案】
- 【{EXISTING_SYSTEM_LABEL} 既有 navigation pattern 是什麼】
```

---

## 4. 驗收 AI 開工前理解的三題測試
<!-- touchpoint: phase-workflow-059 kind=gate -->

無論用哪個 ticket 範本，AI 開始寫 code 之前，**至少問 AI 三題**確認它真的理解：

### 問題 1：這個 ticket **不能做** 什麼？

AI 應該能依已決事項講出 **至少 3 條** 跟本 ticket 相關的。

### 問題 2：這個 ticket 的 scope **邊界** 在哪？

AI 應該能清楚說：**我會改這些檔案，不會碰這些檔案**。

### 問題 3：如果遇到 SPEC 沒寫的情況，你會怎麼做？

<!-- touchpoint: none -->
AI 應該回答：**stop + ask**，而不是「自己推理最合理的做法」。

**這三題答不好 = AI 還沒準備好寫 code，叫它重讀文件**。

---

## 9. 附錄：快速指令 & Ticket type 對照表

### 9.1 Session 一開始（5 秒啟動）

```
照 ai-prompts.md § 1.1 跑 Lite onboarding，我要做 {FEATURE_NAME} 開發
```

### 9.2 Ticket type → Prompt 組法對照表 ⭐

拉 ticket 前看它 frontmatter 的 `type` 與 `layers`：

| Ticket ID | type | 常見 layers | Prompt 組法 |
|---|---|---|---|
| `{S}-F{n}` | Foundation（≥2 條行為共用的契約／骨架）| Service；要動既有的注入點／composition root 時再加 Delta | § 3.0＋§ 3.1（含 Delta 再加 § 3.3）|
| `{S}-P{n}` | Prefactor（先整理既有 code，行為不變）| Delta | § 3.0＋§ 3.3 ⭐ |
| `{S}-B{n}` | Behavior（一條使用者看得到的行為）| 看 ticket，常見 Service＋UI＋Integration | § 3.0＋`layers` 列到的每一段 |

> 其中 `{S}` = Stage 編號（1-{STAGE_COUNT}），`{n}` = 該 stage 內該 type 的編號。
> 入口 B 的 ticket ID 是 `T{n}`，一樣看 `type`／`layers`。

### 9.3 判斷規則

```
這個工作該切成哪種 ticket？

1. 是不是 ≥2 條行為都依賴、而且不先定就無法平行？（契約、共用 Model、注入點、共用檔骨架）
   └─ 是 → Foundation
   └─ 否 → 下一題

2. 是不是「行為不變，只是先把既有 code 整理到加得進去」？
   └─ 是 → Prefactor（先補行為快照測試）
   └─ 否 → Behavior：標題寫成「使用者能……」，寫得出 demo 步驟才算切對

這張 ticket 的 layers 有哪些？（可複選）
   有 Service / Model / Repository 的新增或修改 → Service
   寫 View / ViewModel                         → UI
   改既有 view / class 的 body                 → Delta ⭐
   串接 2+ 頁面的導航                          → Integration
```

### 9.4 one-liner 快速啟動範本

```
# Behavior ticket（最常見）
照 ai-prompts.md § 3.0＋這張 layers 對應的層段落，這次做 {ticket_id} {ticket_title}

# Foundation ticket
照 ai-prompts.md § 3.0＋§ 3.1，這次做 {ticket_id} {ticket_title}

# Prefactor ticket，或任何 layers 含 Delta 的 ticket
照 ai-prompts.md § 3.0＋§ 3.3，這次做 {ticket_id} {ticket_title}
⚠️ 會改既有 code，regression 風險高
```

### 9.5 Onboarding 完驗收不過時

```
你的理解還不夠，請重讀 {file} § {section}，然後重新回答 § 1.2 驗收項
```

### 9.6 常見搭配指令

<!-- touchpoint: phase-workflow-060 kind=command -->
<!-- touchpoint: phase-workflow-061 kind=mixed -->
```
# 做完一個 ticket 想壓縮 context 繼續下一個
/compact 然後繼續下一個 ticket

# 想跳過某階段（例如 Onboarding 已在本 session 跑過）
上一個 ticket commit 完畢，直接跳 § 3.X 做下一個：{ticket_id}

# 要求 AI 在實作前停下來等你驗收
每一步完成都停下來等我確認，不要一口氣跑完全部。
  先跑 /writing-plans → 我看計畫 → 實作 code → 閘門與 review 路線 → /verification-before-completion → 停下來等我決定 commit

# 遇到 SPEC 沒寫的情境想讓 AI 停下
如果遇到根文件沒寫到的情境，停下來問我，不要自己推理。
```

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版：{FEATURE_NAME} 專屬 AI prompt 指南 |

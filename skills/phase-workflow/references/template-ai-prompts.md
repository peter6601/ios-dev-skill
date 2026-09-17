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

### 情境 A：**新 session 第一次開工** → 走 § 1 Full Onboarding
### 情境 B：**同一 session 繼續做下一個 ticket** → 走 § 3 Ticket Handoff

---

## 1. Full Onboarding（新 session 必跑）

**目的**：讓 AI 在動任何 code 之前，完整理解 {FEATURE_NAME} 的專案全貌、架構、scope、descope、風險。

### 1.1 Onboarding Prompt — Lite 版（省 token）

> **為什麼是 Lite**：Full 版把所有 `tickets/*.md` parent / 詳細 class/method 都讀完，會佔掉大量 context。Lite 版只讀「架構總覽 + scope + 風險 + 後端協定總覽 + 行為準則」，tickets / pages 細節等拿到 ticket 才按需讀。

### 複製以下整段給 AI：

```
你是 {PROJECT_NAME} team 的工程師，我們要開始 {FEATURE_NAME} 的開發。

在你動任何 code 之前，請先「**Lite onboarding**」理解專案骨架。

## Lite 必讀

1. {FEATURE_FOLDER_FULL_PATH}/overview.md
   → 全文 — {FEATURE_NAME} 全貌

2. {FEATURE_FOLDER_FULL_PATH}/sprint-roadmap.md
   → 只讀以下章節：
     - § 1 架構分層圖
     - § 2 Stage 規劃
     - § 3 人力分工
     - § 4 Descope 清單
     - § 5 風險與緩解
     - § 6 Workflow

3. {FEATURE_FOLDER_FULL_PATH}/architecture/networking.md（如有）
   → 全文 — 後端協定總覽

4. {FEATURE_FOLDER_FULL_PATH}/{FEATURE_CONTEXT_FILE}.md
   → 全文 — AI 行為準則 / 已決事項 / Skill 使用 / Branch 健康 / 完工回寫 / 遇到情況表

5. {FEATURE_FOLDER_FULL_PATH}/tickets/README.md
   → 全文 — tickets 索引

6. {FEATURE_FOLDER_FULL_PATH}/coordination/README.md（如有跨團隊）
   → 全文 — 三份跨團隊文件 master/filter 關係

## 🚫 Lite 版不讀（按需才讀）

- ❌ `ai-prompts.md` 本身（使用者的 prompt 模板庫，AI 不需要讀）
- ❌ `architecture/networking-rest.md`（REST ticket 時才讀對應章節）
- ❌ `architecture/networking-messages.md`（WS/Model ticket 時才讀）
- ❌ `pages/*.md`（UI/Delta ticket 時才讀對應那份）
- ❌ `tickets/*.md` parent（拿到 ticket 才讀對應那份）
- ❌ `sprint-roadmap.md § 7+`（Stage 細節按需讀）

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

## 3. Ticket Handoff Prompt 範本

### 3.1 Service / Network / Model ticket 範本（type letter `S`）

```
繼續 {FEATURE_NAME} 開發。

這次要做的 ticket：{ticket_id} {ticket_title}

請先讀以下 context（如果你已經在本 session 讀過可以跳過）：

0. 核心原則 + 已決事項（**每次 ticket 都快速 skim**）：
   {FEATURE_FOLDER_FULL_PATH}/{FEATURE_CONTEXT_FILE}.md

1. Tickets 索引：
   {FEATURE_FOLDER_FULL_PATH}/tickets/README.md
   → 依 ticket id 前綴找到對應 parent 檔案

2. 對應 ticket 完整內容：
   {FEATURE_FOLDER_FULL_PATH}/tickets/<對應檔案>.md
   → 搜尋 "{ticket_id}" 找到該 sub-ticket section

3. Backend API 規格（必讀，如涉及）：
   {FEATURE_FOLDER_FULL_PATH}/architecture/networking.md
   → 該 ticket 標的 Refs 章節

4. 該 ticket 提到的 open question（若有）：
   {FEATURE_FOLDER_FULL_PATH}/coordination/open-questions.md
   → 搜尋 ticket Refs 中提到的 Q 編號

讀完後，請向我報告：
- 【這個 ticket 的 scope 是什麼】
- 【要改/新建哪些檔案】
- 【哪些欄位/方法名是 networking.md 已定義的（不能自己發明）】
- 【這個 ticket 有沒有碰到已決事項任一條，怎麼處理】
- 【你建議的實作計畫（3-5 步）】

我確認後你才能開始寫 code。

走 /writing-plans → 實作 → /review → /verification-before-completion 流程。
```

### 3.2 UI / Page ticket 範本（type letter `U`）

```
繼續 {FEATURE_NAME} 開發。

這次要做的 ticket：{ticket_id} {ticket_title}（屬於 Page {X}）

請先讀以下 context：

0. 核心原則 + 已決事項：
   {FEATURE_FOLDER_FULL_PATH}/{FEATURE_CONTEXT_FILE}.md

1. Tickets 索引：
   tickets/README.md → UI ticket 依 page 編號找對應檔案

2. 對應 ticket 完整內容：
   tickets/<對應檔案>.md → 搜尋 "{ticket_id}"

3. Page {X} 完整 SPEC：
   pages/0{X}-*.md
   → 特別注意 § 4 UI 結構 + § 5/6 互動流程 + § 9/10 Acceptance Criteria

4. Figma node ID（在 SPEC 中會標示，請回報給我確認能 open）

5. 既有共用元件（若 ticket 用到）：
   - {SHARED_COMPONENT_LIST}
   請讀該元件的檔案後再開始

讀完後，請向我報告：
- 【這個 ticket 的 UI scope 是什麼】
- 【Figma 規範的樣式重點（顏色、圓角、padding、font size）】
- 【要複用哪些既有元件 vs 新建什麼】
- 【這個 ticket 有沒有碰到已決事項任一條，怎麼處理】
- 【Accessibility Level 1 baseline 打算怎麼做】
- 【你建議的實作步驟（3-5 步）】

我確認後你才能開始寫 code。

走 /writing-plans → /component（若新建元件）→ 實作 → /review → /verification-before-completion 流程。
```

### 3.3 Delta（改既有）ticket 範本（type letter `D`）

```
繼續 {FEATURE_NAME} 開發。

這次要做的 ticket：{ticket_id} {ticket_title}
⚠️ **這是改 {EXISTING_SYSTEM_LABEL} 既有 view / code 的 Delta ticket，regression 風險高**

請先讀以下 context：

0. 核心原則 + 已決事項：
   {FEATURE_FOLDER_FULL_PATH}/{FEATURE_CONTEXT_FILE}.md

1. Tickets 索引：
   tickets/README.md → 找對應 ticket 所在的 parent 檔案

2. 對應 ticket 完整內容：
   tickets/<對應檔案>.md → 搜尋 "{ticket_id}"

3. 該 Delta 依據的 SPEC：
   pages/0{X}-*.md § 3 切入點策略 + § 4 差異清單

4. **{EXISTING_SYSTEM_LABEL} 既有 code（完整讀進來）**：
   → ticket Files 區塊列的每個檔案路徑都要用 Read tool 讀一遍
   → 不要只 grep，要完整讀過該 view 的 body 結構

5. Negative Constraints {EXISTING_SYSTEM_LABEL} 既有 code 保護原則：
   {FEATURE_CONTEXT_FILE}.md § {EXISTING_SYSTEM_LABEL} 既有 code 保護

讀完後，請向我報告：
- 【這個 ticket 要改哪個既有檔案】
- 【原本的 code 結構是什麼（以便判斷 regression 風險）】
- 【改動策略選擇】：
  - 策略 A：新建 outer view / VM 獨立業務邏輯（推薦）
  - 策略 B：共用 VM + View 加 `mode` parameter + 條件渲染
  - 策略 C：新建 view 複用既有 sub-components
  - → 你打算走哪條？理由？
- 【影響的呼叫 site / 既有測試】
- 【這個 ticket 有沒有碰到已決事項任一條，特別注意 {EXISTING_SYSTEM_LABEL} 既有 code 保護原則】
- 【regression test 計畫】

我確認後你才能開始寫 code。

⚠️ **{EXISTING_SYSTEM_LABEL} 保護鐵律**：
- 優先走策略 A（新建），不動既有
- 若必須改既有 view/class 簽名，加 optional parameter 預設值向下相容
- 既有 body 邏輯不動，只加條件渲染或透過注入改行為

走 /writing-plans → 實作 → **手動 {EXISTING_SYSTEM_LABEL} regression** → /review → /verification-before-completion 流程。
```

### 3.4 Integration ticket 範本（type letter `I`）

```
繼續 {FEATURE_NAME} 開發。

這次要做的 ticket：{ticket_id} {ticket_title}（屬於 Module {INTEGRATION_MODULE_NAME}）

這是串接多個 Page/Module 的 integration ticket，依賴上下游都已完成。

請先讀以下 context：

0. 核心原則 + 已決事項：
   {FEATURE_FOLDER_FULL_PATH}/{FEATURE_CONTEXT_FILE}.md

1. 對應 ticket 內容：
   tickets/module-{INTEGRATION_MODULE_NAME}.md
   → 搜尋 "{ticket_id}"

2. **上下游 Page 的 SPEC**（至少 2 份）：
   ticket 描述中提到的 Page SPEC，都要讀過對應的 § 互動流程 / § 跨頁依賴
   同時讀對應的 `tickets/page-0X-*.md` 確認前置 sub-ticket 是否都已完成

3. 既有 navigation pattern：
   {EXISTING_SYSTEM_LABEL} root container / coordinator
   （請先搜尋專案找到正確檔案）

4. 依賴的 ticket 狀態確認：
   ticket deps 中列的前置 ticket 是否都已完成 merge？若未完成請告知。

讀完後，請向我報告：
- 【這個 integration 要串接哪兩個（或多個）頁面】
- 【使用者流程（3-5 步）】
- 【navigation 是 push / sheet / fullScreenCover？為什麼】
- 【要動哪些既有 coordinator / root container 檔案】
- 【{EXISTING_SYSTEM_LABEL} 既有 navigation pattern 是什麼】
- 【這個 ticket 有沒有碰到已決事項任一條】

我確認後你才能開始寫 code。
```

---

## 4. 驗收 AI 開工前理解的三題測試

無論用哪個 ticket 範本，AI 開始寫 code 之前，**至少問 AI 三題**確認它真的理解：

### 問題 1：這個 ticket **不能做** 什麼？

AI 應該能依已決事項講出 **至少 3 條** 跟本 ticket 相關的。

### 問題 2：這個 ticket 的 scope **邊界** 在哪？

AI 應該能清楚說：**我會改這些檔案，不會碰這些檔案**。

### 問題 3：如果遇到 SPEC 沒寫的情況，你會怎麼做？

AI 應該回答：**stop + ask**，而不是「自己推理最合理的做法」。

**這三題答不好 = AI 還沒準備好寫 code，叫它重讀文件**。

---

## 9. 附錄：快速指令 & Ticket 前綴對照表

### 9.1 Session 一開始（5 秒啟動）

```
照 ai-prompts.md § 1.1 跑 Lite onboarding，我要做 {FEATURE_NAME} 開發
```

### 9.2 Ticket 前綴 → Template 對照表 ⭐

拉 ticket 前先查這張表決定用哪個 § 3.X：

| Ticket 前綴 | 類型 | 用 Template | one-liner 範例 |
|---|---|---|---|
| `{S}-S{n}` | Service / API / Model / Protocol | § 3.1 Service | `照 § 3.1 做 {S}-S{n} <title>` |
| `{S}-U{n}` | UI / View / Component | § 3.2 UI | `照 § 3.2 做 {S}-U{n} <title>` |
| `{S}-D{n}` | Delta / 改既有 | § 3.3 Delta ⭐ | `照 § 3.3 做 {S}-D{n} <title>` |
| `{S}-I{n}` | Integration / 導航串接 | § 3.4 Integration | `照 § 3.4 做 {S}-I{n} <title>` |

> 其中 `{S}` = Stage 編號（1-{STAGE_COUNT}），`{n}` = 該 stage 內該 type 的編號

**新增 ticket 時，append 一行到此表（手動維護）**。

### 9.3 判斷規則

```
ticket 屬性 → template 選擇

1. 是否改既有 view / class 的 body？
   └─ 是 → § 3.3 Delta ⭐
   └─ 否 → 下一題

2. 是否寫 UI / View / ViewModel？
   └─ 是 → § 3.2 UI
   └─ 否 → 下一題

3. 是否串接 2+ Page 的導航？
   └─ 是 → § 3.4 Integration
   └─ 否 → § 3.1 Service
```

### 9.4 one-liner 快速啟動範本

```
# UI / Page ticket
照 ai-prompts.md § 3.2，這次做 {ticket_id} {ticket_title}

# Service / Network / Model / Protocol ticket
照 ai-prompts.md § 3.1，這次做 {ticket_id} {ticket_title}

# Delta（改既有）ticket
照 ai-prompts.md § 3.3，這次做 {ticket_id} {ticket_title}
⚠️ 這是 Delta ticket，regression 風險高

# Integration ticket
照 ai-prompts.md § 3.4，這次做 {ticket_id} {ticket_title}
```

### 9.5 Onboarding 完驗收不過時

```
你的理解還不夠，請重讀 {file} § {section}，然後重新回答 § 1.2 驗收項
```

### 9.6 常見搭配指令

```
# 做完一個 ticket 想壓縮 context 繼續下一個
/compact 然後繼續下一個 ticket

# 想跳過某階段（例如 Onboarding 已在本 session 跑過）
上一個 ticket commit 完畢，直接跳 § 3.X 做下一個：{ticket_id}

# 要求 AI 在實作前停下來等你驗收
每一步完成都停下來等我確認，不要一口氣跑完全部。
  先跑 /writing-plans → 我看計畫 → 實作 code → /review → /verification-before-completion → 停下來等我決定 commit

# 遇到 SPEC 沒寫的情境想讓 AI 停下
如果遇到 SPEC / networking.md 沒寫到的情境，停下來問我，不要自己推理。
```

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版：{FEATURE_NAME} 專屬 AI prompt 指南 |

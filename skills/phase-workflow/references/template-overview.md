---
type: phase-doc
feature: {FEATURE_NAME}
doc: overview
status: active
updated: {TODAY}
# scale: medium|large   ← Step 4 確認規模後才加這一行（拿掉註解），Resume 靠它判斷進度
---

# {FEATURE_NAME} — 功能總覽

> **給同事的 kickoff 文件**：快速理解這次要做什麼、會動到哪些模組、每個頁面的功能
> **閱讀時間**：10-15 分鐘
> **更深入的文件**：見本檔最後的「想深入了解某一塊？」對照表

> [!IMPORTANT]
> **核心策略**：{KEY_STRATEGY_ONE_LINER — 例如「所有新頁面一律走『新建 outer view + 複用既有子元件』策略，既有整頁 view 全部不動」}

---

## 🎯 一句話說明

> **{ONE_LINE_DESCRIPTION}**

{ONE_PARAGRAPH_CONTEXT — 說明這個 feature 在整個 app 中扮演什麼角色、{EXISTING_SYSTEM_LABEL} 哪些既有元件會被複用、{DOMAIN} 端負責什麼、其他端負責什麼}

---

## 🌊 使用者流程（從沒啟用到結束）

```
{ASCII_USER_FLOW}

範例（某個待辦清單 app 的「共享清單」功能）：
┌──────────────────────────────────────────────────────────────┐
│  Side Menu                                                   │
│     ↓                                                        │
│  清單設定頁（既有）                                          │
│     ↓ 底部新增 Tab Bar 切換                                  │
│  共享設定頁（Page 01 - 新）                                  │
│     ├─ 選可編輯成員（最多 4 位）                             │
│     ├─ 選唯讀成員（最多 8 位）                               │
│     └─ 底部 peek：分享邀請連結                               │
│              ↓ swipe up                                      │
│     邀請連結分享 sheet（Page 02 - 新）                       │
│              ↓ 按開始共享                                    │
│  共享中頁（Page 03 - 新建 outer view + 複用子元件）          │
│              ↓ 按停止                                        │
│  清單詳情（Page 06 - 改既有詳情頁）                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 📏 功能範圍（做 / 不做）

### ✅ 這次要做

> 每條給穩定編號 `FR1、FR2…`（沒有畫面的需求也編），寫成使用者看得到的行為。**一條只寫一件可以單獨 demo 的事**——一句話並列兩件就拆成兩條。判準：要不要獨立的入口或機制。同一個操作的結果（重開還在、另一頁同步）與同一個控制項的反向操作（再點一次取消）不拆，寫成那條的驗收條件。
> ticket 依這份清單切、用 `covers` 指回來；每條 FR# 都要有 ticket 接，或標 deferred／移到「不做」。
> 編號定了就不重排——刪掉的留洞，新增的往後編。

{LIST_WHAT_TO_DO}

| # | 使用者能…… | 優先序 |
|---|---|---|
| FR1 | 範例：清單擁有者能設定共享的成員、人數上限與權限後開始共享 | P1 |
| FR2 | 範例：清單擁有者能叫出邀請連結分享 sheet 讓成員加入 | P1 |
| FR3 | 範例：成員能在共享中頁即時看到清單的更新 | P1 |
| ... | | |

### ❌ 這次不做（已與 PM 對齊）
{LIST_DESCOPE}
- 範例：成員暱稱編輯 UI
- 範例：留言編輯 UI
- 範例：複雜 offline 處理
- ...

---

## 📱 頁面清單

### 🆕 新頁面（{NEW_PAGE_COUNT} 個）

{FOR_EACH_NEW_PAGE}
#### Page {N} — {PAGE_NAME}
**一句話**：{PAGE_PURPOSE}

**功能**：
- {FEATURE_BULLET_1}
- {FEATURE_BULLET_2}
- ...

**為什麼要做**：{WHY}

**實作策略**：
- {STRATEGY — 例如「新建 outer view + 複用既有子元件」或「擴充既有 view」}
- {COMPONENTS_TO_REUSE}
- {NEW_COMPONENTS}

---

### 🔧 修改既有頁面（{MODIFIED_PAGE_COUNT} 處）

{FOR_EACH_MODIFIED_PAGE}
#### 修改 {N}：{EXISTING_PAGE_NAME}（{EXISTING_SYSTEM_LABEL} 既有）
**改什麼**：{WHAT_CHANGES}

**為什麼**：{WHY}

**影響**：{IMPACT_ON_EXISTING_BEHAVIOR}

---

### 🧩 新建共用頁面 / 元件（{SHARED_COMPONENT_COUNT} 個）

{FOR_EACH_SHARED_COMPONENT}
#### {COMPONENT_NAME}
**一句話**：{ONE_LINE}

**功能**：
- {BULLET}

**為什麼是新元件**：{WHY}

---

## 🧭 §0 架構形狀（iOS／macOS domain；由 `swift-architecture-skill` 填，`architecture-auditor` 依此稽核每張 ticket）

> **Pattern 與理由**：{PATTERN_PRIMARY}（分層）＋ {PATTERN_PRESENTATION}（presentation）— {WHY_PATTERN：對照 selection-guide 決策矩陣的 2–3 個因素}

**模組邊界**（每個模組一行：誰 own 什麼 state、對外 protocol、注入點）：

| 模組 | own 的 state | 對外 protocol | 注入點 |
|---|---|---|---|
| `{ModuleA}` | {STATE} | `{ProtocolA}` | {COMPOSITION_ROOT} |

**State 與 presentation 規則**（通用底線只有這兩條，其餘由選定的 pattern 決定）：
- **互斥**呈現（sheet／alert／navigation／toast 同時只能有一個）用一個 `Identifiable` enum ＋ `.sheet(item:)`；純局部開關保留 Bool
- ViewModel 只暴露狀態（`phase`、`route`），**不用 `should*`／`did*` 旗標指揮 View**
- {SELECTED_PATTERN_STATE_RULES：由 `swift-architecture-skill` 依所選 pattern 填。MVI／TCA 才有「單一 `send(Action)` 入口」這條；MVVM 有多個公開方法是合法的，不要硬套}
- {FEATURE_SPECIFIC_STATE_RULES}

**非同步工作的 ownership 契約**（每一項工作填六格；**Task 的數量與位置是線索，不是判準**）：

| 工作 | 啟動者與持有者 | 生命週期 | 結束與清理 | 重入策略 | 舊結果如何失效 | isolation 與逾時 |
|---|---|---|---|---|---|---|
| `{WORK_1}` | {OWNER} | {LIFECYCLE} | {CLEANUP} | {REENTRANCY} | {STALE} | {ISOLATION} |

- 優先 structured concurrency（`.task(id:)`、`async let`、task group）；需要 handle 才存 `Task`，存了就在表裡寫清楚誰 cancel、何時 cancel
- **不為了符合規則把工作硬搬到 Service，也不要求全部塞進單一 `run()`**——判準是六格填不填得出來
- Combine 只在邊界（NotificationCenter／KVO／第三方 SDK），進 ViewModel 前 `.values` 轉 AsyncSequence
- {SELECTED_PATTERN_ASYNC_RULES：所選 pattern 另外要求的 owner 規則，沒有就留空}

**本 feature 的 PR checklist**（5–8 條，從 `swift-architecture-skill` 的 pattern checklist 裁；`architecture-auditor` 用）：
1. {CHECK_1}
2. {CHECK_2}
3. {CHECK_3}

---

## 🏗️ 技術模組清單

### 🆕 新增的 Service / Model / Repository（共 {NEW_MODULE_COUNT} 個）

| 模組 | 作用 | 技術 |
|---|---|---|
| `{ModuleA}` | {ROLE} | {TECH_STACK} |
| `{ModuleB}` | {ROLE} | {TECH_STACK} |

### 🔧 修改的 {EXISTING_SYSTEM_LABEL} 既有模組

> **核心策略**：{REUSE_STRATEGY_SUMMARY}

| 既有模組 | 修改內容 | 影響範圍 |
|---|---|---|
| `{ExistingA}` | {WHAT_CHANGES — additive optional parameter? subclass? overload?} | {SCOPE} |

> [!WARNING]
> **紅線檔（以下既有檔案完全不動）**
> {IOS_ONLY_IF_iOS}
> - `{RedlineFile1}`
> - `{RedlineFile2}`
> - ...

### 🧩 新建的 UI 共用元件

| 元件 | 用在哪 |
|---|---|
| `{ComponentA}` | {WHERE_USED} |

---

## ♻️ {EXISTING_SYSTEM_LABEL} 複用策略

> **核心策略**：{ONE_SENTENCE_STRATEGY}

### 直接複用（不改這些檔案）

| {EXISTING_SYSTEM_LABEL} 既有 | 本 feature 怎麼用 |
|---|---|
| `{ReusedA}` | {HOW_REUSED} |

### 不動的整頁 view（本 feature 新建替代品）

| {EXISTING_SYSTEM_LABEL} 整頁 | 本 feature 新建替代 |
|---|---|
| `{LegacyView}` | → `{NewView}` |

---

## 🔎 現況盤點（Step 1.5 verified facts；as-of `{COMMIT_OR_DATE}`）

<!-- Step 1.5 真的跳過（沒有任何會被碰到的既有 code）就整段刪掉。
這張表是技術模組清單與每張 ticket 的 Files／Refs 的依據；下游 session 與 Resume 靠它知道「規劃當時 code 長什麼樣」。
只列這個 feature 會碰到或引用的符號，不是整個 codebase 的清單。design doc 說的跟 code 不一樣的，一定要列。 -->

| 符號／檔 | design doc 說 | 當前 code 真相（`file:line`）| 文件怎麼寫 |
|---|---|---|---|
| `{SYMBOL}` | {DOC_CLAIM 或「未提」} | {✅ 存在／❌ 不存在／⚠️ 不一樣：…} | {直接用真實簽名／標（新建）／切一張 Prefactor／列為開放問題 Q#} |

- **驗證指令**：{實跑 build／test 的結果一句話；沒辦法跑就寫「未實跑」}
- **現況形狀**：{iOS：`architecture-auditor` 對整合面模組的結論一句話；沒跑寫「未跑」}

---

## 📅 時程與里程碑

### 目標：{TARGET_TIMELINE_RANGE}（可上 {DEPLOY_TARGET}）

<!-- intake 沒收到時程目標就整段寫「未定」，Stage 只列名稱與產出、不寫 Day 起訖。不要編數字。 -->

> 預估總計 ~{TOTAL_DAYS} 工作天。{IF_LARGE：詳見 [`sprint-roadmap.md`](./sprint-roadmap.md)——中型不產這份，刪掉這句}

{FOR_EACH_STAGE}
#### Stage {N} — {STAGE_NAME}（Day {START}-{END}，{DAYS} 天）
- {STAGE_DELIVERABLE}
- ...
- **產出**：{STAGE_FINAL_OUTPUT}

---

## 🚨 最重要的風險點

| # | 風險 | 影響 | 應對 |
|---|---|---|---|
| **R1** | {RISK_1} | {IMPACT} | {MITIGATION} |
| **R2** | {RISK_2} | {IMPACT} | {MITIGATION} |
| **R3** | {RISK_3} | {IMPACT} | {MITIGATION} |

---

## 🤝 跨團隊協作需求

### 從 Backend 還需要拿到
- {BACKEND_TBD_1}
- {BACKEND_TBD_2}

### 從 PM 還需要對齊
- {PM_TBD_1}
- {PM_TBD_2}

### 從 Design 還需要補
- {DESIGN_TBD_1}
- {DESIGN_TBD_2}

---

## ❓ 開放問題

<!-- 跨 ticket 的未決問題放這裡。大型改放 coordination/open-questions.md，這一段只留一行連結。
會擋 Stage 1–2 ticket 的，Step 3 STOP 時就問使用者；有答案後在這裡標 ✅＋一句答案；Step 5 產 context.md 時再抄進「已決事項」（Step 5 之前 context.md 還不存在）。 -->

| # | 問題 | 擋哪張 ticket／哪條 FR# | 狀態 |
|---|---|---|---|
| Q1 | {QUESTION} | {TICKET_OR_FR} | 待使用者／待 PM／待後端／✅ 已決（見 context.md）|

---

## 📂 想深入了解某一塊？

| 想看什麼 | 讀哪份文件 |
|---|---|
| 開發時的原則與回寫規則 | [`context.md`](./context.md) |
| 所有可拆 issue 的 ticket | [`tickets/README.md`](./tickets/README.md) |
| 給 AI 的 handoff prompt | [`ai-prompts.md`](./ai-prompts.md) |
| 還有哪些未決問題 | 本檔「開放問題」段{IF_LARGE：；大型改看 `coordination/open-questions.md`} |
{IF_LARGE：| 後端 API 協定與對接 | `architecture/<topic>.md` |}
{IF_LARGE：| 執行藍圖與分工策略 | `sprint-roadmap.md` |}

---

## 💡 幾個 meta 提醒

### 1. {KEY_STRATEGY_INSIGHT_1}
{EXPLANATION}

### 2. 向下相容

<!-- 只有 design doc 的 reuse 策略是「新建替代、不動既有」時才留下面兩條；策略不同（例如既有骨架本來就要改）就照 design doc 改寫，不要照抄。 -->
{IF_REDLINE：- 所有新增 ViewModel / Service 都是**新類別**，不改既有類別簽名}
{IF_REDLINE：- 既有功能在這個 feature 下完全不受影響}

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版：{FEATURE_NAME} 全貌 kickoff 文件 |

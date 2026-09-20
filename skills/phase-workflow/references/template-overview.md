---
type: phase-doc
feature: {FEATURE_NAME}
doc: overview
status: active
updated: {TODAY}
---

# {FEATURE_NAME} — 功能總覽

> **給同事的 kickoff 文件**：快速理解這次要做什麼、會動到哪些模組、每個頁面的功能
> **閱讀時間**：10-15 分鐘
> **更深入的文件**：見本檔最後的「想深入了解某一塊？」對照表

> [!IMPORTANT] 核心策略
> {KEY_STRATEGY_ONE_LINER — 例如「所有新頁面一律走『新建 outer view + 複用既有子元件』策略，既有整頁 view 全部不動」}

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
{LIST_WHAT_TO_DO}
- 範例：共享設定頁（成員、人數上限、權限）
- 範例：邀請連結分享 sheet
- 範例：共享中頁
- ...

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

> [!WARNING] 紅線檔（以下既有檔案完全不動）
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

## 📅 時程與里程碑

### 目標：{TARGET_TIMELINE_RANGE}（可上 {DEPLOY_TARGET}）

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

## 📂 想深入了解某一塊？

| 想看什麼 | 讀哪份文件 | 中型有嗎 |
|---|---|---|
| 開發時的原則與回寫規則 | [`context.md`](./context.md) | ✅ |
| 所有可拆 issue 的 ticket | [`tickets/README.md`](./tickets/README.md) | ✅ |
| 給 AI 的 handoff prompt | [`ai-prompts.md`](./ai-prompts.md) | ✅ |
| 後端 API 協定與對接 | `architecture/<topic>.md` | ❌ 大型才有 |
| 執行藍圖與分工策略 | `sprint-roadmap.md` | ❌ 大型才有 |
| 還有哪些未決問題 | `coordination/open-questions.md` | ❌ 大型才有 |

> 中型請把標 ❌ 的列整列刪掉——那幾份檔不會產出（見 phase-workflow SKILL.md 的 Output manifest）。
| 想用 AI 協助開發 | `ai-prompts.md` |

---

## 💡 幾個 meta 提醒

### 1. {KEY_STRATEGY_INSIGHT_1}
{EXPLANATION}

### 2. 向下相容
- 所有新增 ViewModel / Service 都是**新類別**，不改既有類別簽名
- 既有功能在這個 feature 下完全不受影響

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版：{FEATURE_NAME} 全貌 kickoff 文件 |

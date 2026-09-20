---
type: phase-doc
feature: {FEATURE_NAME}
doc: sprint-roadmap
status: active
updated: {TODAY}
---

# Sprint Roadmap — {FEATURE_NAME}

> **目的**：{TARGET_TIMELINE_RANGE} 完成 {FEATURE_NAME}
> **建立日期**：{TODAY}
> **Team**：{TEAM_MEMBERS}
> **核心原則**：**最大化既有系統 reuse**、**foundation 收斂後 ticket 發散**
> **References**：`tickets/`（一 ticket 一檔）/ `overview.md`（§0 架構形狀與模組清單）/ `architecture/<topic>.md`

---

## 0. 目標與限制

### 整體目標

- {TIMELINE_TARGET}（如：3 週內完成可內測版本）
- {EXISTING_SYSTEM_LABEL} 既有功能不能 regression
- 架構乾淨到未來加功能不用大改

### 執行原則

1. **Reuse-first**：能用既有的不重寫
2. **Mock-first**：網路層先用 mock，等 backend 回覆再換真實（如涉及後端）
3. **Foundation-first**：Stage 1 收斂完成再發散其他 stage
4. **Ticket-based 認領**：每張 ticket 0.15-0.5d，卡住可切換

---

## 1. 架構分層圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 5: Features (各自獨立)              │
│  {PAGE_LIST}                                                 │
│  ↓ 依賴 Layer 4                                              │
├─────────────────────────────────────────────────────────────┤
│                    Layer 4: Shared UI Components             │
│  {SHARED_UI_COMPONENTS}                                      │
│  ↓ 依賴 Layer 3                                              │
├─────────────────────────────────────────────────────────────┤
│                    Layer 3: Service Implementations          │
│  {SERVICE_IMPLEMENTATIONS}                                   │
│  ↓ 依賴 Layer 2                                              │
├─────────────────────────────────────────────────────────────┤
│                    Layer 2: Protocols + Models (⭐ 收斂核心) │
│  {MODELS_AND_PROTOCOLS}                                      │
│  ↓ 依賴 Layer 1                                              │
├─────────────────────────────────────────────────────────────┤
│                    Layer 1: {EXISTING_SYSTEM_LABEL} 既有（不動） │
│  {EXISTING_REUSED_MODULES}                                   │
│  {REDLINE_FILES}                                             │
└─────────────────────────────────────────────────────────────┘
```

**關鍵**：Layer 2 是**收斂點**。建完後，Layer 3/4/5 的 ticket 就能**平行獨立開發**。

---

## 2. Stage 規劃

```
Stage 1   Stage 2          Stage 3          Stage 4          Stage 5          Stage 6
Foundation→ Service Core →  Feature Pages → ...           →  Integration + QA
(收斂)      + Quick Wins                                       (收斂)

Day 1-X    Day X-Y          Day Y-Z          ...
All-hands  Pick-your-own    Pick-your-own    ...
```

> **預估** ~{TOTAL_DAYS} 工作天，依 {STAGE_COUNT} stage 分配
> **PR 對照**：每個 Stage 對應的 GitHub PR / branch / commit 詳見 [`coordination/branch-tracker.md`](./coordination/branch-tracker.md)

### Stage 1：Foundation（{DAYS_1} 天，Day {RANGE_1}）

{LIST_FOUNDATION_TASKS}
1. {Model/Protocol task}
2. {Protocol task}
3. {Repository protocols}
4. {Enum / shared types}
5. {Mock service skeleton}
6. {Shared UI 元件骨架}
7. ...

### Stage 2：{STAGE_2_NAME}（{DAYS_2} 天，Day {RANGE_2}）

{LIST_STAGE_2_TASKS}

### Stage 3：{STAGE_3_NAME}（{DAYS_3} 天，Day {RANGE_3}）

{LIST_STAGE_3_TASKS}

{REPEAT_FOR_OTHER_STAGES}

### Stage {N}：Integration + QA（{DAYS_N} 天，Day {RANGE_N}）

1. 串接 nav / coordinator
2. 接真實 backend（如有）
3. {EXISTING_SYSTEM_LABEL} regression test
4. E2E happy path
5. Accessibility baseline + i18n + 送 TestFlight / 出貨

---

## 3. 人力分工建議（skill-based）

### 3.1 團隊背景

- **人力**：{TEAM_MEMBERS}
- **歷史分工**：通常採「**架構 + 服務 vs UI**」兩條線平行
- **既有系統熟手**：critical path 上的 ticket 建議由熟悉既有 code 的人接

### 3.2 三種 skill 推薦（ticket 欄位對應）

| Skill | 適合的 tickets | 能力特徵 |
|---|---|---|
| **UI 擅長** | {ticket_id_pattern_UI} | SwiftUI layout、元件組裝、互動狀態 |
| **架構 / 服務擅長** | {ticket_id_pattern_SERVICE} | Protocol 設計、Codable、Concurrency、網路層 |
| **既有系統熟手** | {ticket_id_pattern_DELTA} + {ticket_id_pattern_INTEGRATION} | 熟既有 view / data model / 紅線檔規則 |

---

## 4. Descope 清單

### ❌ 完全不做（已對齊）

{LIST_DESCOPE_HARD}
- {item_1}
- {item_2}

### ⚠️ 簡化版本

{LIST_DESCOPE_SOFT}
- {item_1 — 原本想做的完整版 → 簡化到什麼程度}

### ✅ 不 descope（照做）

{LIST_MUST_DO}

### Accessibility Baseline 標準

| 動作 | 範例 |
|---|---|
| Icon button 補 `.accessibilityLabel` | `Image("icn_share").accessibilityLabel("分享邀請連結")` |
| 資訊性 icon+數字合併 | `HStack { Image("icn_count"); Text("18") }.accessibilityElement(children: .combine).accessibilityLabel("18 個項目")` |
| 裝飾性 image 隱藏 | `.accessibilityHidden(true)` |
| 關鍵狀態 announce | `UIAccessibility.post(.announcement, argument: "{STATE}")` |

**預估工作量**：每個 view +2-5 行 modifier，總 +0.5 天
**不做**：Dynamic Type / VoiceOver flow polish / 顏色對比度 WCAG

---

## 5. 風險與緩解

| # | 風險 | 影響 | 緩解 |
|---|---|---|---|
| R1 | {RISK_1} | {IMPACT_1} | {MITIGATION_1} |
| R2 | {RISK_2} | {IMPACT_2} | {MITIGATION_2} |
| R3 | {RISK_3} | {IMPACT_3} | {MITIGATION_3} |

---

## 6. Workflow 與 Daily Rituals

### 6.1 AI Coding Workflow 整合

依個人偏好可加 AI 輔助：

#### Stage 1 Foundation
```
每個 task 開始前：
  /writing-plans → 列計畫 → 實作 → /review → /verification-before-completion
```

#### Stage 2+ Ticket（新功能類）
```
新 Page / 新 Service:
  /writing-plans → /test → 實作 → /review → /verification-before-completion

Delta（改既有）:
  /writing-plans → 完整讀既有檔 → 實作 → 手動 regression → /review → /verification-before-completion

Bug fix:
  /ios-investigate（找根因再修）
```

### 6.2 Pair Programming 時機

- **Day 1 早上 2 小時**：全員 pair 對齊 Stage 1 架構 + file layout + naming
- **Integration stage 啟動**：全員 pair 對齊 integration plan
- 卡住時隨時 pair（優先於 skill 呼叫）

### 6.3 每日 Stand-up（15 分鐘）

- 昨天完成什麼 ticket
- 今天要做什麼 ticket
- 卡住什麼（立刻決定是否 switch）
- {EXISTING_SYSTEM_LABEL} 既有 code 改動預告

### 6.4 卡住的處理原則

- **10 分鐘法則**：卡 10 分鐘解不開就標「blocked」切換 ticket
- 不要卡在等 PM / Backend 回覆，直接切 mock path
- Debug 類問題用 `/ios-investigate`

### 6.5 Code Review 策略

- Stage 1：**嚴格 review**（foundation 錯了會連累全部）
- Stage 2+：**快速 review**（各自負責、快節奏）

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版：Sprint Roadmap，依 design doc 切 {STAGE_COUNT} stage |

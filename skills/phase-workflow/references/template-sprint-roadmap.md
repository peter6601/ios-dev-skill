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
> **核心原則**：**最大化既有系統 reuse**、**foundation 收斂後，一條一條行為打通**
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
3. **Foundation-first**：Stage 1 只放 ≥2 條行為共用的契約與骨架，收斂完成再發散
4. **Behavior-sliced**：Stage 2 起每張 ticket 是一條使用者看得到的行為，從 Model 打通到畫面與導航；做完就能實機 demo。不按技術層切（沒有「Service 全做完」這種 ticket）
5. **Ticket-based 認領**：每張 ticket 0.15-0.5d，卡住可切換

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

**關鍵**：Layer 2（契約）是**收斂點**，＝ Foundation ticket。建完後各張 **Behavior ticket** 平行，每張各自穿過 Layer 3–5。
這張圖是**依賴圖**，不是切 ticket 的刀法——不要照 Layer 一層一張地切。
改同一個 Layer 3／4 檔的 Behavior 要用 `deps` 串行（見 `tickets/README.md` 的「不可平行」）。

---

## 2. Stage 規劃

```
Stage 1        Stage 2              Stage 3              ...        Stage N
Foundation  →  行為批次 1         →  行為批次 2         →  ...   →  QA + 出貨
(+Prefactor)   (P1：最短可 demo     (P2 行為)                       (收斂)
(收斂)          的主流程)

Day 1-X        Day X-Y              Day Y-Z              ...
All-hands      Pick-your-own        Pick-your-own        ...
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
6. {共用檔的空骨架——後面各行為只做加法}
7. {Prefactor：先拆既有 View／ViewModel 才加得進去的整理（行為不變，先補快照測試）}

> 只放 **≥2 條行為都依賴**的東西。只有一條行為用到的 Service／元件不放這裡，放進那條行為的 ticket。

**Checkpoint**：契約與骨架 build 得過、mock 可注入；Stage 2 的行為可以平行開工。

### Stage 2：{STAGE_2_NAME}（{DAYS_2} 天，Day {RANGE_2}）

{LIST_STAGE_2_BEHAVIORS：每列一條行為「使用者能……」＋它涵蓋的 FR#}

**Checkpoint**：本批每條行為各自可實機走通（P1 主流程做完＝第一個可 demo 版本）。

### Stage 3：{STAGE_3_NAME}（{DAYS_3} 天，Day {RANGE_3}）

{LIST_STAGE_3_BEHAVIORS}

**Checkpoint**：本批每條行為各自可實機走通。

{REPEAT_FOR_OTHER_STAGES}

### Stage {N}：QA + 出貨（{DAYS_N} 天，Day {RANGE_N}）

1. 接真實 backend（如有；mock → 真實的切換）
2. {EXISTING_SYSTEM_LABEL} regression test
3. E2E happy path（跨行為的完整流程）
4. Accessibility baseline + i18n + 送 TestFlight / 出貨

> 導航**不在這裡才第一次串**——每條行為需要的導航在它自己的 ticket 裡就接好了。這個 Stage 只驗跨行為的整體流程。

---

## 3. 人力分工建議（skill-based）

### 3.1 團隊背景

- **人力**：{TEAM_MEMBERS}
- **分工單位**：一人（或一個 AI session）接**一條行為**，從 Model 做到畫面；不把同一張 ticket 拆給兩個人
- **既有系統熟手**：critical path 上的 ticket 建議由熟悉既有 code 的人接

### 3.2 認領建議（依 ticket 的 type／layers）

| 誰 | 適合的 tickets | 能力特徵 |
|---|---|---|
| **架構 / 服務擅長** | Foundation（{ticket_id_pattern_FOUNDATION}）；layers 以 Service 為主的 Behavior | Protocol 設計、Codable、Concurrency、網路層 |
| **既有系統熟手** | Prefactor（{ticket_id_pattern_PREFACTOR}）；layers 含 Delta、碰紅線檔附近的 Behavior | 熟既有 view / data model / 紅線檔規則 |
| **UI 擅長** | layers 以 UI 為主的 Behavior（{ticket_id_pattern_UI_HEAVY}） | SwiftUI layout、元件組裝、互動狀態 |

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
每張 ticket 用 /ios-dev tickets/<id>.md 接手（情境 7）：
  /writing-plans → 列計畫 → /subagent-driven-development → 閘門與 review 路線 → /verification-before-completion
```

#### Stage 2+ Ticket（Behavior）
```
Behavior（一條行為，依層施工 Model → Service → View → 導航 → 測試）:
  /writing-plans（含 unit test cases）→ /subagent-driven-development → 閘門與 review 路線 → /verification-before-completion → 照 ticket 的 Verification 段實機走一遍

layers 含 Delta（改既有）或 Prefactor:
  /writing-plans → 完整讀既有檔 → 實作 → 手動 regression → 閘門與 review 路線 → /verification-before-completion

Bug fix:
  /ios-investigate（找根因再修）
```

### 6.2 Pair Programming 時機

- **Day 1 早上 2 小時**：全員 pair 對齊 Stage 1 架構 + file layout + naming
- **QA stage 啟動**：全員 pair 對齊跨行為 E2E 與 regression 計畫
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

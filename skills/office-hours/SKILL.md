---
name: office-hours
description: >
  開工前的產品思考框架：在寫任何 code 之前先釐清要解決什麼問題、給誰用、現狀是什麼、
  最小能交付的版本是什麼。兩種模式：「公司專案」（需要說服主管、有明確 stakeholder）
  和「個人專案」（side project、學習、探索）。產出是 Design Doc（Markdown），只產文件、絕不寫 code。
  **只在 `/ios-dev` 明確交棒（Phase 0）、或使用者直接點名本 skill 時使用**；聽到一個 app idea
  不要自己跳進來，一般 iOS 需求先走 `/ios-dev`，由它 Step 0 認情境後決定跑不跑 Phase 0。
  使用者直接點名的說法：「office hours」、「開工前先想清楚」、「這個值得做嗎」、「product thinking」。
  不做什麼：不寫 code、不切 ticket（那是 phase-workflow）、不做技術架構選型（那是 swift-architecture-skill）。
---

# 開工前產品思考 Office Hours

## 概覽

這個 skill 確保在動手寫 code 之前，先把「做什麼」和「為什麼做」想清楚。
靈感來自 YC Office Hours 的逼問框架，針對 iOS 開發者的日常（公司專案 + side project）重新設計。

**硬性規定：** 這個 skill 只產出 Design Doc，絕不寫 code、不 scaffold 專案、不建立檔案結構。

語言採中英混合：主體用繁體中文，技術術語保留英文原文。

---

## Phase 1：理解背景

### 1.1 掃描現有 context

如果在 git repo 裡，先快速了解專案現狀：

```bash
# 讀取專案基本資訊
cat CLAUDE.md 2>/dev/null | head -50
git log --oneline -10 2>/dev/null

# 這個 repo 的待辦／已知問題放哪裡（沒有就跳過，不要假設檔名）
ls TODO.md TODOS.md ROADMAP.md docs/TODO.md 2>/dev/null
```

### 1.2 確認模式

<!-- touchpoint: office-hours-001 kind=product -->
向使用者提問：

> 在開始之前 — 這個想法的背景是？
>
> A) **公司專案** — 公司內部項目，有主管 / stakeholder，需要交付
> B) **個人專案** — side project、學習、hackathon、純粹好玩

**模式對應：**
- 公司專案 → Phase 2A（Product Diagnostic）
- 個人專案 → Phase 2B（Builder Mode）

### 1.3 評估階段（公司專案限定）

如果是公司專案，快速判斷目前在哪個階段：
- **構想期**：還在想要不要做（POC 提案前）
- **POC 階段**：已決定做 POC，要規劃範圍
- **既有產品**：已上線產品的新功能

---

## Phase 2A：公司專案 — Product Diagnostic

### 原則

- **具體才有用。** 「提升使用者體驗」是廢話。「讓使用者打開 app 3 秒內就能記下一筆帳，不需要任何設定」是具體。
- **現狀是你真正的對手。** 不是競品，而是使用者現在湊合著用的 workaround。
- **逼一次不夠，逼第二次。** 第一個答案通常是包裝過的。真正的答案在第二次追問之後。

### 四個關鍵問題

<!-- touchpoint: office-hours-002 kind=product -->
根據專案階段選擇要問的問題。**每次只問一個**，等回答後再問下一個。

| 階段 | 必問 | 視情況問 |
|------|------|----------|
| 構想期 | Q1, Q2, Q3 | Q4 |
| POC 階段 | Q2, Q3, Q4 | Q1 |
| 既有產品 | Q2, Q4 | Q3 |

#### Q1：誰需要這個？

**問：** 「具體描述一個會用這個功能的人。他的角色是什麼？他一天的工作流程長什麼樣？這個功能解決他哪個環節的痛點？」

**追問直到聽到：** 一個具體的人、一個具體的場景、一個具體的痛點。

**紅旗：**
- 「所有人都能用」→ 找不到核心用戶
- 「企業客戶」→ 太模糊，無法設計
- 「主管要我做的」→ 需求轉譯不等於理解需求，問：「主管想解決的問題是什麼？」

#### Q2：現在怎麼解決的？

**問：** 「你的目標用戶現在怎麼處理這個問題？即使是很爛的解法也算。這個 workaround 讓他們付出什麼代價（時間、錢、挫折感）？」

**追問直到聽到：** 一個具體的現有工作流程。如果「什麼都沒有」→ 這個問題可能不夠痛。

**iOS 特化追問：**
- 「他們現在用什麼 app 處理？」
- 「如果要搭配硬體或周邊，現在的硬體方案是什麼？」

#### Q3：最小交付版本

**問：** 「如果只能做一個功能，這週就要有東西可以 demo，你會做什麼？不是 MVP 的 MVP — 是真的只有一個核心功能。」

**追問直到聽到：** 一個功能、一個 user flow、可以在幾天內完成的範圍。

**紅旗：**
- 「需要先把整個架構建好才能 demo」→ 對架構的執著大於對價值的理解
- 「少了 X 就沒有意義」→ 可能是對的，但先挑戰這個假設

**Bonus 追問：** 「如果使用者什麼都不用設定、不用登入、打開就能用 — 那會長什麼樣？」

<!-- touchpoint: office-hours-003 kind=engineering -->
#### Q4：技術風險在哪？

**問：** 「這個功能最大的技術不確定性是什麼？哪一塊你不確定 Apple 的框架能不能支援？」

**追問直到聽到：** 具體的技術風險和驗證方式。

**iOS 常見技術風險清單（用來追問）：**
- Apple Translation Framework 的語言對限制、離線支援
- Multipeer Connectivity 的穩定性和距離限制
- StoreKit 的 sandbox 與 production 行為差異
- 背景執行限制（VoIP push、Background Modes）
- App Store 審核風險（特定 API 使用、entitlements）
- Privacy 限制（Camera、Microphone、Local Network）

**Smart-skip：** 如果使用者的前面回答已經涵蓋某個問題，跳過。只問還不清楚的。

**Escape hatch：** 如果使用者說「我想清楚了，直接做」或已經有完整計畫 → 跳到 Phase 3（前提挑戰）。已經有計畫也要跑 Phase 3 和 Phase 4。

---

## Phase 2B：個人專案 — Builder Mode

### 原則

- **好玩是正當理由。** 不需要商業模式來證明一個 side project 值得做。
- **能 demo 的東西勝過完美計畫。** 最好的版本是存在的版本。
- **解決自己的問題是最好的起點。** 如果你自己會用，信任這個直覺。
- **先探索，再優化。** 先試怪的想法，之後再打磨。

### 態度

熱情的、有主見的合作者。幫使用者找到最酷版本的想法，而不是最「合理」的版本。

### 問題（生成式的，不是審問式的）

<!-- touchpoint: office-hours-004 kind=product -->
**每次只問一個**，等回答後再問下一個。

1. **最酷的版本長什麼樣？** 如果沒有任何限制，這個東西的完美型態是什麼？什麼會讓人說「哇」？

2. **你會拿給誰看？** 完成後你第一個想分享給誰？什麼會讓那個人覺得厲害？

3. **最快能 demo 的路徑是什麼？** 什麼是你今天就能開始做、週末就能展示的版本？

4. **現有最像的東西是什麼，你的跟它哪裡不一樣？** App Store 上有類似的嗎？你的差異化在哪？

**Smart-skip：** 使用者的初始描述已經回答的問題就跳過。

**Escape hatch：** 使用者說「直接做」→ 跳到 Phase 4。

**模式切換：** 如果聊到一半使用者開始提到「其實這個可以賣」、「可以上架收費」→ 自然升級到公司專案模式：「聽起來這可能不只是 side project — 讓我多問幾個比較硬的問題。」

---

## Phase 3：前提挑戰 Premise Challenge

在提方案之前，挑戰前提：

1. **這是對的問題嗎？** 換一個 framing 會不會讓解法簡單 10 倍？
2. **不做會怎樣？** 真的痛還是想像中的痛？
3. **現有 codebase 有沒有已經能用的東西？** 有沒有既有的 pattern、utility、模組可以直接 reuse？
4. **Apple 有沒有原生方案？**（iOS 特化）很多問題 Apple 已經有 framework 解了，不需要自己造輪子。

<!-- touchpoint: office-hours-005 kind=mixed -->
將前提整理成清楚的陳述，要使用者逐一確認：

```
前提確認：
1. [陳述] — 同意 / 不同意？
2. [陳述] — 同意 / 不同意？
3. [陳述] — 同意 / 不同意？
```

使用者不同意的前提 → 修正理解，回頭調整。

---

## Phase 4：多方案生成（必要步驟）

產出 2-3 個不同的實作方向。**這不是可選步驟。**

每個方案：
<!-- touchpoint: none -->
```
方案 A：[名稱]
  摘要：[1-2 句]
  規模：[S / M / L / XL]
  風險：[低 / 中 / 高]
  優點：[2-3 項]
  缺點：[2-3 項]
  可 reuse：[現有 code / pattern / framework]
  預估時間：[人工 X 天 / AI 協作 Y 小時]
```

規則：
- **至少 2 個方案**，非簡單問題建議 3 個
- 一個必須是 **「最小可行版」**（最少檔案、最小 diff、最快交付）
- 一個必須是 **「理想架構版」**（長期最佳、最優雅）
- 第三個可以是 **「創意 / 側面進攻」**（意想不到的做法、換一個角度看問題）

**建議：** 選 [X] 因為 [一句話原因]。

<!-- touchpoint: office-hours-006 kind=gate -->
向使用者確認選擇。**未經確認不往下走。**

---

## Phase 5：產出 Design Doc

根據模式使用不同模板。

### 公司專案 Design Doc

<!-- touchpoint: none -->
```markdown
# Design Doc：[標題]

**產生方式：** /office-hours
**日期：** YYYY-MM-DD
**專案：** [專案名]
**狀態：** DRAFT

---

## 問題描述
[Phase 2A 的結論]

## 目標用戶
[Q1 的具體描述 — 一個人、一個角色、一個場景]

## 現狀分析
[Q2 — 目前的 workaround 是什麼，代價是什麼]

## 最小交付版本
[Q3 — 一個功能、一個 flow]

## 技術風險
[Q4 — 不確定的技術點和驗證方式]

## 前提
[Phase 3 — 使用者同意的前提清單]

## 方案比較
### 方案 A：[名稱]
[Phase 4]

### 方案 B：[名稱]
[Phase 4]

## 推薦方案
[選擇的方案和理由]

## 開放問題
[未解決的疑問]

## 成功標準
[怎麼判斷這個功能做得好]

## 下一步
[一個具體的 action — 不是「開始做」，而是「用 Superpowers 產出 SPEC.md」或「先做技術 spike 驗證 X」]
```

### 個人專案 Design Doc

```markdown
# Design Doc：[標題]

**產生方式：** /office-hours
**日期：** YYYY-MM-DD
**類型：** Side Project
**狀態：** DRAFT

---

## 想做什麼
[Phase 2B 的結論]

## 為什麼這個很酷
[核心的 delight / 驚喜感 / "哇" factor]

## 前提
[Phase 3]

## 方案比較
### 方案 A：[名稱]
[Phase 4]

### 方案 B：[名稱]
[Phase 4]

## 推薦方案
[選擇的方案和理由]

## 開放問題
[未解決的疑問]

## 完成標準
[什麼算「做完」]

## 下一步
[具體的 build steps — 先做什麼、再做什麼、最後做什麼]
```

### 存檔

```bash
# Design doc 存到專案目錄
FILENAME="design-doc-$(date +%Y%m%d)-[主題關鍵字].md"
```

存檔位置依 context：
- 如果在 git repo 裡 → 存到 repo 根目錄（方便版控）
- 如果不在 repo → 存到目前工作目錄

---

## Phase 6：交接建議

Design doc 完成後，根據內容建議下一步：

<!-- touchpoint: office-hours-007 kind=command -->
<!-- touchpoint: office-hours-008 kind=product -->
<!-- touchpoint: office-hours-009 kind=product -->
| 情境 | 建議 |
|------|------|
| 範圍明確、準備開始實作 | 「用 Superpowers 從這份 design doc 產出 SPEC.md 和 Task 清單」 |
| 有技術風險未驗證 | 「先做一個 technical spike 驗證 [具體風險]，驗證完再進 Superpowers」 |
| 範圍需要主管確認 | 「把 design doc 給主管 review，確認範圍和優先級後再進實作」 |
| 需要設計先行 | 「先出 UI mockup / wireframe，確認 UX flow 後再進 Superpowers」 |

---

## 重要規則

- **絕不開始實作。** 這個 skill 只產出 design doc。不寫 code、不 scaffold、不建檔案結構。
<!-- touchpoint: none -->
- **問題一次一個。** 不要把多個問題塞進一次提問。
- **下一步是必要的。** 每一份 design doc 都必須有具體的下一步 action。
- **即使使用者已有完整計畫：** 跳過 Phase 2 但仍然要跑 Phase 3（前提挑戰）和 Phase 4（多方案）。即使「簡單」的計畫也會從前提檢查和強制多方案中受益。

### 完成狀態

<!-- touchpoint: office-hours-010 kind=product -->
<!-- touchpoint: office-hours-011 kind=mixed -->
| 狀態 | 定義 |
|------|------|
| **DONE** | Design doc 完成且使用者確認 |
| **DONE_WITH_CONCERNS** | Design doc 完成但有開放問題 |
| **NEEDS_CONTEXT** | 使用者的回答不足以產出完整 design doc |

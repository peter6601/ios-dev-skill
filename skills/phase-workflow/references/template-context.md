---
type: phase-doc
feature: {FEATURE_NAME}
doc: context
status: active
updated: {TODAY}
---

# {FEATURE_NAME} — AI 行為準則（唯一需要讀的檔案）

> **本檔是 AI 在 {FEATURE_NAME} 開發中唯一需要讀的行為準則檔**。
> Lite Onboarding 時讀一次全文；每次開工做 ticket 時快速 skim 確認沒忘。
> `ai-prompts.md` 是給**使用者**複製 prompt 用的模板庫，AI 自己不需要讀。

---

## 🎯 核心原則（就一條）

**不清楚就問，不要自己推理。**

- 遇到 SPEC / 文件沒寫到的情況 → **stop + ask**
- 可以提供建議、可以列選項，但**不要立刻動手做**
- 有疑問就回報使用者，等確認後再動
- 寫 code 前先確認 scope 邊界

---

## 📋 {FEATURE_NAME} 已決事項

以下是 PM / 使用者 / backend 已經決定的事，做 ticket 時這些是固定的。

### 架構職責

{LIST_ARCHITECTURE_DECISIONS}

範例：
- **衝突合併**：iOS 不合併，後端做。`ListItem.mergedFrom` 留 nil
- **共享 session 生命週期**：iOS **一般不呼叫** DELETE — 僅登出例外
- **共享 session 建立時機**：user 必須手動按「開始共享」才 POST

### 功能範圍（不做）

{LIST_DESCOPE_DECISIONS}

範例：
- 成員暱稱編輯 UI：不做（桌機版功能）
- 留言編輯 UI：不做
- 通知開關 UI：iOS 擁有者端不顯示

### {EXISTING_SYSTEM_LABEL} 既有 code 保護 ⭐

> [!WARNING] 紅線檔 — 絕不修改
> **本 feature 的新頁面全部採用「新建 view + 複用子元件」策略**。整頁 view / 整頁 ViewModel 一律不動。
>
> {LIST_REDLINE_FILES}
> 範例：
> - `ListDetailView` / `ListDetailViewModel`
> - `ListSettingsView`
> - `ListSyncManager`
> - `ListStore`（additive overload 例外 — 純 additive，原 method body 0 改動）
> - ...

- **唯一允許的既有 UI 改動**：
  {LIST_ALLOWED_EXISTING_MODIFICATIONS}
  範例：
  - `ListItemCell.swift` 加 optional `ownerName: String?` / `colorIndex: Int?`（預設 nil，向下相容）

- **新建替代品**：
  | 既有整頁 | 新建替代 |
  |---|---|
  | `{LegacyViewA}` | → `{NewViewA}` |
  | `{LegacyViewB}` | → `{NewViewB}` |

### Backend API 欄位（如涉及）

- 以 `architecture/<topic>.md`（大型才有；主題由 Step 3 決定）或 overview.md 的技術模組清單為準，沒寫到的不加
- {BACKEND_OPEN_ITEMS_SUMMARY}

### i18n

- 文案 PM 統一提供
- 實作時用 `LocalizedString("key", comment: "中文 placeholder")` 佔位，不自己寫英文

---

## 🏗️ 實作原則

### 架構

- **以 `overview.md` 的 §0 架構形狀為準**：pattern、模組邊界、state 與 presentation、async ownership 契約四段，
  由 `swift-architecture-skill` 依決策矩陣選出，這裡不預設任何 pattern（矩陣可能沒有選 MVVM）
- §0 的「本 feature PR checklist」就是 `architecture-auditor` 稽核每張 ticket 的尺
- 與各 skill 的預設風格衝突時，**以 §0／`docs/adr/` 為準**，並在報告裡明講衝突的是哪一條

### 開發流程：先計畫 → 先測試 → 再寫 code

每個 ticket 的實作順序：

```
1. /writing-plans → 列出實作計畫 → 【停下來等使用者確認】
2. /test → 列出 unit test cases → 【停下來等使用者確認】
3. 寫 test（Red）→ 寫 code（Green）→ Refactor
4. /review → /verification-before-completion → commit
```

**⚠️ 關鍵**：步驟 1 和 2 都要**先讓使用者看過才動工**，不要一口氣跑完。

### TDD 範圍

- ✅ **Unit Test**：ViewModel / Service / Repository / Builder / State Machine — 每個 ticket 都出
- ❌ **UI Test**：不寫（XCUITest / ViewInspector 等 UI 層測試不做）
- **純 UI ticket**（只有 View 沒有 VM 邏輯的）：不需要出 test，直接從步驟 1 跳到步驟 3 的寫 code

### UI ticket 特別注意：Figma 先行

實作畫面相關的 ticket 時（type letter `U` 或 `D`）：

- **動手寫 UI 之前**，先提醒使用者：「請提供 Figma 截圖或用 Figma MCP 取得設計稿」
- **不要自己想像 UI 長什麼樣** — 顏色、間距、圓角、字體大小全部以 Figma 為準
- 如果使用者沒給 Figma 參考，**stop + ask**

---

## 🛠️ Skill 使用原則

| Skill | 用否 | 說明 |
|---|---|---|
| `/ios-dev` | ❌ 不跑 | Phase 0-1 已在 SPEC + sprint-roadmap 完成 |
| `/writing-plans` | ✅ 每個 ticket | 實作計畫 |
| `/component` | ✅ 新建 UI 元件時 | type letter `U` ticket |
| `/test` | ✅ Service 層必跑 | UI 可略 |
| `/review` | ✅ 每個 ticket | Code review |
| `/verification-before-completion` | ✅ 每個 ticket | Commit 前驗證 |
| `/ios-investigate` | ✅ 遇 bug 時 | 除錯用 |
| `/ios-critique` / `/simplify` / `/ios-harden` | ✅ Integration 階段 | 品質閘門 |
| `/accessibility` / `/ios-polish` | {ACCESSIBILITY_DECISION} | 視 descope 決定 |
| `/localize` / `/app-store-preflight-skills` | ✅ 出貨前 | Phase 4 |

---

## 📏 讀檔省量原則

做 ticket 時讀檔案的規則：

1. **tickets/<id>.md** → 一個 ticket 一檔，整份讀（本來就短）
2. **overview.md / context.md** → 只讀 ticket Refs 指到的章節，不要整份 read
3. **architecture/<topic>.md**（大型才有）→ 只讀 ticket Refs 指到的 § X.X
4. **{EXISTING_SYSTEM_LABEL} 既有檔案**（Delta ticket）→ 例外：必須整份讀完

> 通用原則：**「搜尋定位 → 讀該段」**，不是 **「讀整份 → 搜尋定位」**。

---

## 🌿 開工前：Branch 健康檢查

### Branch 命名規範

```
{BRANCH_PREFIX}/{STAGE}/{SCOPE}

範例：
  {BRANCH_EXAMPLE_1}
  {BRANCH_EXAMPLE_2}
```

- `stage` = `stage1` ~ `stage{STAGE_COUNT}`
- `scope` = 功能名（用 page / module 名）

### 拿到新 ticket 時先檢查

| 檢查項 | 判斷 | 行為 |
|---|---|---|
| Branch ticket 太多？ | 超過 5-6 個 ticket 或 ~800 行 diff | 建議使用者開新 branch |
| Branch 標題不符？ | 例 `stage1/foundation` 但 ticket 是 stage2 | 建議開新 branch |
| 新 branch 要相依嗎？ | 看 ticket deps 是否在前一個 branch | 是 → fork；否 → fork base |

**不要自己直接開 branch** — 列出建議讓使用者決定。

---

## 📝 完工回寫流程

每個 ticket commit 後必做：

### Step 1：Ticket 跟實際不符時（實作過程中）

發現差異 → **stop + 跟使用者討論** → 使用者決定後：
- 更新 `tickets/<id>.md` 的 Tasks / Files / 說明
- 若影響 overview.md 的技術模組清單或 §0 → 同步更新
- 大型：若影響 `sprint-roadmap.md` / `architecture/<topic>.md` → 同步更新

### Step 2：Commit 後回寫（必做）

**一律**：`tickets/<id>.md` 的 frontmatter `status` 改 `done`、填 `pr`。
**大型另外**：在 [`coordination/branch-tracker.md`](./coordination/branch-tracker.md) 加一列
`| {ticket_id} | {commit_hash} | {一句話說明} |`；中型沒有 `coordination/`，寫進 ticket 檔的「實作筆記」段。

### Step 3：有特殊情況才寫 implementation-log（選做）

大型：在 [`coordination/implementation-log.md`](./coordination/implementation-log.md) 最上方加一筆 entry；
中型：寫進 ticket 檔的「實作筆記」段。內容都一樣：
- 有**選項決策** → 填決策表（問題 / 選項 / 選擇 / 理由）
- 有**Ticket 差異** → 填差異紀錄
- 有**踩到的坑** / 既有系統意外發現 → 填備註
- **完全照 SPEC 順利做完 → 跳過此 step**

---

## 🔧 遇到情況怎麼辦

| 情況 | 怎麼做 |
|---|---|
| Ticket 範圍不清 | stop + 問使用者 |
| API 欄位不在 networking-*.md | stop + 問使用者，不自己補 |
| {EXISTING_SYSTEM_LABEL} view 結構不清 | 先完整讀檔，讀完再評估 |
| 規格跟已決事項衝突 | stop + 問使用者 |
| 想加「為了完整性」的功能 | 很可能 scope 外 → stop + 問 |
| Branch 太多 ticket 或標題不符 | 建議使用者開新 / rename |
| Ticket 跟實際程式碼不符 | stop + 討論 → 更新 ticket + SPEC |
| 實作有多個選項 | 列出選項討論 → 完工記在 implementation-log（中型：ticket 的實作筆記段）|
| Commit 完成 | ticket frontmatter 改 `done`＋填 `pr`（必做）；大型另寫 branch-tracker，有特殊情況再寫 implementation-log |
| 不確定用哪個 ticket template | 查 ai-prompts.md § 9.2 前綴對照表 |

---

## 📚 按需讀索引（拿到 ticket 時才讀）

| 情境 | 讀這份 |
|---|---|
| Service ticket（type `S`）| overview.md 的技術模組清單 + §0 模組邊界；大型另讀 `architecture/<topic>.md` 對應章節 |
| UI ticket（type `U`）| overview.md 的畫面清單 + §0 的 state／presentation 規則 |
| Delta（改既有）ticket（type `D`）| ticket 的 Refs 指到的章節 + **完整讀既有原始檔** |
| Integration ticket（type `I`）| 上下游 ticket 檔 + overview.md §0 的模組邊界表 |

> 這張表只能列 Output manifest 上真的會產出的檔（見 phase-workflow SKILL.md）。

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版：{FEATURE_NAME} AI 行為準則 |

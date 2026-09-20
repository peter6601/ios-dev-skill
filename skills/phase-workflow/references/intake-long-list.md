# Intake Long List — 完整性檢查 + 缺項 prompt

Skill 流程 Step 2 用。

讀完 design doc 後，跑這 8 項 checklist。識別已涵蓋項（標 ✅）+ 缺項（標 ❓），用以下 long list 一次列給使用者補。**不要逐題分批問 — 一次列完讓使用者一次補完**。

---

## 8 項完整性 Checklist

```
從你提供的 design doc，我抽到以下內容。請補 ❓ 的項目：

==== Critical（影響檔案生成）====

✅ Feature 一句話描述: {VALUE}
   （或 ❓ 缺，請補：一句話說明這個 feature 是做什麼用的）

✅ 使用者流程: {VALUE}
   （或 ❓ 缺，請補：使用者從進入 → 操作 → 完成的步驟流程，越具體越好）

✅ 頁面清單:
     新建頁面 ({N} 個): {LIST}
     修改既有頁面 ({N} 處): {LIST}
     共用元件 ({N} 個): {LIST}
   （或 ❓ 缺，請補：總共有幾個新頁面 / 改幾個既有頁面 / 幾個共用元件）

✅ 技術模組清單:
     新增 Service / Repository / Model: {LIST}
     修改既有模組: {LIST}
   （或 ❓ 缺，請補：要新建哪些 Service / Repository / Model）

✅ 規模估計（ticket 數）:
     由上面頁面數 + 模組數推估 — 約 {N} 張 ticket
     分流：{中型 1-8 / 大型 >8}（只決定輸出幾份檔，不決定要不要進本 skill）

==== Secondary（影響規則細節）====

✅ 既有系統 reuse 策略: {VALUE}
   （或 ❓ 缺，請說明：哪些既有 view / service / data model 要複用，哪些不能動）

✅ Descope 清單（不做什麼）:
     - {ITEM_1}
     - {ITEM_2}
   （或 ❓ 缺，請補：至少 3 個明確不做的功能 — 跟 PM 對齊過的）

✅ 風險點（至少 3 個）:
     R1. {RISK_1}
     R2. {RISK_2}
     R3. {RISK_3}
     （R# 是風險編號；需求編號用 FR#，兩者不要混）
   （或 ❓ 缺，請補：3 個最擔心的事 — 例如「{EXISTING_SYSTEM_LABEL} regression」、「Backend P0 延遲」、「個人能量分配」）

✅ 行為清單與優先序（ticket 依這份切，不依技術層切）:
     FR1. {使用者能……}（P1：最短可 demo 的主流程）
     FR2. {使用者能……}（P2）
     FR3. {沒有畫面的需求也列，例「離線時排隊，恢復連線後補送」}
   （或 ❓ 缺，請補：使用者看得到的行為逐條列出＋哪幾條是 P1。
     這份會變成 overview.md「這次要做」的 FR# 編號，之後每條都要有 ticket 接，或標 deferred／不做）

✅ 時程目標: {VALUE}
   （可空：目標日期／可上哪個環境／每個 Stage 大約幾天。沒有就寫「未定」，overview 的時程段照實寫「未定」，不要編數字）

==== Domain（影響 template 選用）====

✅ Domain: iOS（預設）/ macOS / web / 其他 ——先從 repo 推斷，推不出才問
   （iOS 自動套既有系統紅線檔保護規則 + Figma node 規範；架構 pattern 依 §0 選型，不預設 MVVM；其他 domain 跳過 iOS-specific section）

✅ 跨團隊 deps:
     - Backend: {YES/NO} {DESCRIPTION}
     - PM: {YES/NO} {DESCRIPTION}
     - Design: {YES/NO} {DESCRIPTION}
   （影響是否生 architecture/ 跟 coordination/）

==== iOS-only（若 Domain = iOS）====

✅ 紅線檔清單: {LIST}
   （例：ListDetailView, ListSyncManager, ListStore, ...）
   （請補：哪些既有 Swift 檔在本 feature 開發期間絕不動）

✅ 允許的既有 UI 改動: {LIST}
   （例：ListItemCell 加 optional ownerName parameter）

==== Variable for ai-prompts.md（影響變數代入）====

✅ Project name: {VALUE} (例 TodoApp)
✅ Feature folder name: {VALUE} (例 2.0-SharedLists)
✅ Branch 命名規範: {PATTERN} (例 feature/2.0.0/{stage}/{scope})
```

---

## Prompt 範本（給使用者）

skill 列完 checklist 後，跟使用者說：

```
我從你的 design doc 抽到 ✅ 的項目，❓ 的請補。

可以的話一次列完所有 ❓ 答案，我會用來生 overview.md（確認是大型後再補 sprint-roadmap.md）。

如果某項你「目前沒答案，想跟我討論再決定」，標 [TBD] + 你的想法，我會列選項給你選。
```

---

## 規模分流判定

根據 checklist 的「規模估計」項，決定後續輸出：

門檻的唯一真相在 `SKILL.md` 的「規模分流邏輯」：**1–8 中型／>8 大型**。
進不進本 skill 由責任邊界決定（`SKILL.md`「何時用」），**不由 ticket 數決定**——
只有兩張 ticket 的新模組照樣要中型規劃，這裡不得把它退回短 plan。

```python
if estimated_tickets is None or estimated_tickets == 0:
    # 估不出來就回去問頁面數／模組數，不要用「數量少」當作不需要規劃的理由
    ask_again("規模估計")
elif 1 <= estimated_tickets <= 8:
    size = "medium"
    outputs = ["overview.md", "context.md",
               "tickets/README.md", "tickets/<id>.md (每 ticket 一檔)", "tickets/board.base",
               "ai-prompts.md"]
elif estimated_tickets > 8:
    size = "large"
    outputs = ["overview.md", "sprint-roadmap.md", "architecture/", "context.md",
               "tickets/README.md", "tickets/<id>.md (每 ticket 一檔)", "tickets/board.base",
               "coordination/", "ai-prompts.md"]

# 所有 reference 檔加 frontmatter (type: phase-doc)；ticket 檔加 frontmatter (tags: [phase-ticket])
# link 語法保持 relative markdown（GitHub-safe），不用 wikilink
# 關鍵 marker 用 GitHub 標準 callout（[!WARNING]/[!IMPORTANT]/[!NOTE]/[!TIP]/[!CAUTION]）
```

---

## 答案處理

使用者補完答案後：

1. **更新 working state**（在記憶中而非寫檔；唯一的例外是 Step 1.5 的 verified facts 表，Step 3 要寫進 overview.md「現況盤點」段）
2. **跳到 Step 3**：只寫 overview.md（大綱階段；sprint-roadmap.md 等 Step 4 確認是大型才產）
3. **不要立刻寫其餘的檔** — 等 Step 4 規模確認 + 使用者 ack

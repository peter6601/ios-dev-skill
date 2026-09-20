<!-- Template: rd-spec.md（入口 B — RD Spec living doc）
變數化來源：一個 PM-spec 功能的實際 RD spec @ 2026-09-01

使用說明：
- 受眾是 PM / QA / 他平台 RD：語言繁中、白話優先；技術細節給 file:line 但不展開 code。
- 支援兩種情境：**從零**（功能未動工——前提表不填「落地現況」欄、無證據表、全部開完整卡）
  與**盤點式**（已動工——多填落地現況、已完成壓縮成證據表、只有剩餘工作開完整卡）。
- 貼 GitHub issue comment 時去掉 frontmatter（`gh issue comment --body-file`）。
- callout 只用 GitHub 認得的 5 種（WARNING / IMPORTANT / NOTE / TIP / CAUTION）。
- 改版：新 comment 標「vN 取代 vN-1，上一則請刪除或收合」，`<output_root>` 的源檔同步 bump。
-->
---
type: phase-doc
feature: {FEATURE_NAME}
doc: rd-spec
status: draft            # draft → active（已貼 issue 後）
updated: {TODAY}
---

# {PM_SPEC_TITLE} — {PLATFORM} {實作盤點與 |}Sub-issue 拆解（v{N}）

> **v{N}（{TODAY}）{首版 | 取代 v{N-1} comment，上一則請刪除或收合}**。{盤點式加：快照基準：branch `{BRANCH}` @ `{COMMIT}`（分支仍在活動中時註明）。}
>
> - {有他平台拆解時：前提全數繼承 {PEER_ISSUE_REF} comment v{M}（{DATE}）定案：{一行列舉關鍵定案}。}
> - {**T 編號沿用 {PEER_PLATFORM}**（同義工作同號，跨平台對照免翻譯）；本平台特有工作從 T{X} 起編。}
> - 現況一句話：{哪層完成、哪層未完、剩什麼}。

label 體系：`type:spike` / `type:feature` / `type:chore` / `type:risk` + `area:{...}`

---

## 設計稿

| 畫面 | Figma node |
|---|---|
| {SCREEN_NAME} | `{NODE_ID}`（[連結]({FIGMA_URL})） |

> [!NOTE]
> {設計稿缺口與「實作先行」註記；設計稿中不實作的示意元素要點名，防工程照稿做出來}

---

## 前提（定案表{＋本平台落地現況}）

<!-- 每列一個關鍵決策。定案來源：PM spec、他平台拆解、grill 結論。盤點式加第三欄。 -->

| 問題 | 定案 | {本平台落地現況} |
|---|---|---|
| {關鍵問題} | {答案} | {✅ 已依此實作（`file:line`）/ ⚠️ 偏離＋原因 / 🔶 部分 / ⏸ 待決（指向 T 卡）} |

---

## 需求對照（PM spec 條目 → T 卡）

<!-- PM spec 的每個條目一列，給穩定編號 FR#。這張表抓的是「PM spec 有寫、轉成 rd-spec 時掉了」的條目。
任何一列的「T 卡／處置」空著，就不得送 Step 3.5B 審查、也不得貼 issue。 -->

| # | PM spec 條目（章節） | T 卡／處置 |
|---|---|---|
| FR1 | {條目一句話}（PM spec § {X}） | T{n} |
| FR2 | {條目一句話}（PM spec § {X}） | Out of Scope——{原因一行} |
| FR3 | {條目一句話}（PM spec § {X}） | 待 PO（見文末）|

---

## 現況總覽（as-of `{COMMIT}`）

| T | 項目 | 狀態 |
|---|---|---|
| T{n} | {項目} | ✅ done / 🔧 partial / ⬜ not started / ⏸ 待決 / ➖ 他平台認領 |

**關鍵路徑**：{T→T 鏈；標出 release gate 與可並行的支線}

---

## 🧭 §0 架構形狀（iOS／macOS；由 `swift-architecture-skill` 填，`architecture-auditor` 依此稽核每張卡）

> **Pattern 與理由**：{PATTERN_PRIMARY}（分層）＋ {PATTERN_PRESENTATION}（presentation）— {WHY_PATTERN：決策矩陣的 2–3 個因素；既有 codebase 時說明沿用或改動的理由}

**模組邊界**：{每個新增／修改模組一行：誰 own 什麼 state、對外 protocol、注入點}

**State 與 presentation 規則**：**互斥**呈現用一個 `Identifiable` enum＋`.sheet(item:)`（純局部開關保留 Bool）；ViewModel 只暴露狀態、不用 `should*`／`did*` 指揮 View；{SELECTED_PATTERN_STATE_RULES：由所選 pattern 決定，MVI／TCA 才有「單一 `send(Action)`」}；{FEATURE_SPECIFIC_STATE_RULES}

**非同步工作的 ownership 契約**：每一項工作填六格（啟動者與持有者／生命週期／結束與清理／重入策略／舊結果如何失效／isolation 與逾時）。優先 structured concurrency；需要 handle 才存 `Task`，存了就寫清楚誰 cancel、何時 cancel。**不為了符合規則把工作硬搬到 Service，也不要求全部塞進單一 `run()`**。Combine 只在邊界；{FEATURE_SPECIFIC_ASYNC_RULES}

**本 feature 的 PR checklist**（5–8 條）：
1. {CHECK_1}
2. {CHECK_2}
3. {CHECK_3}

## 代號說明

- **M0、M1…** = 階段；**T0、T1…** = 工作卡{（編號對齊 {PEER_ISSUE_REF}，T{X} 起為本平台特有）}
- **Depends on** = 要等誰做完才能開始；**Blocks** = 沒做完會卡住誰
- 開成 sub-issue 後可把 T 編號換成實際 issue 編號（`Depends on #1234`，GitHub 自動建關聯）

---

## M{n} — {階段名}

<!-- 已完成的整批壓縮成證據表，不開卡（盤點式專用）： -->

| T | 完成內容 | 證據與測試 |
|---|---|---|
| T{n} ✅ | {一句話} | `{file:line}`；{測試檔（條數）} |

<!-- 未完成／剩餘的每張開完整卡： -->

### T{n} — {卡名} {🔧|⬜|⏸}

**Labels:** `type:{...}` `area:{...}`

{一段描述：為什麼有這張卡、現況到哪、決策背景}

**Tasks**
- [ ] {task（已完成的打勾保留，呈現進度）}

**Acceptance Criteria**
- {可驗證的完成定義，能指到具體畫面/欄位/指令}

**Depends on:** {T? 或 —} **Blocks:** {T? 或 —}

---

## 本平台特有技術修復（已完成，不開卡）

<!-- 他平台清單上沒有、但本平台踩到的硬仗。每項一行白話（不修會怎樣＋修了什麼），PM/QA 讀得懂。 -->

1. **{名稱}**——{白話風險＋處理方式}（{commit 或 file:line}）。

---

## PR 拆分（卡片對應 PR）

| PR | 內容 | 時機 |
|---|---|---|
| PR-0 | {可先行的獨立風險項，如相容性修復 cherry-pick} | 先行 |
| PR-1 | {主包} | {條件} |
| PR-2+ | {剩餘各卡各 PR} | 各卡完成時 |

---

## Out of Scope

<!-- 繼承他平台定案＋本平台補充；每項附一行原因，防 scope 爬回來 -->

- {不做項}——{原因（一行）}

{發現結構性根因時加：**結構性根因（建議另開 tech debt ticket）**：{描述；本次不做的理由}}

---

## 待 PO／後端決定

<!-- grill 問不出答案的、跨平台不一致要拍板的、後端契約未結案的，全收這裡。標明擋誰。 -->

- **{決策點}**（T{n}）：{選項與影響}——{擋 T?}

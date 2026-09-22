# Phase-Doc Lint 規則

> Karpathy LLM Wiki 的 **Lint** 步驟：定期掃描，找矛盾 / 過時 / 孤兒 / 缺連結。
> phase-workflow 產出的文件用 `type: phase-doc`（reference 檔）+ `tags: [phase-ticket]`（ticket 檔）標記，讓 lint 可挑出來檢查。

## 誰來跑

**`scripts/lint-tickets.py <feature-folder>`**（stdlib，不用裝套件）跑 § A／B／C／F／G／H。
exit 0＝沒有 🔴（🟡 不擋，加 `--strict` 才擋）；exit 1＝有 🔴；exit 2＝路徑不對。`--json` 給程式讀。

腳本**判不了、要自己對**的：
- § H「Behavior 標題並列兩件事」——腳本只看得到「和／及／與／＋、；」，語意要人判；它報了不一定是錯，沒報也不一定沒事
- § H「跨兩個不相依模組」——要對根文件的技術模組清單
- § D 過時／矛盾、§ E 缺失的概念頁

**舊資料夾**（2026-09-20 前切的，`type` 是 Service／UI／Delta／Integration）：腳本自動進 legacy 模式，
只跑 § A 基本欄位與 § B／C，全部降成 🟡，永遠 exit 0。不遷移。

改腳本前先跑 `python3 scripts/test_lint_tickets.py`（fixture 用程式生成——這個資料夾會整個被裝進 Claude 的 skill 目錄，
放 `.md` fixture 可能被當成指令或 skill 文件讀進去）。

---

## 識別 phase-workflow 文件

| 檔類 | frontmatter 標記 | 位置 |
|---|---|---|
| Reference 文件 | `type: phase-doc` | `<output_root>/*.md` |
| Ticket 檔 | `tags: [phase-ticket]` | `<output_root>/tickets/*.md` |

`<output_root>` 是 Step 1 決定的：預設 `<ios-repo>/docs/features/<feature>/`，
使用者明確給 external workspace 時才是 `<workspace>/Projects/<Project>/<feature>/`。

你有自己的文件健檢排程，就讓它呼叫 `scripts/lint-tickets.py --scan <文件根目錄> --json` 一次掃完所有功能資料夾；規則只住在這支腳本，不要另外重寫一份。沒有排程就在 Step 5 產完、Step 6 收尾與 Phase A → B 切換前手動跑（pull 模式：列出問題，使用者批准才修）。

---

## Lint 檢查清單

### A. Ticket frontmatter 完整性
- [ ] 每個 `tags: [phase-ticket]` 檔必有 `ticket` / `stage` / `type` / `status` / `estimate`
- [ ] `status` ∈ {backlog, in-progress, review, done, blocked}
- [ ] `type` ∈ {Foundation, Prefactor, Behavior}；**舊值 {Service, UI, Delta, Integration} 照收**
      （2026-09-20 前產出的功能資料夾不遷移）
- [ ] `type` 是新值的 ticket 另外必有 `layers`（⊆ {Service, UI, Delta, Integration}）、`covers`、`deps`；
      舊值 ticket 沒有這三欄不算錯，§ F／G／H 對它們只跑得動的部分（有 `deps` 才查 G）
- [ ] `type: Behavior` 的 ticket 標題下的 **Demo** 行不得留空或留著 placeholder
- [ ] `done` 狀態的 ticket 必有 `pr` 值（沒 PR 卻標 done = 可疑）

### B. Broken Refs（交叉引用斷鏈）
- [ ] ticket 的 `## Refs` 區塊每個 relative link target 必須存在
- [ ] reference 文件互相引用的 `[text](./x.md)` target 必須存在
- [ ] **每個非外部 link 的 target 都在 SKILL.md 的 Output manifest 上**——連到 manifest 沒有的檔
      （例如 `pages/*.md`、stage／module 彙總檔）就算檔案碰巧存在也是錯，那不是本 skill 的產物
- [ ] **中型不得出現大型專屬檔的連結**（`sprint-roadmap.md`、`architecture/`、`coordination/`）
- [ ] **沒有 wikilink**：全文不得出現 `[[...]]`，產出要在 GitHub render
- [ ] 模板留下的條件標記（`{IF_LARGE：…}`、`{IF_FIGMA：…}`、`{IF_REDLINE：…}` 等所有 `{IF_…}`）全部已處理掉，成品裡不得殘留
- [ ] callout 標記獨佔一行（`> [!NOTE]`）；後面接標題（`> [!NOTE] 標題`）在 GitHub 不會 render
- （這是 Karpathy「缺失的交叉引用」檢查；relative link 斷鏈 = graph 出現孤點）

### C. 孤兒 ticket（orphan）
- [ ] 每個 ticket 檔應被 `tickets/README.md` 連入（inbound link ≥ 1；本 skill 不產 stage 彙總檔）
- [ ] 沒有任何 inbound 的 ticket = 可能漏掉、或該補進 index

### D. 過時 / 矛盾（stale / contradiction）
- [ ] reference 文件的「已決事項」若被後續 supersede，原條目應標 `~~刪除線~~` 或註明 supersession
- [ ] `coordination/open-questions.md` 中標 RESOLVED 卻沒移到 archive 的題目 = 待清
- [ ] reference 文件 frontmatter `updated` 超過 N 天沒動但 ticket 還在 in-progress = 文件可能脫節

### E. 缺失的概念頁（Karpathy「被提到但沒有獨立頁面」）
- [ ] context.md「紅線檔」清單提到的既有檔，若 ticket 大量引用卻無對應說明 → 可考慮補一頁
- （此項偏建議，不強制）

### F. 需求涵蓋（Step 5 產完就跑；沒過不進 Step 6）
- [ ] 根文件（`overview.md`「這次要做」／`rd-spec.md`「需求對照」）每個 `FR#` 至少被一張 ticket 的 `covers` 列到，
      或在 `tickets/README.md` 需求涵蓋表標 `deferred: Stage N`，或已移到根文件的「不做／Out of Scope」
- [ ] ticket 的 `covers` 不得出現根文件沒有的 `FR#`
- [ ] `covers` 為空的 ticket，`type` 必須是 Foundation 或 Prefactor
- [ ] 同一條 `FR#` 被兩張以上 Behavior 的 `covers` 列到 → 🟡 這條 FR 並列了兩件事，回根文件拆成兩條 FR
- [ ] `tickets/README.md` 需求涵蓋表沒有空白列

### G. 依賴（Step 5 產完就跑；沒過不進 Step 6）
- [ ] `deps` 是 YAML list，每一項都對到同資料夾真的存在的 ticket 檔
- [ ] 沒有循環依賴
- [ ] 不得依賴更後面 Stage 的 ticket（禁止前向依賴）

<!-- touchpoint: phase-workflow-052 kind=engineering -->
### H. 同檔重疊與 ticket 大小（🟡 警告，不擋；回報給使用者裁定）
- [ ] 兩張 ticket 的 `## Files` 有同一個標「編輯」的檔，且互不在對方的 `deps` 鏈上 → 「同檔未排序」。
      修法三選一：加 `deps` 串行／合併成一張／在 `tickets/README.md`「不可平行」註明
- [ ] 拆分訊號：production 檔 >5（測試檔不算）、estimate >0.5 人天、Acceptance Criteria >4 條、Behavior 標題並列兩件以上的事
      （看語意：「和／及／與／＋」、頓號、逗號、分號都算；Foundation 不適用這條，只看檔數）、
      跨兩個不相依模組（＝根文件技術模組清單裡彼此沒有依賴的兩個）→ 考慮再拆；使用者可註記理由放行
- [ ] 出現「全部 Service」「所有 Model」這類一整層一張的 ticket → 按層切了，回頭照 SKILL.md「Ticket 切法」重切
- [ ] Foundation 的 `## Files` 裡有**新建**的 production 檔只被**一張** Behavior 引用（其他 ticket 的 Files／Tasks 都沒提到它）→
      「只有一條行為用到的東西進了地基」，移回那張 Behavior。標「編輯」的既有檔不算（那是注入點／composition root）；
      沒有任何 Behavior 引用也不算（整份進地基的型別本來就不再被編輯）
- [ ] Foundation 的 `estimate` 明顯大於 Stage 2 的每一張 Behavior → 檢查是不是把 ＞0.5 人天的型別整份塞進去了

---

## 輸出格式（pull 模式）

產報告列出問題 + 建議修法，**使用者批准後一次批次修**，不自動改。

```
## Phase-Doc Lint — <feature> (<date>)

### 🔴 Broken Refs (N)
- tickets/2-B2.md → Refs 指向 architecture/<topic>.md § 2.5.9（檔案存在但無此 section）

### 🔴 需求沒人接 (N)
- FR4「離線時排隊補送」→ 沒有任何 ticket 的 covers 列到，也沒標 deferred

### 🔴 依賴 (N)
- tickets/2-B1.md → deps 指向 3-B2（前向依賴）

### 🟡 Frontmatter 缺欄 (N)
- tickets/2-B3.md → 缺 estimate

### 🟡 同檔未排序 (N)
- 2-B1、2-B2 都編輯 FavoriteService.swift，互不在對方 deps 鏈上

### 🟡 孤兒 ticket (N)
- tickets/3-B4.md → 未被 tickets/README.md 連入

### 🟢 Stale (N)
- shared-lists-context.md → updated 2026-04-28，但 stage11 ticket 仍 in-progress
```

---

## 觸發方式

| 時機 | 怎麼跑 |
|---|---|
| 定期排程 | 你的文件健檢排程呼叫 `lint-tickets.py --scan <文件根目錄> --json`（有的話）|
| 手動 | `python3 scripts/lint-tickets.py <feature-folder>`，或說「lint 一下 <feature> 文件」|
| Phase A → B 切換前 | 進入修正期前跑一次，確保初版文件無斷鏈 |
| phase-workflow Step 5 產完、Step 6 收尾 | 跑腳本；有 🔴 不進 Step 6、不得收尾 |

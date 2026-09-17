# Phase-Doc Lint 規則

> Karpathy LLM Wiki 的 **Lint** 步驟：定期掃描，找矛盾 / 過時 / 孤兒 / 缺連結。
> phase-workflow 產出的文件用 `type: phase-doc`（reference 檔）+ `tags: [phase-ticket]`（ticket 檔）標記，讓 lint 可挑出來檢查。

---

## 識別 phase-workflow 文件

| 檔類 | frontmatter 標記 | 位置 |
|---|---|---|
| Reference 文件 | `type: phase-doc` | `Projects/<Project>/<feature>/*.md` |
| Ticket 檔 | `tags: [phase-ticket]` | `Projects/<Project>/<feature>/tickets/*.md` |

你有自己的 vault 健檢腳本（定期 `os.walk` 掃全庫那種）就把以下規則加進去；沒有就在 Step 6 收尾與 Phase A → B 切換前，照這份清單手動跑一次（pull 模式：列出問題，使用者批准才修）。

---

## Lint 檢查清單

### A. Ticket frontmatter 完整性
- [ ] 每個 `tags: [phase-ticket]` 檔必有 `ticket` / `stage` / `type` / `status` / `estimate`
- [ ] `status` ∈ {backlog, in-progress, review, done, blocked}
- [ ] `type` ∈ {Service, UI, Delta, Integration}
- [ ] `done` 狀態的 ticket 必有 `pr` 值（沒 PR 卻標 done = 可疑）

### B. Broken Refs（交叉引用斷鏈）
- [ ] ticket 的 `## Refs` 區塊每個 relative link target 必須存在
- [ ] reference 文件互相引用的 `[text](./x.md)` target 必須存在
- （這是 Karpathy「缺失的交叉引用」檢查；relative link 斷鏈 = graph 出現孤點）

### C. 孤兒 ticket（orphan）
- [ ] 每個 ticket 檔應被 `tickets/README.md` 或某 stage index 連入（inbound link ≥ 1）
- [ ] 沒有任何 inbound 的 ticket = 可能漏掉、或該補進 index

### D. 過時 / 矛盾（stale / contradiction）
- [ ] reference 文件的「已決事項」若被後續 supersede，原條目應標 `~~刪除線~~` 或註明 supersession
- [ ] `coordination/open-questions.md` 中標 RESOLVED 卻沒移到 archive 的題目 = 待清
- [ ] reference 文件 frontmatter `updated` 超過 N 天沒動但 ticket 還在 in-progress = 文件可能脫節

### E. 缺失的概念頁（Karpathy「被提到但沒有獨立頁面」）
- [ ] context.md「紅線檔」清單提到的既有檔，若 ticket 大量引用卻無對應說明 → 可考慮補一頁
- （此項偏建議，不強制）

---

## 輸出格式（pull 模式）

產報告列出問題 + 建議修法，**使用者批准後一次批次修**，不自動改。

```
## Phase-Doc Lint — <feature> (<date>)

### 🔴 Broken Refs (N)
- tickets/4-S2.md → Refs 指向 architecture/networking-rest.md § 2.5.9（檔案存在但無此 section）

### 🟡 Frontmatter 缺欄 (N)
- tickets/5-U1.md → 缺 estimate

### 🟡 孤兒 ticket (N)
- tickets/6-I2.md → 未被 tickets/README.md 連入

### 🟢 Stale (N)
- shared-lists-context.md → updated 2026-04-28，但 stage11 ticket 仍 in-progress
```

---

## 觸發方式

| 時機 | 怎麼跑 |
|---|---|
| 定期排程 | 你的 vault 健檢排程自動帶到（若已加上述規則）|
| 手動 | 「跑 phase-doc lint <feature>」或「lint 一下 <feature> 文件」|
| Phase A → B 切換前 | 進入修正期前跑一次，確保初版文件無斷鏈 |

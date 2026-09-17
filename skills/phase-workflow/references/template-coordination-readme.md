---
type: phase-doc
feature: {FEATURE_NAME}
doc: coordination-index
status: active
updated: {TODAY}
---

# Cross-Team Coordination — {FEATURE_NAME}

> 本資料夾收納「跟外部 team 協作」的所有文件

---

## 📂 三份檔案的角色

```
open-questions.md                       ← MASTER 主檔（OPEN/PARTIAL only）
    │
    ├── open-questions-resolved-archive.md  ← Archive（🟢 RESOLVED + 🟡 DEFERRED，按日期倒序）
    ├── backend-requirements.md             ← 過濾「Owner = Backend」+ 加 context 給 backend team
    └── pm-decisions.md                     ← 過濾「Owner = PM」+ 加決策選項給 PM
```

### `open-questions.md` — 內部的 Q 索引（主檔 OPEN-only）
- **讀者**：開發 team
- **目的**：追蹤所有 **🔴 OPEN / 🟡 PARTIAL** 問題的當前狀態
- **何時讀**：寫 code 時遇到不確定的事，先搜 Q 編號

### `backend-requirements.md` — 給 backend team 的需求清單
- **讀者**：Backend team lead
- **目的**：一次彙整所有要 backend 回答的問題 + 已收到的部分 + PM 決策的 context
- **何時用**：寄給 backend 對齊時

### `pm-decisions.md` — 給 PM 的決策清單
- **讀者**：PM
- **目的**：把所有需要 PM 表態的問題集中，每題給 2-4 個選項 + 推薦
- **何時用**：寄給 PM 對齊時

---

## 🔄 同步規則

1. **`open-questions.md` 是 single source of truth**（OPEN/PARTIAL 主檔）
2. PM / Backend 回覆後：
   - 先在 `open-questions.md` 標 🟢 Resolved + 結論
   - 當 OPEN → RESOLVED 時，把該題完整段落移到 `open-questions-resolved-archive.md`（按日期倒序）
3. 再同步更新 `backend-requirements.md` / `pm-decisions.md` 的打勾狀態
4. 若是 P0/P1 級的新決策，順便更新 `../sprint-roadmap.md` 或對應 `pages/*.md`

**順序**：`open-questions.md`（主檔）→ `open-questions-resolved-archive.md`（移檔）→ `backend-requirements.md` / `pm-decisions.md` → `sprint-roadmap.md` / `pages/`

---

## 📊 目前對外未決統計（初版）

| Owner | 剩餘題數 | 最新狀態 |
|---|---:|---|
| **Backend P0** | {N} | {STATUS} |
| **Backend P1** | {N} | {STATUS} |
| **PM** | {N} | {STATUS} |
| **Design** | {N} | {STATUS} |

詳見 [`open-questions.md`](./open-questions.md) 完整統計。

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版 |

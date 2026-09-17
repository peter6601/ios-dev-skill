---
type: phase-doc
feature: {FEATURE_NAME}
doc: tickets-index
status: active
updated: {TODAY}
---

# {FEATURE_NAME} Tickets — 索引

> 本資料夾是 {FEATURE_NAME} 的 **operational 層 tickets**，**一個 ticket = 一個 `.md` 檔**（frontmatter 驅動看板）
>
> **看板**：開 [`board.base`](./board.base) 看 ticket 狀態（依 status 分欄）
> **上層規劃**（Stage / Module / Page 的中層細節）見：[`../sprint-roadmap.md`](../sprint-roadmap.md)
> **最粗略介紹**：[`../overview.md`](../overview.md)

> [!TIP] 看板用法
> 改某 ticket 檔的 frontmatter `status`（backlog → in-progress → review → done）→ `board.base` 看板自動移欄。這是 in-vault 的輕量 dev board。

---

## 📑 Parent 檔案一覽（按 Stage 分類）

### Stage 1 — Foundation

| 檔案 | Parent | Sub 數 | 估計 |
|---|---|---:|---:|
| [`stage-1-foundation.md`](./stage-1-foundation.md) | Foundation — Models / Protocols / 共用元件 | {N} | {DAYS}d |

### Stage 2 — {STAGE_2_NAME}

| 檔案 | Parent | Sub 數 | 估計 |
|---|---|---:|---:|
| [`module-c-{stage2-module}.md`](./module-c-{stage2-module}.md) | Module C — {ROLE} | {N} | {DAYS}d |

{REPEAT_FOR_OTHER_STAGES}

---

## 📊 總量

- **Parent 檔案**：{PARENT_COUNT}
- **Sub-tickets 總數**：{TOTAL_TICKETS}
- **總估計**：~{TOTAL_DAYS} 人天
- **並行度**：{TEAM_SIZE} 人平行約 {PARALLEL_DAYS} 天

---

## 🎯 使用方式

### 1. 建 GitHub Projects 的 parent issue（多人專案）

每份檔案開頭的 `## Parent:` section 是 parent issue 的內容。

### 2. 建每個 sub-issue

每個 `### {ticket_id}` section 直接複製為 GitHub sub-issue 的 body。

### 3. 從 sub-ticket 找相關 SPEC

每個 sub-ticket 的 **Refs** 欄位都列了對應的 `pages/*.md` / `architecture/networking.md` / Q 編號。

### 4. 用 AI 協助開發

見 [`../ai-prompts.md`](../ai-prompts.md) — 包含：
- Full Onboarding prompt
- 4 種 ticket 類型的 handoff prompt 範本（S / U / D / I）
- 核心原則「不清楚就問」

---

## 🧭 Critical Path

{CRITICAL_PATH_DESCRIPTION}

詳見 [`../sprint-roadmap.md § 5 風險`](../sprint-roadmap.md) + [`../{FEATURE_CONTEXT_FILE}.md`](../{FEATURE_CONTEXT_FILE}.md)。

---

## ⏳ Backend 待釐清（如涉及）

| Ticket | 檔案 | 等待 | 狀態 |
|---|---|---|---|

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版 |

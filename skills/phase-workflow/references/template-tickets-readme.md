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
> **最粗略介紹**：[`../overview.md`](../overview.md)
> {IF_LARGE：**上層規劃**（Stage / Module 的中層細節）見 [`../sprint-roadmap.md`](../sprint-roadmap.md)——**中型不產這份檔，這一行整行刪掉**}

> [!TIP]
> **看板用法**：改某 ticket 檔的 frontmatter `status`（backlog → in-progress → review → done）→ `board.base` 看板自動移欄。這是跟文件放在一起的輕量 dev board，不需外部工具。

---

## 📑 Ticket 一覽（一個 ticket 一檔，按 Stage 分組）

### Stage 1 — {STAGE_1_NAME}

| Ticket | 標題 | 類型 | 涵蓋 | 依賴 | 估計 |
|---|---|---|---|---|---:|
| [`{T1_ID}`](./{T1_ID}.md) | {T1_TITLE} | {F/P/B} | {FR# 或 —} | {T1_DEPS 或 —} | {DAYS}d |
| [`{T2_ID}`](./{T2_ID}.md) | {T2_TITLE} | {F/P/B} | {FR# 或 —} | {T2_DEPS 或 —} | {DAYS}d |

### Stage 2 — {STAGE_2_NAME}

| Ticket | 標題 | 類型 | 涵蓋 | 依賴 | 估計 |
|---|---|---|---|---|---:|
| [`{T3_ID}`](./{T3_ID}.md) | {T3_TITLE} | {F/P/B} | {FR# 或 —} | {T3_DEPS 或 —} | {DAYS}d |

{REPEAT_FOR_OTHER_STAGES}

> 每一列的連結都必須對到本資料夾裡真的存在的 `<id>.md`。**不要連到 stage／module 彙總檔**——
> 本 skill 不產那種檔（見 SKILL.md 的 Output manifest）。

> **類型**：F＝Foundation（≥2 條行為共用的契約／骨架）、P＝Prefactor（先整理既有 code，行為不變）、
> B＝Behavior（一條使用者看得到的行為，從 Model 打通到畫面；單獨做完可 demo）。切法見 phase-workflow SKILL.md。

---

## ✅ 需求涵蓋表（根文件每條 FR# 都要有著落）

| 需求 | 一句話 | Ticket | 狀態 |
|---|---|---|---|
| FR1 | {FR1_ONE_LINE} | [`{ID}`](./{ID}.md) | 已切 |
| FR2 | {FR2_ONE_LINE} | — | deferred: Stage {N}（規格收斂後再切）|

> 每條 FR# 只有三種合法狀態：**已切**（至少一張 ticket 的 `covers` 列到它）／**deferred: Stage N**／
> 已移到根文件的「不做」。任何一列空著＝漏需求，不得收尾。

---

## 📊 總量

- **Ticket 總數**：{TOTAL_TICKETS}
- **總估計**：~{TOTAL_DAYS} 人天
- **並行度**：{TEAM_SIZE} 人平行約 {PARALLEL_DAYS} 天
- **不可平行**：{改同一個檔的 ticket 組，例「2-B1 → 2-B2 → 2-B3 都改 FavoriteService，串行」；沒有就寫「無」}

---

## 🎯 使用方式

### 1. 建 GitHub issue

每個 `<id>.md` 的內容直接複製為 GitHub issue 的 body。多人專案要 parent issue 時，
用上面的 Stage 分組表當 parent 的內容。

### 2. 從 ticket 找相關規格

每個 ticket 的 **Refs** 欄位指向 `../overview.md` / `../context.md`
的**章節**（大型另有 `../architecture/<topic>.md` 與 coordination 的 Q 編號）。
Refs 只能指向 Output manifest 上真的存在的檔。

### 3. 用 AI 協助開發

見 [`../ai-prompts.md`](../ai-prompts.md) — 包含：
- Full Onboarding prompt
- Ticket handoff prompt：一份共同骨架＋四個層段落（Service／UI／Delta／Integration），依 ticket 的 `layers` 欄拼
- 核心原則「不清楚就問」

---

## 🧭 Critical Path

{CRITICAL_PATH_DESCRIPTION}

詳見 [`../context.md`](../context.md)（大型另見 [`../sprint-roadmap.md`](../sprint-roadmap.md) § 5 風險；中型把這個括號刪掉）。

---

## ⏳ Backend 待釐清（如涉及）

| Ticket | 檔案 | 等待 | 狀態 |
|---|---|---|---|

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版 |

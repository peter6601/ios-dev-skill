# 填值範例（fill 後必為合法 YAML）：ticket: "4-S1" / stage: 2 / type: Service / estimate: 0.3
# 入口 B（rd-spec）：ticket: "T12" / stage: 3（= M3 的整數）/ type 照常填（S/U/D/I 不進 ID，只當欄位）
---
ticket: "{TICKET_ID}"            # 入口 A 例 "4-S1"；入口 B 例 "T12"（沿 rd-spec T 編號）
title: "{TICKET_TITLE}"
feature: "{FEATURE_NAME}"
stage: {STAGE_INT}               # 例 2（整數，給 board 排序）
type: "{Service|UI|Delta|Integration}"
status: backlog                  # backlog / in-progress / review / done / blocked
estimate: {ESTIMATE_FLOAT}       # 例 0.3
owner:
pr:
deps:
tags:
  - phase-ticket
---

# {TICKET_ID} {TICKET_TITLE}

> **Type**: {Service|UI|Delta|Integration}（→ handoff template ai-prompts.md § 3.{1|2|3|4}）
> **Stage**: {STAGE_NAME}（分組見 [`README.md`](./README.md)）

---

## Refs

- [`../overview.md`](../overview.md) § {SECTION}
- [`../context.md`](../context.md) § {SECTION}
- {IF_LARGE：[`../architecture/<topic>.md`](../architecture/) § {SECTION} 或 coordination 的 Q-number}

> Refs 只能指向 Output manifest 上真的存在的檔的**章節**（見 phase-workflow SKILL.md）。
> 連結一律 relative markdown，不用 wikilink。

## Files

- `{FILE_PATH_1}.swift`（新建 / 編輯）
- `{FILE_PATH_2}.swift`（新建 / 編輯）

## 架構約束（不可違反；收尾時 `architecture-auditor` 拿這一段當尺）

- 所屬模組與責任：{MODULE_AND_RESPONSIBILITY}
- state owner／presentation owner／async owner：{OWNERS}
- 依賴方向與注入點：{DEPENDENCY_AND_INJECTION}
- 非同步工作生命週期：{持有者／生命週期／清理／重入／舊結果失效／isolation；沒有寫「不適用」}
- 不可破壞的不變條件：{導航、取消、錯誤處理、時序}
- 涉及流程時附轉移表：{目前狀態／事件／下一狀態／副作用；沒有寫「不適用」}

- 中途檢查點：{哪一段完整行為走通後、由誰檢查（architecture-auditor／concurrency-auditor／自檢）、對照哪份契約}

> 小 ticket 可逐項標「不適用」，但不要刪掉整段。
> 實作中若必須新增本段沒有的旗標、Task 或跨模組依賴：先判是**實作違約**（→ 修實作、重驗，
> 不准改這一段來遷就程式碼）還是**契約不適用**（→ 寫理由、更新這一段與對應測試再繼續）。
> 這張 ticket 的架構契約**已經在規劃階段定好**：確認它涵蓋得了要做的事就開工，
> 不要因為它「新增了一個模組」而再跑一次規劃（回流條件見 `ios-dev/references/handoff-checklist.md` 的開發前第 0 步）。

## Tasks

- [ ] {task_1}
- [ ] {task_2}
- [ ] Unit test（Service 層必出）

## Acceptance Criteria

- [ ] {acceptance_1}
- [ ] {acceptance_2}

<!-- 純內部重構 / 無 user-visible 行為時，整段改成：
Acceptance Criteria: <skip — 純內部重構，無 user-visible 行為>
-->

## 實作筆記（完工時回寫；沒有就留空，不要刪這一段）

| 日期 | commit | 一句話 |
|---|---|---|
| | | |

- 選項決策／踩坑：

---

> [!NOTE] 完工回寫
> **一定要做**：本檔 frontmatter `status` 改 `done`、填 `pr`（這是看板的資料來源）。
> **大型才有**：commit 後到 [`../coordination/branch-tracker.md`](../coordination/branch-tracker.md) 加一列；
> 有選項決策／踩坑寫 [`../coordination/implementation-log.md`](../coordination/implementation-log.md)。
> **中型沒有 `coordination/`**，那兩條回寫改成寫進本檔最下方的「實作筆記」段。

<!--
frontmatter status 值對照（驅動 board.base 分欄）:
  backlog      未開工
  in-progress  開發中
  review       等實機驗證 / 等 PR review
  done         已 merge
  blocked      卡 backend / 卡 deps
-->

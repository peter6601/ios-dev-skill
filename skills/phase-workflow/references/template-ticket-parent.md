# {STAGE_OR_MODULE_NAME} Tickets

> **備用模板**：預設是「一個 ticket 一個檔」（`template-ticket-single.md`）＋`tickets/README.md` 當索引。
> 只有在不用 `board.base`、需要一份 narrative grouping 檔時才用這份；用了就要把它列進該次的產出清單，
> 否則 `tickets/README.md` 不得連到它。
> 依 [`sprint-roadmap.md § 2`](../sprint-roadmap.md)（大型才有）的中層細節拆出的 operational 層 tickets
> 回到索引：[`README.md`](./README.md)

---

## Parent: [{STAGE_OR_MODULE_NAME}] {PARENT_TITLE}

**Description**：{PARENT_DESCRIPTION}

**{STAGE_OR_MODULE_NAME} Sub-tickets**：
- [ ] {ticket_id_1}: {ticket_title_1}
- [ ] {ticket_id_2}: {ticket_title_2}
- [ ] {ticket_id_3}: {ticket_title_3}

**Total**：~{TOTAL_DAYS}d

---

### `{ticket_id_1}` {ticket_title_1}

**Refs**:
- {REF_LINK_1 — ../overview.md § Y / ../architecture/<topic>.md § Z / coordination 的 Q-number}
- {REF_LINK_2}

**Files**:
- `{FILE_PATH_1}.swift`（新建 / 編輯）
- `{FILE_PATH_2}.swift`（新建 / 編輯）

**Tasks**:
- [ ] {task_1}
- [ ] {task_2}
- [ ] {task_3}
- [ ] Unit test（Service 層必出）

**Acceptance Criteria**:
- [ ] {acceptance_1}
- [ ] {acceptance_2}
- 或標：`<skip — 純內部重構，無 user-visible 行為>`

**估計**: {0.15-0.5}d

---

### `{ticket_id_2}` {ticket_title_2}

**Refs**:
- {REF_LINK}

**Files**:
- {FILE_PATH}

**Tasks**:
- [ ] {task}

**Acceptance Criteria**:
- [ ] {acceptance}

**估計**: {0.15-0.5}d

---

{REPEAT_FOR_OTHER_SUB_TICKETS}

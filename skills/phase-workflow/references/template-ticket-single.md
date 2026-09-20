# ⚠️ 第一個 `---` 之前的這幾行註解是給填模板的人看的，**填完整段刪掉**——frontmatter 的 `---` 必須在檔案第一行，否則 Obsidian／看板讀不到。
# 填值範例（fill 後必為合法 YAML）：ticket: "2-B1" / stage: 2 / type: Behavior / layers: [Service, UI, Integration] / estimate: 0.5
# 入口 B（rd-spec）：ticket: "T12" / stage: 3（= M3 的整數）/ type、layers 照常填（不進 ID）
# 舊值相容：2026-09-20 前的資料夾用 "4-S1" 與 type: Service／UI／Delta／Integration，不遷移，lint 照收
---
ticket: "{TICKET_ID}"            # 入口 A 例 "1-F1"、"2-P1"、"2-B1"；入口 B 例 "T12"（沿 rd-spec T 編號）
title: "{TICKET_TITLE}"          # Behavior 寫成「使用者能……」；Foundation／Prefactor 寫它建好或整理好什麼
feature: "{FEATURE_NAME}"
stage: {STAGE_INT}               # 例 2（整數，給 board 排序）
type: "{Foundation|Prefactor|Behavior}"
layers: {LAYERS_LIST}            # 例 [Service, UI, Integration]；Service／UI／Delta／Integration 中這張穿過的，用來組 handoff prompt（ai-prompts.md § 3）
status: backlog                  # backlog / in-progress / review / done / blocked
estimate: {ESTIMATE_FLOAT}       # 例 0.5
covers: {COVERS_LIST}            # 例 [FR1, FR3]；根文件的需求編號。只有 Foundation／Prefactor 可以是 []
deps: {DEPS_LIST}                # 例 ["1-F1", "2-B1"]；沒有就 []。只放不先 merge 就無法開工的（程式碼依賴、同檔排序）；demo 前置寫在 Demo 行
owner:
pr:
tags:
  - phase-ticket
---

# {TICKET_ID} {TICKET_TITLE}

> **Type**: {Foundation|Prefactor|Behavior}｜**Layers**: {穿過的層}（→ handoff prompt＝ai-prompts.md § 3.0 骨架＋對應的層段落）
> **Stage**: {STAGE_NAME}（分組見 [`README.md`](./README.md)）
> **Demo**: {Behavior 必填：這張單獨做完，從哪個入口進去、做什麼、會看到什麼。只是 demo 時需要別張先 merge（要有資料才看得到）就寫在這一行「需 2-B1 已 merge，或用 debug seed」，不要塞進 `deps`。寫不出來先分清楚原因——是切法問題（這張不是完整行為）就回頭重切；是根文件缺資訊（例：入口還沒定）就 stop＋問使用者，不要硬寫。Foundation／Prefactor 寫「不適用——{哪幾張 Behavior 靠它}」}

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

> 「編輯」的檔如果也出現在別張 ticket 的 Files，兩張必須在同一條 `deps` 鏈上（串行），否則平行 session 會撞車。

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
> 不要因為它「新增了一個模組」而再跑一次規劃（回流條件見 `/ios-dev` skill 的 handoff-checklist「開發前第 0 步」）。

## Tasks（依層施工：Model → Service → View → 導航 → 測試；這張沒穿過的層就略過）

- [ ] {task_1}
- [ ] {task_2}
- [ ] Unit test（穿過 Service 層必出）

## Acceptance Criteria（什麼算做對）

- [ ] {acceptance_1}
- [ ] {acceptance_2}

<!-- 純內部重構 / 無 user-visible 行為時，整段改成：
Acceptance Criteria: <skip — 純內部重構，無 user-visible 行為>
-->

## Verification（跑什麼看得到做對了）

- [ ] 測試：`{TEST_COMMAND} -only-testing:{TEST_TARGET}/{TEST_CLASS}`
- [ ] Build：`{BUILD_COMMAND}`
- [ ] 實機／模擬器走一遍：{從哪個入口 → 做什麼 → 應該看到什麼}

<!-- 指令來源＝context.md 的「驗證指令」小節（Step 1.5 grounding 盤出來的真實 scheme／test target），不要自己發明。
Foundation／Prefactor 沒有畫面時，第三條改成 <skip — 無 UI>；測試那條不可跳。
Foundation 裡整份實作的型別（SKILL.md「Foundation 放多少」第 3 題），它的單元測試就在這一張，不留給後面的 Behavior。 -->

## 實作筆記（完工時回寫；沒有就留空，不要刪這一段）

| 日期 | commit | 一句話 |
|---|---|---|
| | | |

- 選項決策／踩坑：

---

> [!NOTE]
> **完工回寫**
> **一定要做**：本檔 frontmatter `status` 改 `done`、填 `pr`（這是看板的資料來源）；commit 與選項決策／踩坑寫進上面的「實作筆記」段。
> {IF_LARGE：**大型另外**：commit 後到 [`../coordination/branch-tracker.md`](../coordination/branch-tracker.md) 加一列；有選項決策／踩坑寫 [`../coordination/implementation-log.md`](../coordination/implementation-log.md)。}

<!--
frontmatter status 值對照（驅動 board.base 分欄）:
  backlog      未開工
  in-progress  開發中
  review       等實機驗證 / 等 PR review
  done         已 merge
  blocked      卡 backend / 卡 deps

拆分訊號（命中任一條就考慮再拆；Step 4／5 回報給使用者，可註記理由放行）:
  - Files 的 production 檔 >5（測試檔不算）
  - estimate >0.5 人天
  - Acceptance Criteria >4 條
  - Behavior 的標題並列兩件以上的事——不論用「和／及／與／＋」還是頓號、逗號、分號（看語意，不是比對字元；
    Foundation 本來就是幾件共用物並列，這條不適用，它只看檔數）
  - 跨兩個不相依的模組（＝overview.md 技術模組清單裡，彼此沒有依賴關係的兩個模組）
-->

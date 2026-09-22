# Handoff Checklist — 交棒後的收尾

> `/ios-dev` 把情境 3–7 交棒給下游 skill 後**不再介入執行，但仍持有這份清單**。
> 情境 1、2 不在這裡——它們留在 `/ios-dev` Step 1–8，流程本身就是清單。

> [!IMPORTANT]
> **交棒 payload ＝三段固定拼接，缺一不可**：
>
> 1. 下面「開發前」**整段原樣**
> 2. 下面「共通收尾」**整段原樣**
> 3. 該情境那一段（§3–§7 擇一）原樣
>
> <!-- touchpoint: none -->
> 情境段裡的「收尾走輕」「風險三條＋規模兩條定輕重」「重時派 5 個 agent」都是**指回前兩段的簡寫**，
> 單獨貼過去下游讀不到輕重怎麼判、三條 review 路線是什麼、人工核准前不得做什麼、回寫寫哪三個地方。
> 下游是獨立 context，它看不到這個檔——**沒貼到的規則等於不存在**。
> 驗收方式：把交棒訊息貼進一個空白 session，它要答得出何時回流 `phase-workflow`、如何重判輕重、
> 三條 review 路線、人工核准前的禁止事項、回寫順序。答不出來就是漏了段。

## 開發前（每個情境都先跑，篇幅隨規模）

**第 0 步：這件事的架構契約已經有人寫過了嗎？**

- **有**（情境 7 接 ticket，或手上的計畫已含架構約束段）→ **不要回流重新規劃**。
  讀根文件對應段與 ticket 的架構約束，確認它涵蓋這次要做的事（owner、注入點、async 生命週期、
  不變條件都在），**確認完就實作**。phase-workflow 切出來的「建立模組」ticket 當然命中
  「新增獨立模組」那條觸發——那正是它被規劃出來的原因，不是再規劃一次的理由。
  只有三種情況回流：**①要新增根文件沒有的邊界 ②契約有缺漏**（該有的格子空著，或與現況矛盾）
  **③範圍漂移**（做下去發現得動到這張 ticket 以外的責任區）。回流時只帶缺的那幾格回去補，
  不重跑整套規劃。
- **沒有**（情境 2–6 直接進來的新工作）→ 往下跑 1–4。

1. 照 `architecture-impact-check.md` 答五問，結論三選一：**直接擴充／局部整理／模組邊界**。
   <!-- touchpoint: ios-dev-033 kind=command -->
2. 命中中型觸發條件（新模組／多畫面流程／多 async 協調／要先拆 View 才加得進去）→ **停下來交
   `phase-workflow` 中型**，不要直接開工；與 ticket 數無關。
3. 有新的非同步工作 → 填 ownership 契約六格；涉及流程 → 產一張 presentation 轉移表。
4. 結論寫進 plan／ticket 的「架構約束」段（`plan-template.md`），那是收尾時 `architecture-auditor`
   的尺。

<!-- touchpoint: ios-dev-034 kind=engineering -->
**實作中**若必須新增計畫沒有的流程旗標、Task 或跨模組依賴，停下來先判是哪一種：

- **實作違反了既有契約**（契約是對的）→ **修實作**、重跑驗證。**不准改契約來遷就程式碼**——
  那等於讓檢查失效。
- **契約確實不適用**（當初判斷錯、或需求變了）→ 寫下理由、重跑五問、更新契約**與對應的測試**，
  再繼續。

<!-- touchpoint: ios-dev-035 kind=engineering -->
判不出來是哪一種就停下來問人，不要預設走第二條。

## 共通收尾（每個情境都跑，順序固定）

1. **定輕重**：照 `skill-router.md` §3——**風險三條**（concurrency／持久化／網路協定／
   migration、公開契約、這次改動寫得出可重現的測試（本次補上即可）——情境 3 純呈現畫面以「Preview 或截圖可前後對照」代替測試）所有情境都適用，踩到就是重；**規模兩條**（範圍單一、
   diff ≤50 行）只用在情境 4 與情境 7。
   **實作完成後再判一次**：所有情境重判風險三條；**情境 4 與情境 7 另外重判規模兩條**
   （原估 30 行最後寫成 100 行，就不再是輕）。實作中才碰到的一樣從輕升重。
2. **跑閘門**（做多少工）：
   輕＝該情境的單一 auditor → `ios-review`（fix-first）。
   重＝先派閘門 agent ＋ `review-swarm` → 主 session 一次統一修復 → `/ios-polish` → verification。

3. **選 review 路線**（誰當第二雙眼睛）：照 `skill-router.md` §3 的三選一，**預設 B**。A 只在使用者於 Step 0 確認畫面選了
   「加 Codex 審核」、或複雜 Bugfix（強制）時走。
   - **A 共識**（使用者選了加 Codex，或複雜 Bugfix 強制）：複雜 Bugfix 只有在 Codex 不可用＝`ai-review` 回 529、額度用完，或 context 過大導致輸出退化
     時才降 B，降級要寫進 PR 描述。**最後**派三個 specialist 各回一段 fenced JSON → `/consensus-review --profile ios --preflight`
     （Codex 首輪 → 合併 → 單一 Claude 統一修復 → re-review，中途不停）。
     `--preflight` 對 `--profile ios` **必填**，且只認 `swiftui`／`ux`／`resilience` 三個 category——
     `ios-review`、`perf-auditor`、`concurrency-auditor`、`architecture-auditor`、`review-swarm`
     的 findings 一律在 `init` 前就修掉，餵進去會被拒、連 run 都不會建立。
   - **B 純 agent**：三個 specialist 唯讀跑完 → 主 session 一次統一修復 → `/ios-polish` →
     `/verification-before-completion`。不呼叫 `ai-review`。
   - **C 輕量**：`ios-review` 的兩輪就是全部。門檻：範圍單一、production diff ≤50 行，**而且**風險三條全綠。
     趕時間不是理由、使用者要求也不能放寬；不符合就走 B，不要另開「你堅持就走 C」的選項。
     實作完成後跟輕重一起重判，超過就從 C 升 B。
   B、C 要在 PR 描述註明「未經 Codex 交叉驗證」。
   <!-- touchpoint: ios-dev-036 kind=code-review -->
   <!-- touchpoint: ios-dev-037 kind=gate -->
   <!-- touchpoint: ios-dev-038 kind=gate -->
4. **人工 Code Review**：三條路線都要，不可省。
   走 A 停在 `AWAITING_HUMAN_CODE_REVIEW`，**人工 `approve-code` 前不得 commit、push、
   merge 或建立 PR**；走 B、C 沒有 run、也沒有 `approve-code` 這道指令，改成使用者讀完
   diff 口頭確認，確認前一樣不得 commit、push、merge 或建立 PR。
5. **回寫**（有才寫，沒有就跳過，不要為此建檔）：
   ticket 的 `status` → 功能資料夾的 `coordination/implementation-log.md` →
   第二大腦該功能 MOC 的「近期變更與教訓」。
   <!-- touchpoint: ios-dev-039 kind=engineering -->
6. **收工**：問使用者要不要跑 Phase 5 `/work-log-writer`。

## §3 純呈現畫面

- 只動版面、樣式、動畫時才是這一段；開發前只要答五問的第 3 問。
- 先跑 `ux-critique` 與 `architecture-auditor`，findings 併入 `ios-polish` 那一次修復。
- 收尾走輕。純呈現不派 `concurrency-auditor`。
- 改動很小（範圍單一、production diff ≤50 行）時 review 走 C；純視覺調整沒有自動化測試可寫，
  風險第三條以「Preview 或截圖可前後對照」算數。超過規模走預設的 B。
- **一旦碰到驗證、持久化、連線、ViewModel 狀態、導航或 async**：它不是純呈現——回 `/ios-dev`
  當小功能或中功能重認，並補 presentation 轉移表。

## §4 修正（bug／issue／維護期）

- `/ios-investigate` 找到 root cause 才修；root cause 未知或高風險 → 回 `/ios-dev` Step 1 的
  「複雜 Bugfix」路徑（repair plan → `/consensus-plan` → 修 → `/consensus-review`，強制走 A；
  Codex 不可用＝`ai-review` 回 529、額度用完，或 context 過大導致輸出退化時才降 B，PR 描述註明降級）。
- crash／regression／flaky 在假設階段起 `bug-hunt-swarm`。
- 風險三條＋規模兩條定輕重（§3）；重時派 5 個 agent（裁掉 `ux-critique`）。
- 修完回寫：issue／ticket 狀態、第二大腦「近期變更與教訓」（這是維護期最容易漏的一步）。

## §5 優化

- **改前沒有 `perf-auditor` 報告或 trace 數字就不動 code**；有疑慮先 `trace-analyzer` 錄 trace 取證。
- 改後用同一把尺再量一次，改前改後數字都寫進 PR 描述。
- 收尾走重；單畫面範圍可降輕。

## §6 重構

- 照 `architecture-impact-check.md` 的「既有功能的架構重構路徑」：先出四項產出（責任地圖／
  狀態與工作清單／行為不變條件＋補測試／目標邊界與遷移順序），再動手。
- `architecture-auditor` 出基線 → `swift-architecture-skill` Deep Refactor Mode 定目標形狀（記 ADR）
  → **沿完整行為切分逐段改**（不按檔案逐一搬移；>3 檔問是否 `orchestrate-batch-refactor`）
  → 每段完成就清掉被取代的狀態、訂閱與呼叫路徑 → 測試前後都綠 → `architecture-auditor` 對比。
- 目標範圍沒有測試覆蓋 → 先用 SDD 補行為快照測試再動。
- 涉及多個 state owner、presentation 流程或 async 生命週期 → 走 `phase-workflow` 的重構規劃模式。
- **本次範圍內可以自由新增／拆分／搬移檔案與型別**，不必逐檔問（見 reference 的「允許新增檔案」）。
- 收尾走重；純畫面重構省 `concurrency-auditor`。

<!-- touchpoint: ios-dev-040 kind=command -->
## §7 接 ticket（`/ios-dev tickets/<T>.md`，每張一個新 session）

這是最高頻的路徑，完整流程在這裡，不在 SKILL.md：

1. **讀四份**：ticket 本身 → 根文件（`overview.md`／`rd-spec.md`）對應段落 → repo 的
   `CONTEXT.md`／`docs/adr/` → `coordination/implementation-log.md` 近期段落。
2. **認內容軸**：從 ticket 的檔案清單推斷（router §4），決定載入 `swiftui-specialist`＋
   `swiftui-ui-patterns`（畫面）或 `swift-concurrency`（功能）。
3. **`/writing-plans` 只為這一張**——不跑 `/consensus-plan`，根文件已經審過了。
4. **`/subagent-driven-development`** 執行，架構層以根文件 §0 架構形狀與 feature PR checklist 為準。
   ticket 的架構契約在規劃階段就定好了——**確認涵蓋得了就開工，不要重跑規劃**（見開發前第 0 步）。
   照 ticket 的「中途檢查點」在那一段行為走通時就先驗一次契約，不要全部寫完才檢查。
5. **共通收尾 1–5**。跑 verification 時**先照 ticket 的 Verification 段**（測試指令、build、實機走一遍）；
   舊 ticket 沒有這一段就照 Acceptance Criteria 自己列驗證步驟。回寫時 ticket 的 `covers` 列到的 FR# 不用另外處理，看板靠 `status`。
   <!-- touchpoint: ios-dev-041 kind=command -->
6. **問「接下一張？」**；全部 ticket 完成時提醒 Phase 5 `/work-log-writer` 與 Phase 6 `/second-brain`。

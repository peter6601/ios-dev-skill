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

**先判診斷階段**：情境 4 的 root cause 未確認時，先由 `/ios-investigate` 取證；架構結論寫「待 root cause 確認」，只列假設、驗證方法與診斷問題。確認根因後才執行下面第 0 步與 1–4，決定修法、寫入路徑與 async 契約。

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

**測試的硬規則**（實作全程適用；改到 `*Tests.swift` 時 `/ios-dev` 的 hook 也會再提醒一次）：

- **不得為了讓測試通過**而修改既有斷言、刪測試、skip 測試（`.disabled`、`XCTSkip`、註解掉）或降低門檻（放寬容差、加長 timeout、調低覆蓋率要求）。
- 確實要改時，回報寫明**是哪條 AC 變了**（AC 編號、舊→新、誰決定的）。寫不出是哪條 AC 變了，就是在改測試遷就程式碼——回去修實作。
- 新寫的 test case 標明「依規格」（對得到某條 AC）或「鎖現況」。**只有重構的行為快照可以鎖現況**，用 `characterization_` 前綴或註解標記；修正、新功能照現況寫等於把 bug 鎖成規格。
- 挑 case 先列條件，再用等價分割與決策表挑代表；碰到錢、授權、持久化或最近出過錯的地方多測；至少一個組合／順序／同時的互動案例。
- **停損**：同一個 Task（或同一個修正點）驗證失敗 3 輪就停，記進完成回報的「刻意沒處理」，往主線走；計畫的前置條件另訂了 N 就照 N。

## 共通收尾（每個情境都跑，順序固定）

1. **定輕重**：照 `skill-router.md` §3——**風險三條**（concurrency／持久化／網路協定／
   migration、公開契約、這次改動寫得出可重現的測試（本次補上即可）——情境 3 純呈現畫面以「Preview 或截圖可前後對照」代替測試）所有情境都適用，踩到就是重；**規模兩條**（範圍單一、
   diff ≤50 行）只用在情境 4 與情境 7。
   **實作完成後再判一次**：所有情境重判風險三條；**情境 4 與情境 7 另外重判規模兩條**
   （原估 30 行最後寫成 100 行，就不再是輕）。實作中才碰到的一樣從輕升重。
2. **跑閘門**（做多少工）：
   輕＝該情境的單一 auditor → `ios-review`（fix-first）。
   重＝先派閘門 agent ＋ `review-swarm` → 主 session 一次統一修復 → `/ios-polish` → verification。
   **diff 動到測試檔就加派 `test-auditor`（唯讀），輕重都派**：輕時跟該情境的 auditor 一起跑、findings 併入
   `ios-review` 前修掉；重時跟閘門 agent 同一批發出、併入統一修復。
   **變異測試（只在踩到風險三條時做）**：統一修復之後、`/ios-polish` 之前，派一個**可寫的** subagent
   在**獨立 git worktree** 裡把 1–3 個關鍵判斷改反（`>=` 改 `>`、授權檢查回 `true`、
   寫入前的驗證拿掉），跑對應測試，確認會變紅。worktree 從目前 HEAD 開，再套上本次未 commit 的 diff
   （`git diff HEAD --binary` 套進去，新檔另外複製）；**不要用 `git stash`**——stash 跟其他 worktree 共用，
   會撿到別人的變更。改反的 code 只活在那個 worktree，跑完就刪。沒變紅＝測試抓不到這個判斷，
   補測試（只加測試、不動 production code）後重跑。每個改反點的結果寫進完成回報。

3. **選 review 路線**（誰當第二雙眼睛）：照 `skill-router.md` §3 的三選一，**預設 B**。A 只在使用者於 Step 0 確認畫面選了
   「加 Codex 審核」、或複雜 Bugfix（強制）時走。
   - **A 共識**（使用者選了加 Codex，或複雜 Bugfix 強制）：複雜 Bugfix 只有在 Codex 不可用＝`ai-review` 回 529、額度用完，或 context 過大導致輸出退化
     時才降 B，降級要寫進 PR 描述。**最後**派三個 specialist 各回一段 fenced JSON → `/consensus-review --profile ios --preflight`
     （Codex 首輪 → 合併 → 單一 Claude 統一修復 → re-review，中途不停）。
     `--preflight` 對 `--profile ios` **必填**，且只認 `swiftui`／`ux`／`resilience` 三個 category——
     `ios-review`、`perf-auditor`、`concurrency-auditor`、`architecture-auditor`、`test-auditor`、`review-swarm`
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
4. **人工 Code Review**：三條路線都要，不可省。請使用者審之前先交下面的**完成回報**。
   走 A 停在 `AWAITING_HUMAN_CODE_REVIEW`，**人工 `approve-code` 前不得 commit、push、
   merge 或建立 PR**；走 B、C 沒有 run、也沒有 `approve-code` 這道指令，改成使用者讀完
   diff 口頭確認，確認前一樣不得 commit、push、merge 或建立 PR。
   **三條路線都要留裁決紀錄，寫在 PR 描述**（PR 模板是給非工程師讀的 repo，放進末尾的
   `<details>` 折疊段）：人確認前，Claude 依這輪 findings 列出逐條裁決草稿——
   `採納（已修）／駁回／延後＋一句理由`——使用者只改錯的；確認後加上一行總結：
   `人工 Code Review：通過（YYYY-MM-DD）｜路線 A/B/C`。A 路線的草稿從 run 的 summary 取。
   沒有 PR 的 repo 寫進 implementation-log。**沒寫裁決紀錄，review 不算完成**——
   簽章或口頭「OK」只證明人看過，裁決紀錄才說得出人判了什麼。
5. **回寫**（有才寫，沒有就跳過，不要為此建檔）：
   ticket 的 `status` → 功能資料夾的 `coordination/implementation-log.md` →
   第二大腦該功能 MOC 的「近期變更與教訓」。
   <!-- touchpoint: ios-dev-039 kind=engineering -->
6. **收尾卡**（每次都寫，一行）：追加到你選定的 plan 效益紀錄表（例如 iOS repo 的 docs/plan-log.md；
   你另外有跨 repo 的 workspace 時放在那裡，一份記所有專案）——
   `日期｜專案｜情境｜有無 plan｜review 路線｜未解決錯誤數｜交付物與位置`。
   「有無 plan」＝這次動 code 前有沒有 plan 檔／plan mode／前一兩個 session 寫好的 plan；
   「未解決錯誤數」＝收工時還沒過的 test＋還開著的 finding＋已知沒修的問題，加總成一個數字；
   「交付物與位置」＝PR 連結、分支、上線 URL 或檔案路徑。這張表用來比「先寫 plan 到底有沒有少出錯」，
   只拿同一情境比，不要跨情境比。
   <!-- touchpoint: ios-dev-064 kind=command -->
7. **收工**：問使用者要不要跑 Phase 5 `/work-log-writer`。

### 完成回報（宣稱完成時交這一份，人工 Code Review 讀它）

每條 AC 一行，證據強度四選一，不要寫「應該沒問題」：

```
## 完成回報：<功能／ticket>

### AC 對照
- AC1 <一句話> → <證據位置：測試名稱／檔案:行／截圖路徑／指令輸出> → 已實測｜已讀取｜推論｜未查
- AC2 …

### 變異測試（踩到風險三條才有；沒做寫「未踩風險三條，不做」）
- <檔案:函式> 改反 <哪個判斷> → <哪個測試變紅｜沒變紅，已補 <測試名稱>>

### 測試改動
- 改了既有斷言／刪除／skip 的測試：<無｜測試名稱 → 變了的 AC（舊→新，誰決定）>

### 刻意沒處理
- <問題> → <為什麼現在不處理：停損、超出範圍、等 PO…> → <記在哪：issue／ticket／implementation-log>
```

- **已實測**＝這次跑過且看到結果；**已讀取**＝讀了 code 或文件確認，沒跑；**推論**＝從別處推得，沒直接看；**未查**＝沒碰。
- 「刻意沒處理」沒有就寫「無」，不要整段刪掉——停損觸發、範圍外的 bug、延後的 finding 都進這裡。

## 非同步審核模式（可選；Step 0 確認畫面選項 4）

<!-- touchpoint: ios-dev-065 kind=code-review -->
AI 做完一個功能、自我審查完就排隊等人審，接著做下一個；人有空再審。全在本地。

**能進這個模式的條件**（任一不符就走一般收尾）：
- review 路線是 A（`consensus-review --auto`）——B、C 沒有 run，沒有東西能停著等。
- 這個功能不依賴任何還沒審過的分支；phase-workflow 有 `deps` 的 ticket，deps 全部 merge 了才行。
- `ai-review queue --format json` 的 `pending_count` < 3。滿了就停手，告訴使用者「待審已滿，先審一個」。

**流程**：
1. 從 base 開 **獨立 git worktree**（`superpowers:using-git-worktrees`）——`approve-code` 會重抓 patch，
   同一個資料夾一改，前一個功能的核准就作廢。新功能一律從 base 開，不疊在沒審過的分支上。
2. 在 worktree 裡照一般流程實作與跑閘門，然後三個 specialist → `ai-review init review --preflight`
   → `approve-review --auto` → `run`（背景）→ 停在 `AWAITING_HUMAN_CODE_REVIEW`。
3. 依 run 的 summary 寫好**逐條裁決草稿**（共通收尾第 4 步的格式），放在 run 資料夾 summary 旁邊，
   **不能放進 worktree**（放進去等於改了 patch）。
4. 寫收尾卡，交付物欄填 worktree 路徑與 run ID，狀態註「待審」。
5. 回到第 1 步做下一個（仍受上限 3 個約束）。**已停著的 run 不再 `resume` 或修改**；
   使用者審完要求改，就在同一個 worktree 修好後重建 run，不改原 run。

**使用者審核時**：`ai-review queue` 看所有 repo 的待審（依 repo 分組；`cannot approve` 的項目見下）
→ 進 worktree 看 diff（終端機或任何 git GUI；改動都在未 commit 變更裡，**不要在 GUI 裡 stage 或 commit**）
＋審查單 → 改正裁決草稿 → `approve-code` → commit＋merge（一次一個；後 merge 的若衝突，解完要重跑驗證）
→ 裁決紀錄貼進 PR 描述 → 刪 worktree。

<!-- touchpoint: ios-dev-066 kind=code-review -->
**執行檔更新不影響核准**（2026-10-01 起）：run 停著的期間 `claude`、`codex` 或 Xcode 更新過，
`approve-code`、`status`、`queue` 仍然載得進這個 run（它們不執行模型或驗證指令）；`resume`、`answer`
等會執行的指令照舊拒絕。所以**已停著的 run 不要 `resume`**，要改就照第 5 步重建。
`queue` 標 `cannot approve` 的只剩 worktree 已被刪掉的 run——那種 run 沒有東西可審，直接放棄、從清單外處理。

## §3 純呈現畫面

- 只動版面、樣式、動畫時才是這一段；開發前只要答五問的第 3 問。
- 先跑 `ux-critique` 與 `architecture-auditor`，findings 併入 `ios-polish` 那一次修復。
- 收尾走輕。純呈現不派 `concurrency-auditor`。
- 改動很小（範圍單一、production diff ≤50 行）時 review 走 C；純視覺調整沒有自動化測試可寫，
  風險第三條以「Preview 或截圖可前後對照」算數。超過規模走預設的 B。
- 宣稱完成前用 Xcode MCP 的 `RenderPreview` 產改前、改後兩張 Preview 截圖附在回報裡當證據
  （要先 `XcodeOpenWorkspace`；分工見 `skill-router.md` §11）。
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
   `/writing-plans` 採用 `plan-template.md` 的模型分派判準（ticket frontmatter 有 `level` 就以它為準，不重判）；SDD 依 plan 已解析的實作級與審查級模型 ID 分派。
5. **共通收尾 1–5**。跑 verification 時**先照 ticket 的 Verification 段**（測試指令、build、實機走一遍）；
   舊 ticket 沒有這一段就照 Acceptance Criteria 自己列驗證步驟。回寫時 ticket 的 `covers` 列到的 FR# 不用另外處理，看板靠 `status`。
   <!-- touchpoint: ios-dev-041 kind=command -->
6. **問「接下一張？」**；全部 ticket 完成時提醒 Phase 5 `/work-log-writer` 與 Phase 6 `/second-brain`。

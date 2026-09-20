# 實作計畫模板（`/ios-dev` Step 6 用）

> `/writing-plans` 產出這份文件。落檔位置與命名見 SKILL.md Step 6；
> 輕／重判準見 `skill-router.md` §3，收尾見 `handoff-checklist.md`；
> 架構約束段怎麼填、轉移表與 async 契約的格式見 `architecture-impact-check.md`。

````markdown
# [功能名稱] 實作計畫

## 前置條件
- Design Doc 已審核
- Test cases 已審核

## 架構約束（實作時不可違反；收尾時 `architecture-auditor` 拿這一段當尺）

- 所屬模組與責任：
- state owner／presentation owner／async owner：
- 依賴方向與注入點（composition root）：
- 非同步工作生命週期：<每項六格：持有者／生命週期／清理／重入／舊結果失效／isolation；沒有寫「不適用」>
- 不可破壞的不變條件：<導航、取消、錯誤處理、時序>
- 行為驗收與可執行的驗證指令：

> 小任務可以精簡或逐項標「不適用」，但**不要整段刪掉**。
> 涉及流程時另附 presentation 轉移表（目前狀態／事件／下一狀態／副作用）。

## 中途架構檢查點（不要等全部寫完才檢查）

- **檢查時機**：<哪一段完整行為走通之後，例如「同意 → 授權檢查 → 導航」這條打通時>
- **由誰檢查**：<`architecture-auditor`／`concurrency-auditor`／兩者；小任務寫「主 session 自檢」>
- **對照什麼**：<上面的架構約束段 ＋ 根文件 §0 的哪幾條>
- **偏離時怎麼辦**：先判**是實作違約還是契約不適用**——
  **實作違約**（契約是對的）→ **修實作**並重新驗證，**不准改契約來遷就程式碼**；
  **契約確實不適用**（當初判斷錯或需求變了）→ 寫下理由、更新設計決策與對應測試，再繼續。
  判不出來就停下來問人。缺契約才回流補那幾格；**不要先寫完再說**

## Phase 2 實作任務

> 依實際變更裁，不要照抄五層：沒有外部依賴就不生 Service，沒有狀態就不生 ViewModel。
> 每個 Task 都要寫出**動到哪些檔案**與**可貼上去跑的驗證指令**。下面是滿編版的例子。

### Task 1: Model 層
- 建立資料結構（純資料，無 UI 依賴）
- **驗證**：xcodebuild 能編譯

### Task 2: Service Protocol
- 建立 Protocol 與 Mock（測試用）
- **驗證**：test target 能編譯

### Task 3: ViewModel（TDD）
- 先寫 tests（Red）→ 實作（Green）→ Refactor
- **驗證**：所有 tests pass

### Task 4: View 層
- 實作主要 View、拆分子元件、各 state 都有 Preview
- **驗證**：Preview 能渲染，各 state 正常

### Task 5: 整合
- 接上真實 Service、加入 Navigation
- **驗證**：在 Simulator 上 E2E 測試

## Phase 3 品質閘門

- 這次判定：**<輕／重>**（理由：<情境，或風險三條／規模兩條裡踩到的那一條>）
- Review 路線：**<B 純 agent（預設）／A 共識（使用者選了加 Codex，或複雜 Bugfix）／C 輕量（很小且風險三條全綠）>**（理由：<為什麼是這條>）
- 架構結論：**<直接擴充／局部整理／模組邊界>**（開發前的檢查結論；實作中若改變要回寫）
- 會派的 agent：<把名字列出來，不要寫「依情境裁」>
- 走 A 或 B 時，三個 specialist（`swiftui-reviewer`／`ux-critique`／`resilience-auditor`）
  一定要跑；走 A 時它們的 JSON 是 `--preflight` 的唯一合法內容
- 完整收尾步驟：交棒訊息裡已展開的「共通收尾」那一段（來源 `~/.claude/skills/ios-dev/references/handoff-checklist.md`）。
  交棒訊息沒帶到那一段就是交棒漏了，回去要，不要靠這行自己去讀檔——下游可能讀不到那個路徑

判定與 agent 清單在寫這份計畫時就填死：讀這份計畫的 session 不一定載入了 `/ios-dev`，
留一句「照 router §3 判」它查不到。
````

## 重閘門會派的 agent（一次發出、各自獨立 context、全部唯讀）

- `swiftui-reviewer`：code review（對照 `swiftui-expert-skill` checklist ＋ `latest-apis.md` 過時 API）
- `ux-critique`：設計批評（`ios-critique` 的 10 維度）
- `resilience-auditor`：韌性 ＋ Accessibility（`ios-harden` ＋ accessibility 檢查清單）
- `perf-auditor`：效能（`swiftui-performance-audit`；有疑慮升級 `trace-analyzer` 錄 trace 取證）
- `concurrency-auditor`：Swift 6 合規、**ownership 契約六格**（持有者／生命週期／清理／重入／舊結果失效／isolation）、Combine 邊界
- `architecture-auditor`：四個量化閘門 ＋ pattern 一致性，對照 §0 架構形狀與 feature PR checklist

外加 `review-swarm`（skill，不是 agent）當第四把：regression／安全隱私／測試覆蓋缺口。

情境裁法：情境 1 六個全上；修正（重）裁掉 `ux-critique`；純畫面重構省 `concurrency-auditor`；
優化必含 `perf-auditor` 改前改後各一次。

## 誰能改 code：走路線 A 時以 `init` 為界，切成兩段

（走 B 或 C 沒有這條界線——全程由主 session 修，但一樣只修一次、修完就驗證。）

**`init` 之前——主 session 改**

- 收齊閘門 agent 與 `review-swarm` 的報告，**一次統一修復**。這些 findings 在這裡就修完，
  **不進 `--preflight`**（`consensus-review` 只認三個 specialist 的 category，餵別的會被拒）。
- 修完在這裡跑 `/ios-polish` 與 `/verification-before-completion`。
- **最後**才派三個 specialist（唯讀）各回一段 fenced JSON，收成一個信封
  （`{"specialists": [...]}`，三個都要有，沒發現就 `"findings": []`），餵
  `ai-review init review --profile ios --preflight <file>`。
- 這一段不算 repair round——round 數從 `init` 之後才開始計。

**`init` 之後——只有 workflow 內那一個 Claude 改**

- 主 session 不再動任何檔案，包括「順手」的 polish。
- `ios-distill`、`simplify`、`ios-polish` 變成那一次修復的**輸出約束**，不是額外的修改階段。
- 每次修改消耗一個 repair round，並且一定會被下一輪 Codex 看見。

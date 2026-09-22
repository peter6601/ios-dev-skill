# ios-vibe.md review 01

- run: 20260921T042707Z-b06b3336
- review sequence: 1
- lens: direction（這份文件提出一個新 skill 的做法，還沒有任何實作，要審的是方向：用包裝層包住 ios-dev、用試用卡取代人工 code review、同時支援 Claude 和 Codex。）
- verdict: CHANGES_REQUIRED
- reviewed at: 2026-09-21T04:28:37.877200+00:00

## Blockers

### DIRECTION-001 — 文件選定的做法不得違反自己列出的約束。

- location: docs/design/ios-vibe.md:54
- evidence: 文件約束「例外表沒列的 ios-dev 規則一律照舊，包括所有審查 agent、風險三條與輕重判斷」，卻在 docs/design/ios-vibe.md:139 把「從零建立 app」當成情境 2。repository 明確把新專案列為情境 1並固定走重審查（skills/ios-dev/references/skill-router.md:51、skills/ios-dev/references/skill-router.md:54、skills/ios-dev/references/skill-router.md:158）；情境 2 則預設走輕（skills/ios-dev/references/skill-router.md:58、skills/ios-dev/references/skill-router.md:62、skills/ios-dev/references/skill-router.md:157）。這不是單純改寫提問，而是繞過原本的審查強度規則。
- required outcome: 讓從零建立 app 維持情境 1與固定重審查，只覆寫人機接觸點；若確實要改成情境 2，必須明列為例外，說明等價的重審查如何保留，並修正「輕重判斷照舊」的約束。

## Major

### DIRECTION-002 — 薄包裝層必須有可執行且可維護的組合邊界，不能只靠另一份語意對照表宣稱自動同步。

- location: docs/design/ios-vibe.md:42
- evidence: 文件稱 ios-vibe 不複製流程且 ios-dev 改版會自動跟上（docs/design/ios-vibe.md:52），但實際方案複製並改寫具名 Step、路線與硬閘門（docs/design/ios-vibe.md:83-125），且自己承認新增硬關卡仍須手動補例外表（docs/design/ios-vibe.md:374）。repository 把 router 定義為流程單點真相（skills/ios-dev/SKILL.md:30-32），phase-workflow 也內含多個 STOP、人工確認與審查分支（skills/phase-workflow/SKILL.md:91-112）；目前沒有讓 wrapper 攔截這些接觸點的穩定介面。
- required outcome: 定義可執行的 interaction-policy/profile 邊界，例如由 ios-dev 與 phase-workflow 在每個人類接觸點呼叫共用策略，工程師與 vibe 只提供不同 profile；或明確接受雙表同步成本並加入能枚舉所有 STOP／提問點、偵測新增硬閘門的契約測試。設計取捨需比較此共用策略方案與現有 wrapper 方案。

### DIRECTION-003 — 以試用取代人工 code review 時，驗收必須覆蓋人工審查原本控制的風險，而不只是產品外觀與可執行性。

- location: docs/design/ios-vibe.md:94
- evidence: 核心決策移除所有人工 code review（docs/design/ios-vibe.md:98-101），預設又只有同一模型的 agent 審查（docs/design/ios-vibe.md:226-232）。但 v1 驗收只量工程術語、試用步數、能否啟動、聲明與未存改動遺失（docs/design/ios-vibe.md:352-360），沒有資料毀損、隱私／權限、網路失敗、持久化 migration、背景工作或缺陷逃逸率。repository 原流程把持久化、網路、concurrency、公開契約列為升重條件（skills/ios-dev/references/skill-router.md:145-158），正是試用卡不容易發現的風險。
- required outcome: 明定 v1 的安全邊界與犧牲：要麼限制為離線、非敏感、無破壞性資料操作的 app；要麼對持久化、網路、刪除、權限與 concurrency 強制更獨立的審查。並在三次實測加入資料完整性、錯誤／離線路徑、權限拒絕及高風險 regression 的量化驗收。

# ios-vibe.md review 02

- run: 20260921T042707Z-b06b3336
- review sequence: 2
- lens: direction（這份文件提出一個新 skill 的做法，還沒有任何實作，要審的是方向：用包裝層包住 ios-dev、用試用卡取代人工 code review、同時支援 Claude 和 Codex。）
- verdict: CHANGES_REQUIRED
- reviewed at: 2026-09-21T06:14:49.114784+00:00

## Blockers

### DIRECTION-004 — 不可逆的 persisted schema 變更必須有明確 fallback。

- location: docs/design/ios-vibe.md:242
- evidence: 文件把「改變已存資料的格式」列為支援範圍，僅要求用舊格式輸入驗證升級成功（docs/design/ios-vibe.md:242、424-428）。版本回退則只從舊 commit 開新 branch（docs/design/ios-vibe.md:294-296），沒有說明 migration 失敗、升級中斷或新格式已寫入後如何還原資料；舊版 app 也未必能讀取已升級的資料。這是 persisted schema 的不可逆決定，卻沒有資料層 fallback。
- required outcome: 在允許任何格式升級前定義資料回復契約，例如升級前建立可驗證備份、transactional copy-and-swap、保留 schema version 與明確 restore 流程；並定義「回到上一版」遇到已升級資料時的行為與驗收。否則將 persisted-format migration 排除於 v1。

### DIRECTION-005 — 所選工具降級方案不得違反文件列出的強制驗證約束。

- location: docs/design/ios-vibe.md:247
- evidence: 文件要求「每張試用卡出之前」由 AI 開飛航模式並跑主要流程（docs/design/ios-vibe.md:247），但正式支援的最低工具組 `xcodebuild`＋`simctl` 被定義為「只能 build 和截圖，不能點」（docs/design/ios-vibe.md:354-359）。此降級路徑無法操作設定或跑完主要流程，卻沒有例外、替代網路隔離機制或交由使用者完成的規則，直接違反強制約束。
- required outcome: 為無 UI 自動化環境提供可執行的離線測試替代方案，或把 UI 自動化列為出試用卡的必要前提；若改由使用者操作，需明列例外及驗收證據，不能仍宣稱由 AI 在每張卡前完成。

## Major

### DIRECTION-002 — 薄包裝層必須有可執行且可維護的組合邊界，不能只靠另一份語意對照表宣稱自動同步。

- location: docs/design/ios-vibe.md:55
- evidence: 文件宣稱新增未標記的問人點時「檢查就失敗」，但檢查方法只是搜尋一組關鍵字附近是否有標記（docs/design/ios-vibe.md:167-172），並在風險表承認換一種說法就可能漏抓（docs/design/ios-vibe.md:460）。repository 的 phase-workflow 本身有多個 STOP 與人工決策分支，例如 skills/phase-workflow/SKILL.md:135-145；新增一個不用既有關鍵字的新分支時，標記與例外表會一起缺席，四項檢查仍可能全過。這尚未達到上一輪要求的「偵測新增硬閘門的契約測試」。
- required outcome: 把「一定會報錯」降為明確接受的最佳努力偵測，並加入能觀察實際執行期間所有人類接觸點的契約／transcript eval；或改採每個接觸點必須經過的共用 interaction API/profile，使未宣告的新接觸點預設失敗。

### DIRECTION-006 — 覆寫既有交棒路徑時，替代流程必須涵蓋被移除路徑原本承擔的規劃、切分、實作與收尾責任。

- location: docs/design/ios-vibe.md:188
- evidence: 文件以「同一個 session 小步快跑」取代新專案交給 phase-workflow 切 ticket（docs/design/ios-vibe.md:139、188），但 repository 明定 ios-dev 的規劃情境產出是計畫、不寫 code（skills/ios-dev/SKILL.md:15-17），而新專案／大功能命中模組邊界時會交 phase-workflow，再由每張 ticket 接回實作（skills/ios-dev/SKILL.md:68-70；skills/ios-dev/references/skill-router.md:126-135）。設計沒有定義 inline 路徑如何把架構計畫切成可驗收步驟、何時呼叫實作流程、如何逐步重判風險並跑完整收尾，因此「維持情境 1、只改交棒」目前不是完整替代。
- required outcome: 定義新專案的具體 inline state machine：規劃產物、步驟切分、每一步的實作入口、TDD、完成後風險重判、重審查與試用卡順序；或保留 phase-workflow 的規劃與 ticket 責任，只覆寫新 session／使用者手動接續要求。

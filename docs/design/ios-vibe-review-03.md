# ios-vibe.md review 03

- run: 20260921T042707Z-b06b3336
- review sequence: 3
- lens: direction（這份文件提出一個新 skill 的做法，還沒有任何實作，要審的是方向：用包裝層包住 ios-dev、用試用卡取代人工 code review、同時支援 Claude 和 Codex。）
- verdict: CHANGES_REQUIRED
- reviewed at: 2026-09-21T07:28:44.609334+00:00

## Blockers

### DIRECTION-007 — 文件不得依賴現有審查 API 明確禁止的核准流程。

- location: docs/design/ios-vibe.md:118
- evidence: 文件規定使用者回「OK」後「由 AI 代為執行」`approve-code`，但 repository 明定路線 A 必須停在 `AWAITING_HUMAN_CODE_REVIEW`，且由人執行 `approve-code`；人工核准前不得 commit、push、merge 或建立 PR（skills/ios-dev/SKILL.md:242-253；skills/ios-dev/references/handoff-checklist.md:73-76）。試用成果的 OK 也不是人工讀 code。這使設定 b 無法按文件描述完成。
- required outcome: 不要讓 AI 代執行 `approve-code`。若保留既有路線 A，就必須停下來交給真正讀過 code 的人；若目標使用者做不到，需另設不綁 `approve-code` 的跨模型審查路徑，並明確定義其終點與存檔順序。

### DIRECTION-008 — 所選驗收方案必須符合文件自己的約束：「三次的題目刻意涵蓋 §6『高風險改動的強制測試』的每一種」。

- location: docs/design/ios-vibe.md:469
- evidence: §6 列出存資料、格式升級、刪除、權限、背景或同時進行工作五類（docs/design/ios-vibe.md:266-274），但三次實測只明確要求存資料、格式升級、權限，以及刪除或資料毀損；沒有任何一次要求背景工作、取消或重複觸發（docs/design/ios-vibe.md:469-475）。因此「涵蓋每一種」與實際題目不一致。
- required outcome: 至少一個實測題目必須明確包含背景或並行工作，並驗收取消與重複觸發不會寫壞資料；同時把「四種」等計數修正為與實際分類一致。

## Major

### DIRECTION-009 — 禁止連網的安全邊界必須由能證明該行為的機制守住，不能把啟發式字串掃描當成完整驗證。

- location: docs/design/ios-vibe.md:276
- evidence: 設計宣稱每種工具組合都能完成強制驗證，卻只以掃描 `URLSession`、Network framework、WebSocket 與第三方 SDK 來判定不連網（docs/design/ios-vibe.md:278-281）。這會漏掉未列舉的系統 API、封裝後的呼叫及依賴內部流量；實機飛航模式只在三次作者實測中執行（docs/design/ios-vibe.md:490），不是每張試用卡的出卡閘門。
- required outcome: 將此檢查明確降級為 best-effort，並增加封閉的依賴 allowlist 或可觀察實際網路流量的執行期驗證；否則不能把零命中等同於 app 不會連網。

### DIRECTION-010 — 資料回退機制必須涵蓋 v1 允許的所有持久化資料，而不是只描述一個尚未綁定儲存架構的抽象資料檔。

- location: docs/design/ios-vibe.md:337
- evidence: 文件承諾升級前複製「整份資料檔」、舊版自動還原（docs/design/ios-vibe.md:339-345），但專案範本沒有選定或強制單一持久化方案，只說內建版本號與備份機制（docs/design/ios-vibe.md:411-419）。若生成的 app 使用 SwiftData/Core Data、UserDefaults 或多個檔案，範本無法僅靠泛用的「整份資料檔」保證所有資料都被一致備份與還原。
- required outcome: 為 v1 選定並強制一種持久化層與明確的資料根目錄／交易邊界，所有 app 資料只能經它寫入；或將備份承諾限制到明確支援的儲存類型，其他類型列為超出範圍。

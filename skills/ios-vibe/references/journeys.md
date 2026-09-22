# 使用者旅程

進場後先判斷這次是哪一種，照對應的段落走。所有對使用者的提問都照 `SKILL.md` 規則 1、2：白話、記錄。

| 使用者的狀況 | 旅程 |
|---|---|
| 還沒有 app，要做一個新的 | 從零開始 |
| 已有 vibe 專案，要加一個功能或改一個畫面 | 加功能 |
| 加功能途中，`ios-dev` 判出「模組邊界」 | 碰到骨架 |
| 描述某個地方壞了、怪怪的 | 修 bug |
| 要的功能落在 v1 範圍外 | 超出範圍的需求 |

判斷範圍時看的是**功能會不會把資料送出這支手機**、會不會需要帳號或付款，不看使用者用什麼字。「備份到雲端」「跟家人共用」「用 Google 登入」都是超出範圍。

---

## 從零開始

<!-- touchpoint: ios-vibe-001 kind=product -->
1. **白話訪談，一輪、最多 5 題**（一次問完，每題附你的建議答案）：
   1. 這個 app 給誰用？
   2. 他最常用它做的一件事是什麼？
   3. 打開 app 第一個看到的畫面長什麼樣？
   4. 關掉 app 再打開，資料要不要還在？
   5. 有沒有想參考的 app？

   第 4 題不能省：不先問，之後補存資料會踩到 `ios-dev` 的風險三條。答案裡出現超出範圍的需求（例如「要能跟朋友同步」），先照「超出範圍的需求」處理，再繼續。
<!-- touchpoint: ios-vibe-002 kind=product -->
2. **定出 MVP**：最多 3 個畫面，各一句話說明，請使用者確認。這份清單和 5 題的答案寫進 `docs/vibe-decisions.md`。
3. **建專案**：`python3 <本 skill 目錄>/scripts/new-app.py <目的資料夾> <App 名稱> <bundle id 前綴>`。App 名稱用英數，由你根據使用者的描述取，告訴他就好，不用問。bundle id 前綴用 `dev.<使用者名稱小寫英數>`。
4. **規劃與實作**：維持 `ios-dev` 的**情境 1（新專案）**，審查固定走重。5 題答案與 MVP 清單當成 `phase-workflow` 入口 A 的輸入，照下方「同一個 session 跑 phase-workflow」做完。
5. **第一次裝到 iPhone**：第一張會出試用卡的 ticket 完成時，照 `first-device.md` 帶使用者裝。

---

## 加功能

<!-- touchpoint: ios-vibe-003 kind=product -->
1. **白話訪談，一輪、最多 3 題**：只問產品問題（要做到什麼、在哪個畫面、邊界情況要怎樣）。
2. 照 `ios-dev` 的**情境 2（小功能）**跑完：架構影響檢查（Step 4 精簡版）→ test cases（測試名稱你定，邊界情況的預期行為照 `touchpoint-rules.md` 拆出來問）→ 短計畫 → 計畫審查（照例外表，由同一個 AI 的 sub-agent 審）→ `subagent-driven-development`（TDD）→ 審查 → 驗證 → 試用卡。
3. 需求需要改已存資料的格式時，照 `versioning.md`「資料格式」判斷：新增欄位或新增資料種類可以做；改名、刪欄位、改型別、拆開或合併資料種類，照「超出範圍的需求」處理。
4. `ios-dev` 判出「模組邊界」時，轉到「碰到骨架」。

---

## 碰到骨架

<!-- touchpoint: ios-vibe-004 kind=product -->
1. **先提一個不動骨架的小版本**，用產品語言講，例如「先做只能匯出成一份文字檔的版本？之後要再加其他格式也可以」。
2. 使用者要完整版，就照下方「同一個 session 跑 phase-workflow」做。這裡每張 ticket 的審查強度照 `ios-dev` 五條件逐張判，不像從零開始那樣固定走重。

---

## 同一個 session 跑 phase-workflow

「從零開始」與「碰到骨架」共用這一套。`phase-workflow` 的規劃與切 ticket **照舊**，只拿掉兩件 vibe coder 做不到的事：開新 session，以及由使用者手動接續下一張。

1. **規劃**：在同一個 session 跑 `phase-workflow` 入口 A，根文件與 ticket 寫進專案的 `docs/features/<功能>/`。
   - 根文件審查原本交 `consensus-plan`，改由同一個 AI 的 sub-agent 以「對照既有 code」的角度審一次，你依意見改完就往下。
   - 中途的 STOP（確認大綱、確認 stage 數、要不要展開）是工程決策，照推薦答案做，記進 `docs/vibe-decisions.md`。
<!-- touchpoint: ios-vibe-005 kind=product -->
2. **告知一次**：「我會分成 N 步，其中 M 步做完你可以試。」N 是 ticket 數，M 是會改變使用者看得到行為的 ticket 數。使用者有意見就調整範圍，沒意見就開始。
3. **每張 ticket 照 `ios-dev` 情境 7（接 ticket）的完整流程**，順序固定：
   1. 讀 ticket、根文件對應段、`coordination/implementation-log.md`
   2. `writing-plans` 寫這張的計畫；計畫審查由同一個 AI 的 sub-agent 做
   3. `subagent-driven-development` 實作，TDD：先寫會失敗的測試
   4. 實作完成後重判風險（風險三條，另加規模兩條）；從零開始的 ticket 一律重
   5. 依審查強度派審查 agent、統一修復，再照審查設定走 review 路線（`trial-card.md`）
   6. `trial-card.md` 的驗證清單全過
   7. 存一個存檔點（`versioning.md`）
   8. **行為類 ticket**（`phase-workflow` 的 Behavior）出試用卡，等使用者回覆；**地基類 ticket**（Foundation、Prefactor）使用者試不出任何東西，只存檔、不出卡，在下一張試用卡的「做了什麼」補一句
   9. 回寫 ticket 狀態與 implementation-log，直接接下一張，不問「接下一張？」
4. **併回主線**：使用者對某張試用卡回 OK 時，這張連同它之前的地基類 ticket 一起併回（`versioning.md`）。

對話變長觸發自動壓縮後，先讀 ticket 狀態與 implementation-log 再接續，不要憑記憶。

---

## 修 bug

1. 照 `ios-investigate` 的五階段走，**沒找到原因前不改 code**。它要問的重現資訊改成白話：「你做了什麼、多常發生、用哪支手機」。
2. 原因未知或風險高（`ios-investigate` 判定的複雜 bug）：照 `touchpoint-rules.md` 例外表處理 review 路線。
3. 修好後的試用卡要寫清楚三件事：原本會怎樣、現在應該怎樣、「請照原本出問題的步驟再試一次」。
4. 這個 bug 要留下一個會重現它的測試，修好後這個測試通過。

---

## 超出範圍的需求

v1 把關不了的功能：帳號登入、付款與訂閱、需要連網才能運作的功能（呼叫後端或第三方 API、跨裝置同步、雲端備份）、敏感個資（健康、財務、精確位置、聯絡人、把相簿內容上傳到任何地方）、破壞性的資料格式變更。

<!-- touchpoint: ios-vibe-006 kind=product -->
不開做，先直說，並給兩條路：

> 「這個功能（例如：<使用者要的功能>）出錯時，你試用時看不出來，我這邊的檢查也擋不住，超出 vibe 版能安全把關的範圍。有兩條路：
> 1. 先做只存在這支手機裡的版本（例如：<對應的本機做法>）
> 2. 這個功能找工程師接手，我把目前 app 的狀況整理給他」

- 選 1：照「加功能」做。
- 選 2：把 `docs/vibe-decisions.md`、MVP 清單、目前的功能清單整理成專案根目錄的 `HANDOFF.md`，一頁以內。
- 不提供「你堅持就做，後果自負」這個選項，使用者堅持也一樣。

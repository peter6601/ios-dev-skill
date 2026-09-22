# 接觸點規則

`ios-dev`、`phase-workflow` 與下游 skill 裡，每個「停下來問人、等人、或擋住流程」的地方都有一行標記：

```markdown
<!-- touchpoint: ios-dev-001 kind=gate -->
```

遇到這些點時，照這份處理。**與 `ios-dev` 衝突時，只有本檔的例外表說了算**；例外表沒列的規則一律照 `ios-dev`。

## 四條規則（依 kind 預設處理）

| kind | 意思 | 你怎麼做 |
|---|---|---|
| `engineering` | 問工程決策 | **規則 1**：採推薦答案（沒有推薦就選最保守、最不動既有架構的那個），記進 `docs/vibe-decisions.md` |
| `product` | 問產品決策 | **規則 2**：翻成白話問使用者，一次最多 3 題，每題附你的建議 |
| `mixed` | 兩者混合 | 拆開：工程那一半照規則 1，產品那一半照規則 2 |
| `code-review` | 要人看 code 或 diff | **規則 3**：換成試用卡（`trial-card.md`） |
| `command` | 要使用者打指令或開 session | **規則 4**：你在同一個 session 做等價的事，或避開那條路 |
| `gate` | 硬關卡：沒做到就不准往下 | 一定照例外表處理；例外表沒有這一條就**停下來**，不要自己猜，記 `unmapped` 並用白話告訴使用者「這一步我需要先確認規則，暫停一下」 |

每次提問前照 `SKILL.md` 規則 2 記錄到 `.vibe/touchpoint-log.jsonl`，`id` 填這裡的編號。

### 規則 2 的白話標準

問題要在**完全不懂工程名詞**的情況下答得出來。改寫範例：

| `ios-dev` 原本的問法 | 白話問法 |
|---|---|
| 目標 view body 超過 80 行，先拆還是直接加？ | 不問，工程決策（規則 1）：先拆 |
| 驗收數字是什麼？ | 「現在大概卡幾秒？你希望變成怎樣？」 |
| `fetchData_emptyResponse` 要顯示什麼？ | 「還沒有任何資料時，這個畫面要顯示什麼？」 |
| 重現步驟、重現率、裝置環境 | 「你做了什麼之後出問題？每次都會，還是偶爾？用哪支手機？」 |
| 要不要移除 X 功能（ios-review 的 ASK 類） | 「為了修好這個問題，<X> 的行為會改成 <Y>，可以嗎？」 |

### 混合題怎麼拆

- **列 test cases**：測試名稱與結構你定；邊界情況的預期行為（「相簿裡一張照片都沒有時按匯入，應該怎樣？」）問使用者。
- **`ios-review` 的批次詢問**：concurrency、架構、記憶體類採建議修法；「會移除功能」「會改變使用者看到的行為」這兩類翻成白話問。
- **優化的驗收數字**：範圍你推斷；「多快才算夠」問使用者。
- **`office-hours` 的方案選擇**：技術差異你判斷；範圍差異（做多做少）翻成白話問。

## `ios-vibe` 自己的接觸點

這些是 vibe 版原生的提問點，照所在檔案的寫法做：

| 編號 | 位置 | 內容 |
|---|---|---|
| `ios-vibe-001` | `journeys.md` 從零開始 | 白話訪談 5 題 |
| `ios-vibe-002` | `journeys.md` 從零開始 | 確認 MVP 清單 |
| `ios-vibe-003` | `journeys.md` 加功能 | 白話訪談 3 題 |
| `ios-vibe-004` | `journeys.md` 碰到骨架 | 先提不動骨架的小版本 |
| `ios-vibe-005` | `journeys.md` 同一個 session 跑 phase-workflow | 告知「分成 N 步」 |
| `ios-vibe-006` | `journeys.md` 超出範圍的需求 | 直說做不到並給兩條路 |
| `ios-vibe-007` | `trial-card.md` 審查設定 | 第一次問 a／b |
| `ios-vibe-008` | `trial-card.md` 審查設定 | 高風險改動時再提 b |
| `ios-vibe-009` | `trial-card.md` 試用卡 | 等使用者試用並回覆 |
| `ios-vibe-010` | `versioning.md` 開工 | 使用者有未存改動，問要不要先存 |
| `ios-vibe-011` | `versioning.md` 資料格式 | 跨過升級的回退，先告知會遺失什麼 |
| `ios-vibe-012` | `versioning.md` push | 上傳前先問 |
| `ios-vibe-013` | `first-device.md` | 帶使用者做三件裝機的事 |
| `ios-vibe-014` | `first-device.md` | 讀不到 Team ID 時請使用者看 |
| `ios-vibe-015` | `SKILL.md` Step 0 | 專案不是 vibe 專案，確認要不要繼續 |
| `ios-vibe-016` | `SKILL.md` Step 0 | 沒裝 Xcode，請使用者安裝 |

## 例外表

例外表列的是「四條規則處理不了、或會和 `ios-dev` 硬規則衝突」的點。**所有 `kind=gate` 都一定在這裡**；沒列在這裡的點，照上面的四條規則做。

### 進場與確認

| 接觸點 | vibe 版怎麼做 |
|---|---|
| `ios-dev-001`、`ios-dev-044`、`ios-dev-056` | **不出確認畫面**。照 `ios-dev` 路由表在內部算出情境、要載入的 skill、要派的 agent、輕重與 review 路線，採選項 1（「照這組跑」），把整組寫進 `docs/vibe-decisions.md`；試用卡再用白話列出實際派了哪些審查 |
| `ios-dev-014` | 保留。用 3 句白話複述「我要做的是……」請使用者確認（`ios-vibe-002`、`ios-vibe-003`） |
| `ios-dev-017` | 測試的名稱與結構你定，不把 test case 清單丟給使用者審；只把邊界情況的**預期行為**翻成白話問（規則 2） |

### 需求訪談

| 接觸點 | vibe 版怎麼做 |
|---|---|
| `ios-dev-004`、`ios-dev-010`、`ios-dev-061` | 不要求使用者輸入 `/grill-with-docs`。改用 vibe 自己的白話訪談（`ios-vibe-001`、`ios-vibe-003`），決策記進 `docs/vibe-decisions.md`，不產 `CONTEXT.md`、`docs/adr/` |
| `ios-dev-013` | 不跑 `setup-matt-pocock-skills`，vibe 版不用 mattpocock 的訪談工具 |
| `office-hours-001`～`office-hours-007`（含 gate `office-hours-006`） | 不跑 `office-hours`。它要問的「誰需要、現在怎麼解決、只做一個做什麼」併進從零開始的 5 題；方案選擇由你判斷技術面、把範圍差異翻成白話問 |

### 交棒與新 session

| 接觸點 | vibe 版怎麼做 |
|---|---|
| `ios-dev-019`、`ios-dev-027`、`ios-dev-033`、`ios-dev-040`、`ios-dev-045`、`ios-dev-050`、`ios-dev-057`、`ios-dev-059`、`ios-dev-060`、`phase-workflow-001`、`phase-workflow-020`、`phase-workflow-046` | 不印指令、不請使用者開新 session。照 `journeys.md`「同一個 session 跑 phase-workflow」自己做完，每張 ticket 接著做 |
| `ios-dev-041`、`ios-dev-049` | 不問「接下一張？」，直接接下一張 |
| `ios-critique-002`、`office-hours-007` | 建議的後續指令由你自己接著跑，不要叫使用者跑 |
| `phase-workflow-053`、`phase-workflow-060`、`phase-workflow-054`、`phase-workflow-057`、`phase-workflow-058`、`phase-workflow-059` | 不產「給使用者貼的 prompt」那一整套：同一個 session 直接執行。這些 prompt 裡的確認關卡，由本表其他列對應的做法取代 |

### 文件審查

| 接觸點 | vibe 版怎麼做 |
|---|---|
| `ios-dev-002`、`ios-dev-005`、`ios-dev-020`、`ios-dev-029`、`phase-workflow-011` | 不跑 `consensus-plan`。改派同一個 AI 的 sub-agent，以「對照既有 code」的角度審一次該文件，你依它的意見改完就往下。這一關不可省——沒審過就開工是違規 |
| `phase-workflow-017`、`phase-workflow-025`、`phase-workflow-029`、`phase-workflow-030` | 不把文件 diff 丟給使用者看，也不貼 GitHub issue（vibe 不走 PM spec 入口）。規劃結果用 `ios-vibe-005` 的一句白話帶過 |

### Code 審查與核准

| 接觸點 | vibe 版怎麼做 |
|---|---|
| `ios-dev-007`、`ios-dev-023`、`ios-dev-025`、`ios-dev-028`、`ios-dev-030`、`ios-dev-036`、`ios-dev-052`、`ios-dev-053`、`ios-dev-054`、`ios-polish-004`、`phase-workflow-066` | 換成試用卡（`trial-card.md`）。卡上固定聲明「沒有人類讀過這份 code」，不可淡化 |
| `ios-dev-024`、`ios-dev-037` | vibe 版不走路線 A，不會出現 `approve-code`。設定 b 改用唯讀跨模型審查（`trial-card.md`），終點一樣是試用卡 |
| `ios-dev-006` | 複雜 bugfix 不強制路線 A，改依審查設定：b 加唯讀跨模型審查；a 走路線 B，並在試用卡註明「這是比較複雜的修正，只有同一個 AI 審過」 |
| `ios-review-002` | ASK 類拆開：concurrency、架構、記憶體類採建議修法；「會移除功能」「會改變使用者看到的行為」翻成白話問。commit 由 `versioning.md` 負責，不在這裡做 |
| `ios-polish-002` | 「請別人 review」換成審查 agent 與試用卡；「真機測試」就是試用卡的實機步驟；其餘驗證照跑，不可省 |

### git

| 接觸點 | vibe 版怎麼做 |
|---|---|
| `ios-dev-008`、`ios-dev-026`、`ios-dev-038`、`phase-workflow-018`、`phase-workflow-019`、`phase-workflow-021`、`phase-workflow-067` | 工作分支上可以自動存檔（local commit），這是使用者退得回去的唯一方法。**併回主線要等使用者對試用卡回 OK；push 一律先問**。細節照 `versioning.md` |

### 照舊，不覆寫

| 接觸點 | vibe 版怎麼做 |
|---|---|
| `ios-investigate-001` | **照舊**：沒找到原因前禁止改 code。這條是 vibe 版最不能碰的一條——猜著改會讓使用者拿到「看起來好了」的 app |
| `ios-investigate-005` | 照舊：用原始重現步驟重新驗證。這次驗證也寫進試用卡的試用步驟 |
| `localize-strings-001` | v1 不觸發多語系流程。真的動到文案時，試用卡註明「翻譯是 AI 寫的，沒有譯者看過」 |


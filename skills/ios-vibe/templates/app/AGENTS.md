# VibeApp

這是一個 **vibe 專案**：由 `ios-vibe` 這個 skill 管理。使用者不讀 code，只看畫面對不對、會不會閃退，
所以「能不能通過檢查」全靠下面這些規則和自動化測試，不靠人工 review。

AI 在這個專案工作時，以下規則優先於一般習慣。要違反任何一條，先停下來用白話說明，請使用者決定。

## v1 規則

1. **不連網**：不呼叫網路服務、不加同步或登入、不用 WKWebView 載遠端網頁。
   測試用的 build 會攔截所有網路請求，一攔到就當掉，測試直接失敗（`VibeApp/Debug/NetworkBlocker.swift`）。
2. **不加第三方套件**：不加 Swift Package、CocoaPods、Carthage，也不直接把 framework／xcframework 放進專案。
3. **資料只存兩個地方**：
   - SwiftData：資料庫固定開在資料根目錄，只能由 `VibeApp/Data/DataStack.swift` 開。
   - 使用者產生的檔案：只能透過 `DataFiles` 寫進資料根目錄底下的 `Files/`。
   不准用 Core Data、SQLite、Keychain，也不准自己組路徑寫檔。
4. **UserDefaults 只存介面偏好**（例如上次停在哪個分頁），key 一律以 `ui.` 開頭。使用者的資料不可以放這裡。
5. **資料格式只准「新增」**：新增欄位（要有預設值）或新增一種資料。
   不改名、不刪欄位、不改型別、不拆開或合併資料種類——那類變更一旦失敗，使用者的資料救不回來。
   新增時照 `VibeApp/Data/AppSchema.swift` 開頭的四個步驟做，並把 `DataFormat.currentVersion` 加 1。
6. **改動前後都要跑測試**：
   `xcodebuild -project VibeApp.xcodeproj -scheme VibeApp -destination 'platform=iOS Simulator,name=<模擬器型號>' test`
   單元測試與 UI 測試全過才算完成。UI 測試一律用 `XCUIApplication.launchForVibeTest()` 啟動，
   才會帶上不連網旗標與測試專用的資料夾。
7. **邊界檢查要 0 命中**：`python3 <ios-vibe>/scripts/check-boundaries.py .`

## 資料放在哪

- 資料根目錄：`Application Support/VibeApp/Data/`（資料庫、格式版本號、使用者檔案都在這裡）
- 自動備份：`Application Support/VibeApp/Backups/`（升級前整個 Data 複製一份，永遠不要自動刪）
- app 啟動時會先處理備份／升級／還原，再打開資料庫；這段邏輯在 `VibeApp/Data/DataBootstrapper.swift`，有自己的測試。

## 其他

- `.vibe/` 是 AI 的執行期紀錄（提問紀錄之類），不進版本紀錄。
- 範本自帶的資料層與網路攔截器都有測試。要改它們，先想清楚後果，改完測試要全過。

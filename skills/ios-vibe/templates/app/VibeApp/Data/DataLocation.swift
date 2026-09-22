// vibe-boundaries: allow file-io — 這裡是範本的資料層，負責決定資料放哪裡，本來就要碰檔案系統。
//
// 資料只有一個家：
//   Application Support/VibeApp/
//     Data/        ← 資料庫、格式版本號、使用者產生的檔案，全部在這裡
//     Backups/     ← 升級前的自動備份（不放在 Data 裡，備份才不會備份到自己）
//
// 其他地方的程式不可以自己決定路徑，要存檔一律透過 DataFiles（同資料夾）。

import Foundation

nonisolated struct DataLocation: Sendable, Equatable {
    /// app 專屬的資料夾（Data 與 Backups 的上層）。
    let appRoot: URL

    /// 資料根目錄：這支 app 的所有資料都在這底下。
    var dataRoot: URL { appRoot.appending(path: "Data", directoryHint: .isDirectory) }

    /// 備份資料夾：升級前的整份 Data 複本。
    var backupsRoot: URL { appRoot.appending(path: "Backups", directoryHint: .isDirectory) }

    /// SwiftData 資料庫的固定位置。
    var storeURL: URL { dataRoot.appending(path: "app.store", directoryHint: .notDirectory) }

    /// 資料格式版本號檔案。
    var formatVersionURL: URL { dataRoot.appending(path: "format-version.json", directoryHint: .notDirectory) }

    /// 使用者產生的檔案（照片副本之類）放這裡。
    var filesRoot: URL { dataRoot.appending(path: "Files", directoryHint: .isDirectory) }

    /// 「已經從備份還原」的旗標檔。放在 Data 外面，還原時才不會被覆蓋掉。
    var restoredNoticeURL: URL { appRoot.appending(path: "restored-notice.json", directoryHint: .notDirectory) }

    /// app 在 Application Support 底下的資料夾名稱。
    static let appFolderName = "VibeApp"

    /// 正式啟動時用的位置。
    ///
    /// DEBUG 且帶著 `VIBE_TEST_DATA` 旗標時（只有 UI 測試會帶），改用另一個資料夾，
    /// 測試永遠碰不到使用者的真資料：
    ///   - `fresh`：先清掉測試資料夾，從乾淨狀態開始
    ///   - `keep` ：沿用上一次測試留下的資料（測「關掉再打開資料還在嗎」）
    static func forCurrentLaunch(
        processInfo: ProcessInfo = .processInfo,
        fileManager: FileManager = .default
    ) throws -> DataLocation {
        let support = try fileManager.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        #if DEBUG
        if let mode = processInfo.environment["VIBE_TEST_DATA"] {
            let root = support.appending(path: "\(appFolderName)-UITests", directoryHint: .isDirectory)
            if mode == "fresh" {
                try? fileManager.removeItem(at: root)
            }
            return DataLocation(appRoot: root)
        }
        #endif
        return DataLocation(appRoot: support.appending(path: appFolderName, directoryHint: .isDirectory))
    }
}

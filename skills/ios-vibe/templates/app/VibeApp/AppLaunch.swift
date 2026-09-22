// app 一啟動就跑這裡：先擋網路（只在測試用的 build）、再備份／升級／還原資料，最後才打開資料庫。
//
// 順序很重要：資料庫一旦打開，SwiftData 就可能開始升級檔案，那時候再備份已經來不及。

import Foundation
import SwiftData

/// 要用白話講給使用者聽的資料狀況。
enum DataNotice: Equatable, Sendable {
    /// 從備份還原回舊版資料。
    case restoredFromBackup
    /// 資料是比較新的版本存的，這一版讀不懂，也沒有備份可以退回。
    case newerDataReadOnly

    var message: String {
        switch self {
        case .restoredFromBackup:
            "已回到先前版本的資料，升級之後新增的資料不在這裡。那些資料沒有被刪掉，另外收在備份資料夾裡。"
        case .newerDataReadOnly:
            "這份資料是比較新版本的 app 存的，這一版讀不懂，也找不到可以退回的備份。原本的資料都還在、沒有被刪掉，裝回新版就看得到。現在先用空白、不能修改的模式打開。"
        }
    }
}

/// 一次啟動的結果，畫面照這個決定要顯示什麼。
@MainActor
@Observable
final class DataSession {
    let container: ModelContainer
    /// 使用者檔案的存取入口（唯讀模式下寫入會失敗）。
    let files: DataFiles
    /// 唯讀模式：不給新增、不給刪除。
    let isReadOnly: Bool
    private(set) var notice: DataNotice?
    private let bootstrapper: DataBootstrapper?

    init(container: ModelContainer, files: DataFiles, isReadOnly: Bool, notice: DataNotice?, bootstrapper: DataBootstrapper?) {
        self.container = container
        self.files = files
        self.isReadOnly = isReadOnly
        self.notice = notice
        self.bootstrapper = bootstrapper
    }

    /// 使用者按了「知道了」。還原提示按掉之後就不再出現。
    func dismissNotice() {
        if notice == .restoredFromBackup {
            bootstrapper?.clearRestoredNotice()
        }
        notice = nil
    }
}

enum AppLaunch {
    enum Result {
        case ready(DataSession)
        /// 資料打不開。不刪任何東西，把狀況講給使用者聽。
        case failed(String)
        /// 單元測試借用這個 app 當殼跑，不要碰資料。
        case hostingUnitTests
    }

    static func start() -> Result {
        #if DEBUG
        NetworkBlocker.installIfRequested()
        if isHostingUnitTests { return .hostingUnitTests }
        #endif

        do {
            let location = try DataLocation.forCurrentLaunch()
            let bootstrapper = DataBootstrapper(location: location, appVersion: DataFormat.currentVersion)
            let outcome = try bootstrapper.prepare()

            guard outcome.opensStoreOnDisk else {
                // 讀不懂又沒備份：磁碟上的資料一個字都不動，改用空白的記憶體資料庫開起來。
                let container = try DataStack.makeInMemoryContainer()
                return .ready(DataSession(
                    container: container,
                    files: DataFiles(root: location.filesRoot, isReadOnly: true),
                    isReadOnly: true,
                    notice: .newerDataReadOnly,
                    bootstrapper: bootstrapper
                ))
            }

            let container = try DataStack.makeContainer(at: location)
            if case .upgradePending = outcome {
                // 升級成功了才更新版本號；失敗的話版本號維持舊的，下次啟動再試一次。
                try bootstrapper.finishUpgrade()
            }
            let notice: DataNotice? = bootstrapper.hasRestoredNotice ? .restoredFromBackup : nil
            return .ready(DataSession(
                container: container,
                files: DataFiles(root: location.filesRoot),
                isReadOnly: false,
                notice: notice,
                bootstrapper: bootstrapper
            ))
        } catch {
            return .failed(String(describing: error))
        }
    }

    #if DEBUG
    /// 單元測試是掛在這個 app 裡跑的；那時候不要動使用者的資料。
    /// UI 測試不會走到這裡（被測的 app 是獨立啟動的，沒有這些環境變數）。
    static var isHostingUnitTests: Bool {
        let environment = ProcessInfo.processInfo.environment
        return environment["XCTestConfigurationFilePath"] != nil
            || environment["XCTestBundlePath"] != nil
            || environment["XCTestSessionIdentifier"] != nil
    }
    #endif
}

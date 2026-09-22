// vibe-boundaries: allow file-io — 資料層本身，負責備份與還原整個資料根目錄。
//
// app 啟動、打開資料庫「之前」要先跑這裡。四種狀況：
//
//   1. 第一次啟動           → 建好 Data，寫下版本號
//   2. 版本號和 app 一樣     → 什麼都不用做
//   3. 存的版本比 app 舊     → 先把整個 Data 複製到 Backups/v<舊版本>-<時間>/，
//                             再讓 SwiftData 升級，升級成功後才更新版本號
//   4. 存的版本比 app 新     → 舊版 app 讀不懂新格式：
//                             a. 找得到這一版的備份：把現在的 Data 移到 Backups/unreadable-v<版本>-<時間>/，
//                                把備份複製回 Data，並留下旗標讓畫面顯示白話提示
//                             b. 找不到備份：什麼都不刪、不搬，以空白唯讀模式啟動並顯示提示
//
// 4b 為什麼不搬也不刪：那份資料是新版 app 存的，使用者只要把新版裝回來就看得到。
// 這時候動它（刪掉或搬走）只會讓事情更糟，所以選擇「原封不動 + 說清楚」。

import Foundation

nonisolated struct DataBootstrapper: Sendable {
    let location: DataLocation
    /// 這一版 app 看得懂的格式版本（正式啟動時就是 DataFormat.currentVersion）。
    let appVersion: Int
    var now: @Sendable () -> Date = { .now }

    /// FileManager 本身不是 Sendable，所以不當成存起來的屬性，每次用的時候拿共用的那個。
    private var fileManager: FileManager { .default }

    enum Outcome: Equatable, Sendable {
        /// 第一次啟動，Data 是新建的。
        case firstLaunch
        /// 版本號和 app 一樣，直接用。
        case upToDate
        /// 已經備份好，等 SwiftData 升級；升級成功後要呼叫 finishUpgrade()。
        case upgradePending(from: Int, backup: URL)
        /// 舊版 app 遇到新格式，已經還原了這一版的備份。
        case restoredFromBackup(unreadableVersion: Int, restoredFrom: URL, setAside: URL)
        /// 舊版 app 遇到新格式，但沒有可以還原的備份：資料原封不動，以空白唯讀模式啟動。
        case newerDataWithoutBackup(storedVersion: Int)

        /// 可以打開磁碟上的資料庫嗎？（唯一的例外是「讀不懂又沒備份」）
        var opensStoreOnDisk: Bool {
            if case .newerDataWithoutBackup = self { return false }
            return true
        }
    }

    enum BootstrapError: Error, Equatable {
        case backupFailed(String)
        case restoreFailed(String)
    }

    // MARK: - 主流程

    func prepare() throws -> Outcome {
        try fileManager.createDirectory(at: location.appRoot, withIntermediateDirectories: true)

        guard let stored = try storedVersion() else {
            try createFreshData()
            return .firstLaunch
        }

        if stored == appVersion {
            try fileManager.createDirectory(at: location.filesRoot, withIntermediateDirectories: true)
            return .upToDate
        }

        if stored < appVersion {
            let backup = try makeBackup(ofVersion: stored)
            return .upgradePending(from: stored, backup: backup)
        }

        // stored > appVersion：這一版 app 讀不懂。
        guard let backup = try latestBackup(ofVersion: appVersion) else {
            return .newerDataWithoutBackup(storedVersion: stored)
        }
        let setAside = try restore(from: backup, unreadableVersion: stored)
        return .restoredFromBackup(unreadableVersion: stored, restoredFrom: backup, setAside: setAside)
    }

    /// SwiftData 升級成功之後才呼叫：把版本號寫成這一版。
    /// 升級失敗時不會被呼叫，版本號維持舊的，下次啟動會再走一次升級流程（備份仍在）。
    func finishUpgrade() throws {
        try writeVersion(appVersion)
    }

    // MARK: - 版本號

    /// 回傳存在磁碟上的格式版本；`nil` 代表「還沒有任何資料」。
    ///
    /// Data 裡有東西、但版本號檔不見了或壞了，一律當成版本 0（比任何 app 版本都舊），
    /// 也就是走「先備份再升級」那條路——寧可多備份一次，也不要在沒備份的情況下動資料。
    func storedVersion() throws -> Int? {
        guard fileManager.fileExists(atPath: location.dataRoot.path(percentEncoded: false)) else { return nil }
        let contents = (try? fileManager.contentsOfDirectory(atPath: location.dataRoot.path(percentEncoded: false))) ?? []
        if contents.isEmpty { return nil }

        guard let data = try? Data(contentsOf: location.formatVersionURL),
              let file = try? JSONDecoder().decode(DataFormatFile.self, from: data) else {
            return 0
        }
        return file.formatVersion
    }

    private func writeVersion(_ version: Int) throws {
        let data = try JSONEncoder().encode(DataFormatFile(formatVersion: version))
        try data.write(to: location.formatVersionURL, options: .atomic)
    }

    private func createFreshData() throws {
        try fileManager.createDirectory(at: location.dataRoot, withIntermediateDirectories: true)
        // 先寫版本號再建 Files：萬一中途被中斷，Data 是空的，下次啟動仍然算「第一次」。
        try writeVersion(appVersion)
        try fileManager.createDirectory(at: location.filesRoot, withIntermediateDirectories: true)
    }

    // MARK: - 備份

    /// 把整個 Data 複製到 Backups/v<版本>-<時間>/。
    /// 先複製到暫存名字再改名，中途被中斷不會留下看起來完整、其實只複製一半的備份。
    @discardableResult
    func makeBackup(ofVersion version: Int) throws -> URL {
        try fileManager.createDirectory(at: location.backupsRoot, withIntermediateDirectories: true)
        let staging = location.backupsRoot.appending(
            path: ".incomplete-\(UUID().uuidString)",
            directoryHint: .isDirectory
        )
        do {
            try fileManager.copyItem(at: location.dataRoot, to: staging)
        } catch {
            try? fileManager.removeItem(at: staging)
            throw BootstrapError.backupFailed(error.localizedDescription)
        }
        let destination = uniqueURL(in: location.backupsRoot, baseName: "v\(version)-\(timestamp())")
        do {
            try fileManager.moveItem(at: staging, to: destination)
        } catch {
            try? fileManager.removeItem(at: staging)
            throw BootstrapError.backupFailed(error.localizedDescription)
        }
        return destination
    }

    /// 找出某個格式版本最近一次的備份。
    /// 只認 `v<版本>-<時間>` 這種名字，而且會打開裡面的版本號檔再確認一次。
    func latestBackup(ofVersion version: Int) throws -> URL? {
        let names = (try? fileManager.contentsOfDirectory(atPath: location.backupsRoot.path(percentEncoded: false))) ?? []
        let prefix = "v\(version)-"
        let candidates = names
            .filter { $0.hasPrefix(prefix) }
            .sorted { sortKey($0, prefix: prefix) < sortKey($1, prefix: prefix) }

        for name in candidates.reversed() {
            let url = location.backupsRoot.appending(path: name, directoryHint: .isDirectory)
            let versionFile = url.appending(path: "format-version.json", directoryHint: .notDirectory)
            guard let data = try? Data(contentsOf: versionFile),
                  let file = try? JSONDecoder().decode(DataFormatFile.self, from: data),
                  file.formatVersion == version else { continue }
            return url
        }
        return nil
    }

    /// 排序用：時間字串固定長度，後面的重名編號補零才不會 "-10" 排在 "-2" 前面。
    private func sortKey(_ name: String, prefix: String) -> String {
        let rest = String(name.dropFirst(prefix.count))
        let parts = rest.split(separator: "-", maxSplits: 1, omittingEmptySubsequences: false)
        let stamp = String(parts.first ?? "")
        let suffix = parts.count > 1 ? Int(parts[1]) ?? 0 : 0
        return "\(stamp)-\(String(format: "%06d", suffix))"
    }

    // MARK: - 還原

    /// 舊版 app 遇到新格式時：把備份複製回 Data，把讀不懂的資料移到 Backups 留著。
    ///
    /// 順序刻意是「先把備份複製到暫存 → 再把 Data 搬走 → 再把暫存改名成 Data」，
    /// 兩次改名之間的空窗最短。真的在空窗中斷電，下次啟動會當成第一次啟動，
    /// 但讀不懂的那份資料已經在 Backups 裡，沒有被刪掉。
    private func restore(from backup: URL, unreadableVersion: Int) throws -> URL {
        let staging = location.appRoot.appending(
            path: ".restoring-\(UUID().uuidString)",
            directoryHint: .isDirectory
        )
        do {
            try fileManager.copyItem(at: backup, to: staging)
        } catch {
            try? fileManager.removeItem(at: staging)
            throw BootstrapError.restoreFailed(error.localizedDescription)
        }

        let setAside = uniqueURL(
            in: location.backupsRoot,
            baseName: "unreadable-v\(unreadableVersion)-\(timestamp())"
        )
        do {
            try fileManager.createDirectory(at: location.backupsRoot, withIntermediateDirectories: true)
            try fileManager.moveItem(at: location.dataRoot, to: setAside)
        } catch {
            try? fileManager.removeItem(at: staging)
            throw BootstrapError.restoreFailed(error.localizedDescription)
        }

        do {
            try fileManager.moveItem(at: staging, to: location.dataRoot)
        } catch {
            // 把讀不懂的資料搬回原位，至少回到進來時的狀態。
            try? fileManager.moveItem(at: setAside, to: location.dataRoot)
            try? fileManager.removeItem(at: staging)
            throw BootstrapError.restoreFailed(error.localizedDescription)
        }

        try? fileManager.createDirectory(at: location.filesRoot, withIntermediateDirectories: true)
        markRestoredNotice()
        return setAside
    }

    // MARK: - 提示旗標

    /// 還原之後留一個旗標，畫面上要顯示白話提示。使用者按掉之前一直留著。
    private func markRestoredNotice() {
        let payload = ["restoredAt": ISO8601DateFormatter().string(from: now())]
        guard let data = try? JSONSerialization.data(withJSONObject: payload) else { return }
        try? data.write(to: location.restoredNoticeURL, options: .atomic)
    }

    var hasRestoredNotice: Bool {
        fileManager.fileExists(atPath: location.restoredNoticeURL.path(percentEncoded: false))
    }

    func clearRestoredNotice() {
        try? fileManager.removeItem(at: location.restoredNoticeURL)
    }

    // MARK: - 小工具

    private func timestamp() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "UTC")
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        return formatter.string(from: now())
    }

    private func uniqueURL(in directory: URL, baseName: String) -> URL {
        var candidate = directory.appending(path: baseName, directoryHint: .isDirectory)
        var counter = 2
        while fileManager.fileExists(atPath: candidate.path(percentEncoded: false)) {
            candidate = directory.appending(path: "\(baseName)-\(counter)", directoryHint: .isDirectory)
            counter += 1
        }
        return candidate
    }
}

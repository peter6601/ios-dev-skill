import Foundation
import Testing
@testable import VibeApp

/// 資料的備份與還原是範本自己的機制，它出錯就等於弄丟使用者的資料，
/// 所以五種啟動情況都要有測試：首次啟動、同版本、升級備份、舊版還原、找不到備份。
struct DataBootstrapperTests {

    // MARK: - 工具

    private func bootstrapper(
        in temp: TempDirectory,
        appVersion: Int,
        at instant: String = "2026-01-01T00:00:00Z"
    ) -> DataBootstrapper {
        let date = ISO8601DateFormatter().date(from: instant) ?? Date(timeIntervalSince1970: 0)
        return DataBootstrapper(
            location: DataLocation(appRoot: temp.url),
            appVersion: appVersion,
            now: { date }
        )
    }

    /// 造出「已經存在、版本是 version」的資料。
    private func seedData(in temp: TempDirectory, version: Int, extraFile: String = "photo.txt") {
        temp.writeFile("Data/format-version.json", contents: "{\"formatVersion\":\(version)}")
        temp.writeFile("Data/app.store", contents: "store-v\(version)")
        temp.writeFile("Data/Files/\(extraFile)", contents: "使用者的檔案 v\(version)")
    }

    // MARK: - 1. 首次啟動

    @Test func firstLaunchCreatesDataRootAndVersionFile() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        let boot = bootstrapper(in: temp, appVersion: 1)

        #expect(try boot.prepare() == .firstLaunch)
        #expect(try boot.storedVersion() == 1)
        #expect(FileManager.default.fileExists(atPath: boot.location.filesRoot.path(percentEncoded: false)))
        // 第一次啟動沒有東西需要備份。
        #expect(fileTree(at: boot.location.backupsRoot).isEmpty)
    }

    // MARK: - 2. 同版本

    @Test func sameVersionTouchesNothing() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        seedData(in: temp, version: 1)
        let boot = bootstrapper(in: temp, appVersion: 1)
        let before = fileTree(at: boot.location.dataRoot)

        #expect(try boot.prepare() == .upToDate)
        #expect(fileTree(at: boot.location.dataRoot) == before)
        #expect(fileTree(at: boot.location.backupsRoot).isEmpty)
    }

    // MARK: - 3. 升級：先備份，成功才更新版本號

    @Test func upgradeBacksUpWholeDataFolderBeforeMigrating() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        seedData(in: temp, version: 1)
        let boot = bootstrapper(in: temp, appVersion: 2, at: "2026-03-04T05:06:07Z")
        let before = fileTree(at: boot.location.dataRoot)

        let outcome = try boot.prepare()
        guard case .upgradePending(let from, let backup) = outcome else {
            Issue.record("預期是 upgradePending，實際是 \(outcome)")
            return
        }
        #expect(from == 1)
        #expect(backup.lastPathComponent == "v1-20260304-050607")
        // 備份 = 升級前的整個 Data，一個檔都不少。
        #expect(fileTree(at: backup) == before)
        // 備份放在 Backups 底下，不在 Data 裡面（不然備份會備份到自己）。
        #expect(backup.path(percentEncoded: false).hasPrefix(boot.location.backupsRoot.path(percentEncoded: false)))
        #expect(!backup.path(percentEncoded: false).hasPrefix(boot.location.dataRoot.path(percentEncoded: false)))
        // SwiftData 還沒升級完，版本號先不動。
        #expect(try boot.storedVersion() == 1)

        try boot.finishUpgrade()
        #expect(try boot.storedVersion() == 2)
    }

    @Test func upgradeKeepsGoingWhenTwoBackupsLandOnTheSameSecond() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        seedData(in: temp, version: 1)
        let boot = bootstrapper(in: temp, appVersion: 2)

        let first = try boot.makeBackup(ofVersion: 1)
        let second = try boot.makeBackup(ofVersion: 1)
        #expect(first != second)
        #expect(second.lastPathComponent.hasSuffix("-2"))
    }

    // MARK: - 4. 舊版 app 遇到新格式：還原自己這一版的備份

    @Test func olderAppRestoresItsOwnLatestBackup() throws {
        let temp = TempDirectory()
        defer { temp.remove() }

        // 兩份 v1 備份（要挑比較新的那份）＋一份 v0 的備份（不該被選到）。
        temp.writeFile("Backups/v1-20260101-000000/format-version.json", contents: "{\"formatVersion\":1}")
        temp.writeFile("Backups/v1-20260101-000000/app.store", contents: "舊的 v1 備份")
        temp.writeFile("Backups/v1-20260301-120000/format-version.json", contents: "{\"formatVersion\":1}")
        temp.writeFile("Backups/v1-20260301-120000/app.store", contents: "最新的 v1 備份")
        temp.writeFile("Backups/v1-20260301-120000/Files/photo.txt", contents: "v1 的使用者檔案")
        temp.writeFile("Backups/v0-20251201-000000/format-version.json", contents: "{\"formatVersion\":0}")

        // 現在磁碟上的資料是 v2（比 app 新）。
        seedData(in: temp, version: 2, extraFile: "新版才有的檔案.txt")
        let boot = bootstrapper(in: temp, appVersion: 1, at: "2026-04-05T06:07:08Z")
        let newerData = fileTree(at: boot.location.dataRoot)

        let outcome = try boot.prepare()
        guard case .restoredFromBackup(let unreadable, let restoredFrom, let setAside) = outcome else {
            Issue.record("預期是 restoredFromBackup，實際是 \(outcome)")
            return
        }
        #expect(unreadable == 2)
        #expect(restoredFrom.lastPathComponent == "v1-20260301-120000")
        #expect(setAside.lastPathComponent == "unreadable-v2-20260405-060708")

        // Data 換成備份的內容。
        #expect(fileTree(at: boot.location.dataRoot) == fileTree(at: restoredFrom))
        // 讀不懂的那份資料沒有被刪掉，只是移到 Backups。
        #expect(fileTree(at: setAside) == newerData)
        // 備份本身也還在（是複製回去，不是搬回去）。
        #expect(FileManager.default.fileExists(atPath: restoredFrom.path(percentEncoded: false)))
        // 留下旗標，畫面要顯示白話提示。
        #expect(boot.hasRestoredNotice)

        boot.clearRestoredNotice()
        #expect(!boot.hasRestoredNotice)
        // 還原完就是正常的同版本狀態。
        #expect(try boot.prepare() == .upToDate)
    }

    // MARK: - 5. 舊版 app 遇到新格式，但沒有備份：什麼都不動

    @Test func olderAppWithoutBackupTouchesNothingAndStartsReadOnly() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        seedData(in: temp, version: 3)
        // 只有別的版本的備份，沒有這一版（v1）的。
        temp.writeFile("Backups/v2-20260101-000000/format-version.json", contents: "{\"formatVersion\":2}")
        let boot = bootstrapper(in: temp, appVersion: 1)
        let before = fileTree(at: boot.location.dataRoot)
        let backupsBefore = fileTree(at: boot.location.backupsRoot)

        let outcome = try boot.prepare()
        #expect(outcome == .newerDataWithoutBackup(storedVersion: 3))
        #expect(!outcome.opensStoreOnDisk)
        #expect(fileTree(at: boot.location.dataRoot) == before)
        #expect(fileTree(at: boot.location.backupsRoot) == backupsBefore)
        #expect(!boot.hasRestoredNotice)
    }

    @Test func backupWithWrongVersionInsideIsIgnored() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        // 名字叫 v1，裡面其實是 v2：不可信，不拿來還原。
        temp.writeFile("Backups/v1-20260101-000000/format-version.json", contents: "{\"formatVersion\":2}")
        seedData(in: temp, version: 2)
        let boot = bootstrapper(in: temp, appVersion: 1)

        #expect(try boot.prepare() == .newerDataWithoutBackup(storedVersion: 2))
    }

    // MARK: - 版本號檔不見或壞掉

    @Test func dataWithoutVersionFileIsTreatedAsOldestAndBackedUp() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        temp.writeFile("Data/app.store", contents: "沒有版本號的舊資料")
        let boot = bootstrapper(in: temp, appVersion: 1)

        let outcome = try boot.prepare()
        guard case .upgradePending(let from, let backup) = outcome else {
            Issue.record("預期是 upgradePending，實際是 \(outcome)")
            return
        }
        #expect(from == 0)
        #expect(backup.lastPathComponent.hasPrefix("v0-"))
    }

    // MARK: - 整條路：升級 → 加資料 → 退回舊版

    @Test func rollingBackAcrossAnUpgradeGivesBackExactlyThePreUpgradeData() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        seedData(in: temp, version: 1)
        let beforeUpgrade = fileTree(at: DataLocation(appRoot: temp.url).dataRoot)

        // 新版 app 啟動：備份 → 升級 → 更新版本號 → 使用者又存了新東西。
        let newApp = bootstrapper(in: temp, appVersion: 2, at: "2026-05-05T05:05:05Z")
        _ = try newApp.prepare()
        try newApp.finishUpgrade()
        temp.writeFile("Data/Files/升級後才有的.txt", contents: "升級後新增的資料")

        // 使用者說「回到上一版」，舊版 app 啟動。
        let oldApp = bootstrapper(in: temp, appVersion: 1, at: "2026-06-06T06:06:06Z")
        let outcome = try oldApp.prepare()
        guard case .restoredFromBackup = outcome else {
            Issue.record("預期是 restoredFromBackup，實際是 \(outcome)")
            return
        }
        #expect(fileTree(at: oldApp.location.dataRoot) == beforeUpgrade)
        #expect(oldApp.hasRestoredNotice)
    }
}

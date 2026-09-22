import Foundation
import SwiftData
import Testing
@testable import VibeApp

/// 資料層和資料庫接得起來嗎？（§6 高風險改動：「存資料」一定要有的測試）
@MainActor
struct DataStackTests {

    @Test func dataSurvivesClosingAndReopeningTheStore() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        let location = DataLocation(appRoot: temp.url)
        let boot = DataBootstrapper(location: location, appVersion: DataFormat.currentVersion)
        #expect(try boot.prepare() == .firstLaunch)

        do {
            // 第一次打開：存一筆。
            let container = try DataStack.makeContainer(at: location)
            container.mainContext.insert(Entry(title: "買牛奶"))
            try container.mainContext.save()
        }

        // 重建儲存層＝模擬把 app 關掉再打開。
        let reopened = try DataStack.makeContainer(at: location)
        let entries = try reopened.mainContext.fetch(FetchDescriptor<Entry>())
        #expect(entries.count == 1)
        #expect(entries.first?.title == "買牛奶")
        // 資料庫確實開在資料根目錄裡。
        #expect(FileManager.default.fileExists(atPath: location.storeURL.path(percentEncoded: false)))
    }

    @Test func formatVersionMatchesTheNumberOfSchemas() {
        // 新增了 schema 卻忘了把 DataFormat.currentVersion 加 1 的話，這裡會失敗。
        #expect(DataFormat.currentVersion == AppMigrationPlan.schemas.count)
        #expect(AppMigrationPlan.schemas.last?.versionIdentifier == LatestSchema.versionIdentifier)
        #expect(LatestSchema.versionIdentifier.major == DataFormat.currentVersion)
    }
}

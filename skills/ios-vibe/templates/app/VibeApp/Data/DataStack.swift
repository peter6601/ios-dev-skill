// vibe-boundaries: allow store-setup — 資料層本身：全 app 只有這裡可以開 SwiftData 資料庫。
//
// 資料庫固定開在資料根目錄（DataLocation.storeURL），不用 SwiftData 的預設位置，
// 備份與還原才有辦法「複製一個資料夾就等於複製全部資料」。
// cloudKitDatabase 明講 .none：v1 的 app 不連網，資料不離開這支手機。

import Foundation
import SwiftData

nonisolated enum DataStack {
    static func schema() -> Schema {
        Schema(versionedSchema: LatestSchema.self)
    }

    /// 正式用的資料庫：開在資料根目錄，需要升級時由 AppMigrationPlan 處理。
    static func makeContainer(at location: DataLocation) throws -> ModelContainer {
        let schema = schema()
        let configuration = ModelConfiguration(
            schema: schema,
            url: location.storeURL,
            allowsSave: true,
            cloudKitDatabase: .none
        )
        return try ModelContainer(for: schema, migrationPlan: AppMigrationPlan.self, configurations: [configuration])
    }

    /// 只存在記憶體裡的資料庫：預覽用，以及「讀不懂又沒備份」時的空白唯讀模式用。
    static func makeInMemoryContainer() throws -> ModelContainer {
        let schema = schema()
        let configuration = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: true,
            allowsSave: true,
            cloudKitDatabase: .none
        )
        return try ModelContainer(for: schema, configurations: [configuration])
    }
}

// 資料長什麼樣子（SwiftData）。
//
// 要新增欄位或新增一種資料時的做法（v1 只允許這兩種）：
//   1. 複製 AppSchemaV1，改成 AppSchemaV2，versionIdentifier 改成 (2, 0, 0)
//   2. 新欄位一定要有預設值，舊資料才升得上來
//   3. 把 V2 放進 AppMigrationPlan.schemas，並加一個 .lightweight 的 MigrationStage
//   4. LatestSchema 指向 V2，DataFormat.currentVersion 加 1
//
// 不要改名、刪欄位、改型別、拆開或合併資料種類。

import Foundation
import SwiftData

enum AppSchemaV1: VersionedSchema {
    nonisolated static var versionIdentifier: Schema.Version { Schema.Version(1, 0, 0) }

    nonisolated static var models: [any PersistentModel.Type] { [Entry.self] }

    /// 入門用的一筆紀錄。真正要做的 app 就是從這裡開始長出來的。
    @Model
    final class Entry {
        var title: String = ""
        var createdAt: Date = Date.now

        init(title: String, createdAt: Date = .now) {
            self.title = title
            self.createdAt = createdAt
        }
    }
}

/// 目前最新的 schema。新增版本時改這裡。
typealias LatestSchema = AppSchemaV1

/// 程式裡一律用這個名字，不要直接寫 AppSchemaV1.Entry。
typealias Entry = LatestSchema.Entry

enum AppMigrationPlan: SchemaMigrationPlan {
    nonisolated static var schemas: [any VersionedSchema.Type] { [AppSchemaV1.self] }

    nonisolated static var stages: [MigrationStage] { [] }
}

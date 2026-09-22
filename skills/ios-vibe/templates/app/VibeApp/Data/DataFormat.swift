// 資料格式的版本號。
//
// 什麼時候要加 1：在 AppSchema.swift 新增一個 VersionedSchema（也就是新增欄位或新增資料種類）時，
// 把新的 schema 放進 AppMigrationPlan.schemas，然後把這裡加 1。兩邊對不上時，
// DataFormatTests 會直接讓測試失敗，提醒你漏改。
//
// v1 只允許「新增」這一類變更（新增欄位要有預設值、或新增資料種類）。
// 改名、刪欄位、改型別、拆開或合併資料種類都不允許——那類變更失敗時資料救不回來。

import Foundation

nonisolated enum DataFormat {
    /// 這一版 app 看得懂的資料格式版本。
    static let currentVersion = 1
}

/// 寫在資料根目錄裡的版本號檔案內容。
nonisolated struct DataFormatFile: Codable, Equatable, Sendable {
    var formatVersion: Int
}

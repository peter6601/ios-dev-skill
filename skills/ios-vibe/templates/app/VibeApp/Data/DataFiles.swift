// vibe-boundaries: allow file-io — 資料層本身：這是全 app 唯一可以寫檔的入口。
//
// 使用者產生的檔案（照片副本、匯出的檔案……）只能透過這裡存取，
// 這樣備份時複製整個資料根目錄就一定完整，不會漏掉散落在別處的檔案。
// 其他地方要寫檔時，不要自己組路徑，跟 AppLaunch 要 DataFiles。

import Foundation

nonisolated struct DataFiles: Sendable {
    /// 使用者檔案的根目錄（資料根目錄底下的 Files）。
    let root: URL
    /// 唯讀模式：資料讀不懂又沒備份時，只讓讀、不讓寫。
    var isReadOnly: Bool = false

    /// FileManager 本身不是 Sendable，所以不當成存起來的屬性。
    private var fileManager: FileManager { .default }

    enum FileError: Error, Equatable {
        /// 路徑不合法：絕對路徑、`..`、空字串都不接受。
        case invalidPath(String)
        /// 目前是唯讀模式。
        case readOnly
    }

    /// 把相對路徑換成真正的位置，順便擋掉想跑出資料根目錄的路徑。
    func url(for relativePath: String) throws -> URL {
        let trimmed = relativePath.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty,
              !trimmed.hasPrefix("/"),
              !trimmed.hasPrefix("~"),
              !trimmed.contains("\0") else {
            throw FileError.invalidPath(relativePath)
        }
        let components = trimmed.split(separator: "/", omittingEmptySubsequences: true)
        guard !components.isEmpty, !components.contains(where: { $0 == ".." || $0 == "." }) else {
            throw FileError.invalidPath(relativePath)
        }

        let candidate = components
            .reduce(root) { $0.appending(path: String($1), directoryHint: .notDirectory) }
            .standardizedFileURL
        let rootPath = root.standardizedFileURL.path(percentEncoded: false)
        guard candidate.path(percentEncoded: false).hasPrefix(rootPath.hasSuffix("/") ? rootPath : rootPath + "/") else {
            throw FileError.invalidPath(relativePath)
        }
        return candidate
    }

    @discardableResult
    func write(_ data: Data, to relativePath: String) throws -> URL {
        guard !isReadOnly else { throw FileError.readOnly }
        let url = try url(for: relativePath)
        try fileManager.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        try data.write(to: url, options: .atomic)
        return url
    }

    func read(_ relativePath: String) throws -> Data {
        try Data(contentsOf: url(for: relativePath))
    }

    func exists(_ relativePath: String) -> Bool {
        guard let url = try? url(for: relativePath) else { return false }
        return fileManager.fileExists(atPath: url.path(percentEncoded: false))
    }

    func remove(_ relativePath: String) throws {
        guard !isReadOnly else { throw FileError.readOnly }
        let url = try url(for: relativePath)
        guard fileManager.fileExists(atPath: url.path(percentEncoded: false)) else { return }
        try fileManager.removeItem(at: url)
    }

    /// 列出某個子資料夾裡的檔名（不遞迴）。
    func list(in relativeDirectory: String = "") throws -> [String] {
        let directory = relativeDirectory.isEmpty ? root : try url(for: relativeDirectory)
        let names = (try? fileManager.contentsOfDirectory(atPath: directory.path(percentEncoded: false))) ?? []
        return names.filter { !$0.hasPrefix(".") }.sorted()
    }
}

extension DataFiles {
    /// 預覽用：指到暫存資料夾而且唯讀，SwiftUI 預覽不會碰到真的資料。
    static func preview() -> DataFiles {
        DataFiles(
            root: FileManager.default.temporaryDirectory.appending(path: "VibeAppPreview", directoryHint: .isDirectory),
            isReadOnly: true
        )
    }
}

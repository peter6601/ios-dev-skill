import Foundation

/// 測試用的暫存資料夾：每個測試一個，用完就刪，永遠不會碰到真的 app 資料。
struct TempDirectory {
    let url: URL

    init() {
        url = FileManager.default.temporaryDirectory
            .appending(path: "vibe-tests-\(UUID().uuidString)", directoryHint: .isDirectory)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
    }

    func remove() {
        try? FileManager.default.removeItem(at: url)
    }

    /// 在這個暫存資料夾裡建一個檔，內容就是字串本身。
    @discardableResult
    func writeFile(_ relativePath: String, contents: String) -> URL {
        let fileURL = url.appending(path: relativePath, directoryHint: .notDirectory)
        try? FileManager.default.createDirectory(
            at: fileURL.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try? Data(contents.utf8).write(to: fileURL, options: .atomic)
        return fileURL
    }
}

/// 把一個資料夾裡的檔案列成「相對路徑 → 內容」，用來比對備份和原本的資料一不一樣。
func fileTree(at root: URL) -> [String: String] {
    var result: [String: String] = [:]
    let rootPath = root.standardizedFileURL.path(percentEncoded: false)
    guard let enumerator = FileManager.default.enumerator(atPath: rootPath) else { return result }
    for case let relative as String in enumerator {
        let fileURL = root.appending(path: relative, directoryHint: .notDirectory)
        var isDirectory: ObjCBool = false
        guard FileManager.default.fileExists(atPath: fileURL.path(percentEncoded: false), isDirectory: &isDirectory),
              !isDirectory.boolValue,
              let data = try? Data(contentsOf: fileURL) else { continue }
        result[relative] = String(decoding: data, as: UTF8.self)
    }
    return result
}

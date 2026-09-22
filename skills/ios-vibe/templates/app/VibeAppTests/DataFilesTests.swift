import Foundation
import Testing
@testable import VibeApp

/// 使用者產生的檔案只能透過 DataFiles 存，而且只能存在資料根目錄底下。
struct DataFilesTests {

    @Test func writeThenReadRoundTrips() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        let files = DataFiles(root: temp.url.appending(path: "Files", directoryHint: .isDirectory))

        let written = try files.write(Data("哈囉".utf8), to: "notes/first.txt")
        #expect(written.path(percentEncoded: false).contains("/Files/notes/first.txt"))
        #expect(String(decoding: try files.read("notes/first.txt"), as: UTF8.self) == "哈囉")
        #expect(files.exists("notes/first.txt"))
        #expect(try files.list(in: "notes") == ["first.txt"])

        try files.remove("notes/first.txt")
        #expect(!files.exists("notes/first.txt"))
    }

    @Test(arguments: ["../跑出去.txt", "/etc/passwd", "~/Documents/x.txt", "", "  ", "a/../../b.txt"])
    func rejectsPathsThatLeaveTheDataRoot(path: String) {
        let temp = TempDirectory()
        defer { temp.remove() }
        let files = DataFiles(root: temp.url)

        #expect(throws: DataFiles.FileError.self) {
            try files.url(for: path)
        }
    }

    @Test func readOnlyModeRefusesWrites() throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        let files = DataFiles(root: temp.url, isReadOnly: true)

        #expect(throws: DataFiles.FileError.readOnly) {
            try files.write(Data("x".utf8), to: "a.txt")
        }
        #expect(throws: DataFiles.FileError.readOnly) {
            try files.remove("a.txt")
        }
    }
}

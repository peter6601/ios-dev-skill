import Foundation
import Testing
@testable import VibeApp

/// 不連網的第 2 層（執行期攔截）有沒有真的攔到。
/// 這裡把「攔到就 crash」換成「攔到就記一筆」，測試才跑得完。
///
/// 測試用的網址是 .invalid 結尾，就算攔截失效也連不出去。
@Suite(.serialized)
struct NetworkBlockerTests {

    /// 攔到的網址記在這裡（攔截是在別的執行緒發生的）。
    final class Recorder: @unchecked Sendable {
        private let lock = NSLock()
        private var storage: [URL] = []
        var urls: [URL] {
            lock.lock(); defer { lock.unlock() }
            return storage
        }
        func append(_ url: URL?) {
            guard let url else { return }
            lock.lock(); defer { lock.unlock() }
            storage.append(url)
        }
    }

    @Test func blocksRequestsFromTheSharedSession() async throws {
        let recorder = Recorder()
        NetworkBlocker.install { recorder.append($0) }
        defer { NetworkBlocker.uninstall() }

        let url = URL(string: "https://vibe-network-check.invalid/ping")!
        await #expect(throws: (any Error).self) {
            _ = try await URLSession.shared.data(from: url)
        }
        #expect(recorder.urls == [url])
    }

    @Test func blocksRequestsFromASessionMadeWithItsOwnConfiguration() async throws {
        let recorder = Recorder()
        NetworkBlocker.install { recorder.append($0) }
        defer { NetworkBlocker.uninstall() }

        let session = URLSession(configuration: .default)
        let url = URL(string: "https://vibe-network-check.invalid/custom")!
        await #expect(throws: (any Error).self) {
            _ = try await session.data(from: url)
        }
        #expect(recorder.urls == [url])
    }

    @Test func localFilesAreNotBlocked() async throws {
        let temp = TempDirectory()
        defer { temp.remove() }
        let fileURL = temp.writeFile("local.txt", contents: "本機檔案不算連網")

        let recorder = Recorder()
        NetworkBlocker.install { recorder.append($0) }
        defer { NetworkBlocker.uninstall() }

        let (data, _) = try await URLSession.shared.data(from: fileURL)
        #expect(String(decoding: data, as: UTF8.self) == "本機檔案不算連網")
        #expect(recorder.urls.isEmpty)
    }

    @Test func onlyTurnsOnWhenTheFlagIsThere() {
        #expect(NetworkBlocker.isRequested(environment: ["VIBE_BLOCK_NETWORK": "1"], arguments: []))
        #expect(NetworkBlocker.isRequested(environment: [:], arguments: ["--vibe-block-network"]))
        #expect(!NetworkBlocker.isRequested(environment: [:], arguments: []))
        #expect(!NetworkBlocker.isRequested(environment: ["VIBE_BLOCK_NETWORK": "0"], arguments: []))
    }
}

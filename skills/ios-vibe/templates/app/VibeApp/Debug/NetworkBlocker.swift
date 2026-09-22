#if DEBUG
// vibe-boundaries: allow urlsession — 這個檔案就是「不連網」的執行期攔截器，本身一定要碰 URLProtocol／URLSession。
//
// v1 的 app 不連網。UI 測試啟動 app 時會帶 VIBE_BLOCK_NETWORK=1，
// 這時候攔截器上線，app 只要發出任何網路請求就直接 crash，測試就會失敗。
//
// 這一整個檔案包在 #if DEBUG 裡，正式（Release）build 不含這段。
//
// 擋得到什麼：走 URLSession 的請求（含自訂 configuration 的 session）。
// 擋不到什麼：WKWebView、低階 socket／Network framework、系統行程代發的請求。
// 那幾種由 check-boundaries.py 掃字串、由相依白名單擋套件，三層合起來仍然只是盡力而為。

import Foundation
import Synchronization

nonisolated final class NetworkBlocker: URLProtocol {
    static let environmentKey = "VIBE_BLOCK_NETWORK"
    static let launchArgument = "--vibe-block-network"

    private static let handler = Mutex<(@Sendable (URL?) -> Void)?>(nil)

    /// 有帶旗標才上線。正式使用時不會帶，所以平常完全不影響 app。
    static func isRequested(environment: [String: String], arguments: [String]) -> Bool {
        environment[environmentKey] == "1" || arguments.contains(launchArgument)
    }

    static func installIfRequested(processInfo: ProcessInfo = .processInfo) {
        guard isRequested(environment: processInfo.environment, arguments: processInfo.arguments) else { return }
        install { url in
            fatalError("vibe: 攔到網路請求 \(url?.absoluteString ?? "（沒有網址）")")
        }
    }

    /// 測試可以換掉處理方式：記下來就好，不用真的 crash。
    static func install(onBlocked: @escaping @Sendable (URL?) -> Void) {
        handler.withLock { $0 = onBlocked }
        URLProtocol.registerClass(NetworkBlocker.self)
        SessionConfigurationHook.installOnce()
    }

    static func uninstall() {
        handler.withLock { $0 = nil }
        URLProtocol.unregisterClass(NetworkBlocker.self)
    }

    static var isInstalled: Bool {
        handler.withLock { $0 != nil }
    }

    // MARK: - URLProtocol

    override class func canInit(with request: URLRequest) -> Bool {
        guard isInstalled else { return false }
        // 本機檔案不算連網，放行。
        let scheme = request.url?.scheme?.lowercased()
        return scheme != "file" && scheme != "data"
    }

    override class func canInit(with task: URLSessionTask) -> Bool {
        guard let request = task.currentRequest ?? task.originalRequest else { return false }
        return canInit(with: request)
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let url = request.url
        Self.handler.withLock { $0 }?(url)
        client?.urlProtocol(self, didFailWithError: URLError(.notConnectedToInternet))
    }

    override func stopLoading() {}
}

/// `URLProtocol.registerClass` 只管得到 URLSession.shared。
/// 自己 new 一個 URLSession（`URLSession(configuration: .default)`）會繞過去，
/// 所以把 configuration 的預設值也換掉，讓它一出廠就帶著攔截器。
private nonisolated enum SessionConfigurationHook {
    private static let installed = Mutex<Bool>(false)

    static func installOnce() {
        let alreadyDone = installed.withLock { done -> Bool in
            if done { return true }
            done = true
            return false
        }
        guard !alreadyDone else { return }

        for selector in [
            #selector(getter: URLSessionConfiguration.default),
            #selector(getter: URLSessionConfiguration.ephemeral)
        ] {
            guard let original = class_getClassMethod(URLSessionConfiguration.self, selector),
                  let replacement = class_getClassMethod(
                    URLSessionConfiguration.self,
                    selector == #selector(getter: URLSessionConfiguration.default)
                        ? #selector(URLSessionConfiguration.vibeBlockedDefault)
                        : #selector(URLSessionConfiguration.vibeBlockedEphemeral)
                  ) else { continue }
            method_exchangeImplementations(original, replacement)
        }
    }
}

nonisolated extension URLSessionConfiguration {
    @objc nonisolated fileprivate class func vibeBlockedDefault() -> URLSessionConfiguration {
        // 互換之後，這個名字指向原本的 default。
        let configuration = vibeBlockedDefault()
        configuration.protocolClasses = [NetworkBlocker.self] + (configuration.protocolClasses ?? [])
        return configuration
    }

    @objc nonisolated fileprivate class func vibeBlockedEphemeral() -> URLSessionConfiguration {
        let configuration = vibeBlockedEphemeral()
        configuration.protocolClasses = [NetworkBlocker.self] + (configuration.protocolClasses ?? [])
        return configuration
    }
}
#endif

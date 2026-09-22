import SwiftData
import SwiftUI

/// 啟動結果決定第一個畫面：資料開得起來就進主畫面，開不起來就說清楚。
struct RootView: View {
    let launch: AppLaunch.Result

    var body: some View {
        switch launch {
        case .ready(let session):
            EntryListView()
                .environment(session)
                .modelContainer(session.container)
                .overlay(alignment: .bottom) {
                    NetworkBlockerMarker()
                }
        case .failed(let details):
            ContentUnavailableView {
                Label("資料打不開", systemImage: "exclamationmark.triangle")
            } description: {
                Text("資料沒有被刪掉。請把這段訊息交給協助你的人：\n\(details)")
            }
        case .hostingUnitTests:
            Color.clear
        }
    }
}

/// 測試用：帶著不連網旗標啟動時，放一個看不見的標記，讓 UI 測試確認攔截器真的上線了。
private struct NetworkBlockerMarker: View {
    var body: some View {
        #if DEBUG
        if NetworkBlocker.isInstalled {
            Color.clear
                .frame(width: 1, height: 1)
                .accessibilityElement()
                .accessibilityLabel("network blocker active")
                .accessibilityIdentifier("vibeNetworkBlockerActive")
        }
        #endif
    }
}

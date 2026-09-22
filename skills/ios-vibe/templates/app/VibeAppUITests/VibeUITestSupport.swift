// vibe-boundaries: allow uitest-launch — UI 測試唯一可以直接呼叫 launch() 的地方。
//
// UI 測試一律用這裡的方法啟動 app，啟動時才會帶著：
//   - VIBE_BLOCK_NETWORK=1：app 一發出網路請求就當掉，測試就失敗（不連網的第 2 層）
//   - VIBE_TEST_DATA      ：資料寫到測試專用的資料夾，碰不到使用者的真資料

import XCTest

extension XCUIApplication {

    enum TestData: String {
        /// 從乾淨的資料開始。
        case fresh
        /// 沿用上一次留下的資料（測「關掉再打開，資料還在嗎」）。
        case keep
    }

    /// 啟動 app，並確認不連網的攔截器真的上線了。
    @MainActor
    static func launchForVibeTest(data: TestData = .fresh, file: StaticString = #filePath, line: UInt = #line) -> XCUIApplication {
        let app = XCUIApplication()
        app.configureForVibeTest(data: data)
        app.launch()
        XCTAssertTrue(
            app.descendants(matching: .any)["vibeNetworkBlockerActive"].waitForExistence(timeout: 10),
            "不連網的攔截器沒有上線，這次 UI 測試擋不住網路請求",
            file: file,
            line: line
        )
        return app
    }

    /// 關掉再打開，資料沿用上一次的。
    @MainActor
    func relaunchForVibeTest(data: TestData = .keep) {
        terminate()
        configureForVibeTest(data: data)
        launch()
    }

    @MainActor
    private func configureForVibeTest(data: TestData) {
        launchEnvironment["VIBE_BLOCK_NETWORK"] = "1"
        launchEnvironment["VIBE_TEST_DATA"] = data.rawValue
    }
}

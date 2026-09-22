import XCTest

/// 主要流程：打開 app → 新增一筆 → 看得到 → 刪掉 → 不見了。
/// 每張試用卡出之前，這些測試都要全部重跑一次。
final class MainFlowUITests: XCTestCase {

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testAddThenDeleteAnEntry() throws {
        let app = XCUIApplication.launchForVibeTest()

        app.buttons["addEntryButton"].tap()

        let titleField = app.textFields["entryTitleField"]
        XCTAssertTrue(titleField.waitForExistence(timeout: 5))
        titleField.tap()
        titleField.typeText("Milk")
        app.buttons["saveEntryButton"].tap()

        let row = app.staticTexts["Milk"]
        XCTAssertTrue(row.waitForExistence(timeout: 5), "新增完應該看得到這一筆")

        // 要對整列滑：文字元素只有字那麼寬，對它滑的距離不夠觸發 swipe action。
        let cell = app.cells.containing(NSPredicate(format: "label == %@", "Milk")).firstMatch
        XCTAssertTrue(cell.waitForExistence(timeout: 5), "新增完應該有這一列")
        cell.swipeLeft()

        let deleteButton = app.buttons["deleteEntryButton"]
        XCTAssertTrue(deleteButton.waitForExistence(timeout: 5), "向左滑之後應該出現刪除按鈕")
        deleteButton.tap()
        XCTAssertTrue(row.waitForNonExistence(timeout: 5), "刪掉之後就不該再看到")
    }

    /// 存資料類的改動一定要有的測試：關掉 app 再打開，資料還在。
    @MainActor
    func testEntryIsStillThereAfterRelaunch() throws {
        let app = XCUIApplication.launchForVibeTest()

        app.buttons["addEntryButton"].tap()
        let titleField = app.textFields["entryTitleField"]
        XCTAssertTrue(titleField.waitForExistence(timeout: 5))
        titleField.tap()
        titleField.typeText("Keep me")
        app.buttons["saveEntryButton"].tap()
        XCTAssertTrue(app.staticTexts["Keep me"].waitForExistence(timeout: 5))

        app.relaunchForVibeTest()

        XCTAssertTrue(
            app.staticTexts["Keep me"].waitForExistence(timeout: 10),
            "把 app 關掉再打開，剛剛存的資料應該還在"
        )
    }
}

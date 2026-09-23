---
name: ios-investigate
description: >
  iOS 專用的系統化除錯流程。嚴格遵守「沒有找到 Root Cause 前禁止修 Code」的鐵律，
  分五階段進行：收集症狀 → 模式比對 → 假設驗證 → 實作修復 → 驗證回報。
  內建 iOS 常見 Bug Pattern 對照表（Swift Concurrency data race、UIKit main thread violation、
  StoreKit receipt 異常、Memory leak / retain cycle、Core Data concurrency、
  Multipeer Connectivity 斷線、Apple Translation Framework 限制等）。
  觸發場景：使用者說「debug」、「除錯」、「這個 bug」、「為什麼 crash」、「查一下這個問題」、
  「investigate」、「root cause」、「崩潰」、「閃退」、「這裡怪怪的」、「行為不對」，
  或在描述任何 iOS app 異常行為時主動建議使用。
  即使使用者只是貼了一段 crash log 或 error message，只要上下文涉及 iOS 開發，都應觸發此 skill。
---

# iOS 系統化除錯流程

## 概覽

這個 skill 將 iOS 除錯從「猜測→亂改→祈禱」升級為結構化的工程方法。
核心哲學來自 gstack 的 investigate skill，針對 Swift / SwiftUI / UIKit / StoreKit / 
Multipeer Connectivity 等 iOS 技術棧深度客製。

語言採中英混合：主體用繁體中文，技術術語、class 名稱、method 名稱、error message 保留英文原文。

---

## 鐵律 Iron Law

<!-- touchpoint: ios-investigate-001 kind=gate -->
**沒有找到 Root Cause 前，禁止修改任何 Code。**

修症狀只會製造打地鼠式的 debug 循環。每一次沒有解決根因的修改，都讓下一個 bug 更難找。
先找到根因，再動手修。

---

## Phase 1：症狀收集 Symptom Collection

在形成任何假設之前，先完整收集證據。

### 1.1 讀取錯誤訊息

仔細閱讀完整的 error message、crash log、stack trace。特別注意：

- **Crash Report**：Exception Type、Exception Codes、Triggered by Thread
- **Console Log**：`[error]`、`[fault]` 級別的 os_log 輸出
- **Xcode Issue Navigator**：Runtime warnings（紫色標記）
<!-- touchpoint: ios-investigate-010 kind=engineering -->
- **線上 crash／效能問題**（使用者裝置上發生、本機重現不了）：有 Xcode MCP（Xcode 27+）時先撈 Apple 後台資料——`GetTopCrashIssues`（近 14 天、依受影響裝置數排序）→ 挑簽名用 `GetCrashIssueLogs` 取 crash log 與 Apple 的分析建議；hang、耗電等用 `GetTopFieldPerformanceIssues`／`GetFieldPerformanceIssueLogs`。`is_beta` 可分開 TestFlight 與 App Store。沒有 Xcode MCP 時請使用者從 Xcode Organizer 匯出 `.crash` 貼上

### 1.2 讀取相關程式碼

從症狀反向追蹤程式碼路徑。使用 Grep 找出所有相關引用，Read 理解邏輯流程。

重點追蹤：
- 出錯的 function / method 的完整呼叫鏈
- 相關的 State 管理流程（`@State`、`@Observable`、`@Published`）
- 非同步操作的 lifecycle（`Task`、`async/await`、`Combine` pipeline）

### 1.3 查看近期變更

```bash
# 查看受影響檔案的近期修改
git log --oneline -20 -- <affected-files>

# 如果是 regression，找出哪個 commit 引入問題
git log --oneline --since="1 week ago" -- <affected-directory>
```

問自己：這之前是正常的嗎？什麼時候壞的？如果是 regression，root cause 就在 diff 裡。

### 1.4 重現問題

<!-- touchpoint: ios-investigate-002 kind=product -->
能否穩定重現？記錄：
- 重現步驟（越精確越好）
- 重現率（100%？偶發？特定條件？）
- 環境（Simulator vs 實機、iOS 版本、裝置型號）
- **Sandbox vs Production**（StoreKit 相關問題必須記錄）

如果無法重現，回到收集更多證據，不要猜。

**輸出**：`Root Cause 假設：...` — 一個具體、可驗證的聲明，說明什麼壞了、為什麼壞了。

---

## Phase 2：iOS Bug Pattern 比對

將症狀與以下常見 iOS bug pattern 比對：

| Pattern | 典型症狀 | 去哪裡找 |
|---------|---------|---------|
| **Swift Concurrency Data Race** | `EXC_BAD_ACCESS`、間歇性 crash、Thread Sanitizer 警告 | 多個 Task 同時存取 non-isolated mutable state；Actor 邊界違規 |
| **Main Thread Violation** | 紫色 runtime warning、UI 卡頓或不更新、`[UIView setNeedsLayout] must be used from main thread` | 在 background thread 操作 UI；`@MainActor` 漏標 |
| **Retain Cycle / Memory Leak** | 記憶體持續增長、`deinit` 不被呼叫、Instruments Leaks 顯示 leak | Closure 捕獲 `self`、delegate 未用 `weak`、`Task` 在 `deinit` 後仍持有 reference |
| **StoreKit Receipt 異常** | 購買成功但點數/訂閱沒入帳、跨 Apple ID 資料殘留、sandbox receipt 混 production | StoreKit 1 receipt 跨 Apple ID 持久化、`originalTransactionId` 混淆、Server Notification V2 漏處理 |
| **Task Lifecycle 問題** | `CancellationError`、`BUG_IN_CLIENT_OF_LIBMALLOC`、Unit Test 間歇性失敗 | `Task` 在 view/VM 的 `deinit` 後仍執行；Task 沒有被正確 cancel |
| **NSInternalInconsistencyException** | `UIAlertController` 相關 crash、`UITableView` / `UICollectionView` section mismatch | 在非預期時機 present/dismiss VC；data source 與 UI state 不同步 |
| **Core Data Concurrency** | `NSInternalInconsistencyException`、data corruption、intermittent crash | 跨 context 存取 managed object；main context 在 background thread 操作 |
| **Multipeer Connectivity 斷線** | Session disconnect、peer 找不到、資料傳輸中斷 | MCSession state 管理不當、未處理 `notConnected` callback、background 限制 |
| **Apple Translation Framework 限制** | 翻譯失敗、語言對不支援、iOS 版本不相容 | iOS 18+ 限定、離線模型未下載、不支援的語言對 fallback 沒處理 |
| **Keychain / 帳號歸戶** | 登入後資料混亂、多帳號切換殘留、subscription 歸屬錯誤 | Keychain 存取權限、App Group 設定、`originalTransactionId` 歸戶邏輯 |
| **SwiftUI State 異常** | View 不更新、State 被意外重置、NavigationStack 行為怪異 | `@State` 放錯位置（應在 parent）、`@Observable` 未觸發 view update、`id()` modifier 導致 view recreation |
| **Configuration Drift** | 本機正常 CI 失敗、Simulator 正常實機 crash | Build Configuration 差異、Provisioning Profile、entitlements、環境變數 |

額外檢查：
- 使用者指定的、或 repo 裡真的存在的已知問題清單（TODO／ROADMAP／issue tracker；沒有就跳過）
- `git log` 同區域的歷史修復紀錄 — **同一批檔案反覆出 bug 是架構問題的訊號**，不是巧合

---

## Phase 3：假設驗證 Hypothesis Testing

在寫任何修復之前，先驗證假設。

### 3.1 確認假設

在懷疑的根因位置加入臨時 log、assertion、或 debug output：

```swift
// 範例：驗證是否為 main thread violation
print("⚠️ DEBUG: Current thread: \(Thread.current), isMain: \(Thread.isMainThread)")

// 範例：驗證 Task lifecycle
print("⚠️ DEBUG: Task started, self is \(type(of: self)) at \(Unmanaged.passUnretained(self).toOpaque())")

// 範例：驗證 StoreKit transaction
print("⚠️ DEBUG: originalTransactionId=\(tx.originalID), currentId=\(tx.id), productId=\(tx.productID)")
```

執行重現步驟。證據是否符合假設？

### 3.2 假設錯誤時

回到 Phase 1，收集更多證據。**不要猜。**

### 3.3 三振出局規則 3-Strike Rule

<!-- touchpoint: ios-investigate-003 kind=engineering -->
如果 3 個假設都失敗了，**停下來**。向使用者提問：

```
3 個假設都測試了，沒有一個符合。這可能是架構層級的問題，不是單純的 bug。

A) 繼續調查 — 我有新假設：[描述]
B) 升級給人工 review — 這需要熟悉系統的人來看
C) 加 instrumentation 等待 — 在問題區域埋 log，下次觸發時收集資料
```

### 紅旗 Red Flags

看到以下任一項，放慢腳步：

- **「先這樣修」** — 沒有「先這樣」。修對或升級，沒有第三選項。
- **還沒 trace data flow 就提修法** — 你在猜。
- **每次修完又冒出新問題** — 問題在錯誤的層級，不是錯誤的 code。

---

## Phase 4：實作修復 Implementation

Root cause 確認後：

### 4.1 修根因，不修症狀

最小的改動消除實際問題。

### 4.2 最小 Diff

改最少的檔案、最少的行數。抵抗順手重構旁邊 code 的衝動。

### 4.3 寫 Regression Test

寫一個測試：
- **沒有修復時會失敗**（證明測試有意義）
- **有修復後會通過**（證明修復有效）

iOS 測試重點：
```swift
// XCTest 範例
func testSubscriptionAttributionAfterAccountSwitch() async throws {
    // Arrange: 模擬帳號切換情境
    // Act: 執行購買流程
    // Assert: 驗證 originalTransactionId 正確歸戶
}
```

### 4.4 跑完整測試

```bash
# 跑 test suite 並貼出結果
xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16' | xcpretty
```

不允許任何 regression。

### 4.5 大範圍修改警示

<!-- touchpoint: ios-investigate-004 kind=engineering -->
如果修改超過 5 個檔案，先向使用者確認：

```
這次修復影響了 N 個檔案。對一個 bug fix 來說 blast radius 偏大。

A) 繼續 — root cause 確實跨越這些檔案
B) 拆分 — 先修 critical path，其餘延後
C) 重新思考 — 可能有更精準的做法
```

---

## Phase 5：驗證與回報 Verification & Report

### 5.1 重新驗證

<!-- touchpoint: ios-investigate-005 kind=gate -->
用原始的重現步驟確認 bug 已修復。**這不是可選步驟。**

跑測試 suite 並貼出結果。

### 5.2 結構化 Debug Report

```
DEBUG REPORT
════════════════════════════════════════
症狀 Symptom:      [使用者觀察到的現象]
根因 Root Cause:   [實際出了什麼問題、為什麼]
修復 Fix:          [改了什麼，附 file:line 參考]
證據 Evidence:     [測試輸出、重現結果證明修復有效]
回歸測試 Regression Test: [新測試的 file:line]
相關 Related:      [已知問題清單的對應項、同區域歷史 bug、架構筆記]
狀態 Status:       DONE | DONE_WITH_CONCERNS | BLOCKED
════════════════════════════════════════
```

---

## 重要規則 Important Rules

  <!-- touchpoint: ios-investigate-006 kind=engineering -->
- **3 次修復嘗試失敗 → 停下來質疑架構。** 不是假設錯了，是架構有問題。
- **無法驗證的修復不要提交。** 如果不能重現並確認，不要 ship。
- **永遠不要說「這應該能修好」。** 驗證並證明。跑測試。
  <!-- touchpoint: ios-investigate-007 kind=engineering -->
- **修改超過 5 個檔案 → 向使用者確認** blast radius 再繼續。

### 完成狀態定義

<!-- touchpoint: ios-investigate-008 kind=engineering -->
<!-- touchpoint: ios-investigate-009 kind=mixed -->
| 狀態 | 定義 |
|------|------|
| **DONE** | Root cause 找到、修復完成、regression test 已寫、所有測試通過 |
| **DONE_WITH_CONCERNS** | 已修復但無法完全驗證（如：間歇性 bug、需要 staging 環境） |
| **BLOCKED** | 調查後 root cause 不明確，已升級 |
| **NEEDS_CONTEXT** | 缺少繼續所需的資訊，已說明需要什麼 |

---

## iOS 除錯工具快速參考

根據症狀選擇合適的工具：

| 症狀 | 首選工具 |
|------|---------|
| Crash / EXC_BAD_ACCESS | Zombie Objects + Address Sanitizer |
| Memory Leak | Instruments Leaks + Memory Graph Debugger |
| Data Race | Thread Sanitizer (TSan) |
| Main Thread Violation | Main Thread Checker（Xcode 預設開啟） |
| UI 不更新 | `Self._printChanges()` (SwiftUI) + Xcode Preview |
| 網路問題 | Charles Proxy / Instruments Network |
| StoreKit 問題 | StoreKit Configuration File + Sandbox 帳號 + Server Notification 日誌 |
| Core Data | `-com.apple.CoreData.SQLDebug 1` launch argument |
| Multipeer Connectivity | 實機雙機測試 + Console.app 過濾 MCSession log |

---

## 附錄：常見陷阱速查

### Swift Concurrency 陷阱
- `@MainActor` 標記的 class 中，non-isolated method 仍可能在 background 執行
- `Task { }` 繼承 actor context，`Task.detached { }` 不繼承
- `nonisolated` function 中存取 actor-isolated property 會在 Swift 6 報錯

### StoreKit 陷阱
- StoreKit 1 的 receipt 會跨 Apple ID 持久化在裝置上
- Sandbox 環境的 subscription 自動續訂時間表跟 production 不同
- `Transaction.currentEntitlements` 只回傳 StoreKit 2 的交易

### SwiftUI State 陷阱
- `@State` 放在 child view 會在 parent 重繪時被重置（要放 parent 或用 `@StateObject`）
- `@Observable` 的 computed property 不會觸發 view update
- `.task` modifier 會在 view identity 改變時自動 cancel 並重新執行

---
name: ios-review
description: >
  iOS 專案的 Pre-landing PR Review。分析 diff 中的 Swift Concurrency 安全性、
  Memory Leak / Retain Cycle、Main Thread Violation、StoreKit 正確性、SwiftUI State 管理、
  Accessibility、以及 App Store 審核風險。採用兩輪 Review（CRITICAL + INFORMATIONAL）與
  Fix-First 流程（能自動修的直接修、需要判斷的批次詢問）。
  觸發場景：使用者說「review」、「code review」、「PR review」、「幫我看一下 code」、
  「檢查這個 branch」、「pre-landing」、「review 這個 PR」、「上線前檢查」，
  或即將 merge / push 時主動建議使用。
  即使使用者只是說「看一下」或「幫我 check」，只要上下文涉及 iOS code 變更，都應觸發此 skill。
---

# iOS Pre-Landing PR Review

## 概覽

這個 skill 對 iOS 專案的 branch diff 進行結構化 code review，專抓測試抓不到的結構性問題。
核心架構來自 gstack 的 `/review` skill，checklist 完全針對 Swift / SwiftUI / UIKit / 
StoreKit / Combine 技術棧重寫。

語言採中英混合：主體用繁體中文，技術術語保留英文原文。

---

## Step 0：偵測 Base Branch

確定此 PR 的目標分支，後續所有 diff 比對使用此分支。

1. 檢查是否已有 PR：`gh pr view --json baseRefName -q .baseRefName`
2. 如果沒有 PR，偵測 repo 預設分支：`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
3. 都失敗時 fallback 到 `develop`（git-flow 慣例），其次 `main`

---

## Step 1：Branch 檢查

```bash
CURRENT=$(git branch --show-current)
echo "Current branch: $CURRENT"
```

如果在 base branch 上 → 輸出「沒有東西可以 review — 你在 base branch 上」，停止。

```bash
git fetch origin <base> --quiet
git diff origin/<base> --stat
```

如果沒有 diff → 輸出相同訊息，停止。

---

## Step 2：Scope Drift 偵測

在 review code 品質之前，先確認：**有沒有做超過或少做？**

1. 讀取 commit messages：`git log origin/<base>..HEAD --oneline`
2. 讀取 TODOS.md / PR description（如果有的話）
3. 比對 `git diff origin/<base> --stat` 的檔案清單與宣稱的意圖

偵測：
- **Scope Creep**：改了與目的無關的檔案、順手重構
- **Missing Requirements**：宣稱要做但 diff 裡沒有的項目

輸出：
```
Scope Check: [CLEAN / DRIFT DETECTED / REQUIREMENTS MISSING]
Intent: <一行描述預期做什麼>
Delivered: <一行描述 diff 實際做了什麼>
[如有 drift: 列出每個超出範圍的變更]
[如有 missing: 列出每個未完成的需求]
```

這是 INFORMATIONAL — 不阻擋 review，繼續下一步。

---

## Step 3：取得 Diff

```bash
git fetch origin <base> --quiet
git diff origin/<base>
```

包含已 commit 和未 commit 的變更。

---

## Step 4：兩輪 Review

### 指令

Review `git diff origin/<base>` 的內容，依照以下 checklist 檢查。具體到 `file:line`，建議修法。
沒問題的就跳過。只標記真正的問題。

**兩輪掃描：**
- **Pass 1 (CRITICAL)：** 最高嚴重度，優先處理
- **Pass 2 (INFORMATIONAL)：** 較低嚴重度但仍需處理

---

### Pass 1 — CRITICAL

#### 1.1 Swift Concurrency 安全性

- **Data Race**：非 `Sendable` 型別跨越 actor boundary；mutable state 在多個 `Task` 中被存取但未用 actor 保護
- **Actor Isolation 違規**：non-isolated method 存取 actor-isolated property；`nonisolated` function 內意外存取 isolated state
- **`@MainActor` 漏標**：更新 UI 的 method / closure 未標記 `@MainActor`；`Task { }` 內假設繼承了 actor context 但實際沒有
- **`Task.detached` 危險使用**：`Task.detached` 內存取 self 或 actor-isolated state 而沒有 await
- **Structured Concurrency 洩漏**：`Task { }` 啟動後無人持有 reference 也無人 cancel（fire-and-forget without cleanup）

#### 1.2 Memory Management

- **Retain Cycle**：closure 捕獲 `self` 未使用 `[weak self]` 或 `[unowned self]`（特別是 escaping closure、Combine sink、NotificationCenter observer）
- **Task Lifecycle**：`Task` 在 View / ViewModel 的 `deinit` 後仍在執行；`task` 存在 property 但 `deinit` 未 cancel
- **Delegate Retain Cycle**：delegate property 未宣告為 `weak`
- **Timer Retain**：`Timer.scheduledTimer` 的 target 是 self 但未 invalidate

#### 1.3 Thread Safety

- **Main Thread Violation**：在非 main thread 操作 UIKit API（`UIView`、`UIViewController`、`UIAlertController` 等）
- **UI 更新不在 MainActor**：`@Published` property 在 background 被 set；`ObservableObject` 的 published property 在 background Task 內修改
- **Core Data Context 跨線程**：在建立 context 以外的 thread 存取 `NSManagedObject`

#### 1.4 StoreKit / IAP 正確性

- **Receipt 處理**：StoreKit 1 receipt 沒有考慮跨 Apple ID 持久化問題；購買後未驗證 receipt
- **Transaction 歸戶**：`originalTransactionId` 與 `transactionId` 混淆；subscription 歸戶邏輯沒有處理帳號切換
- **Entitlement 檢查**：只用 StoreKit 2 的 `Transaction.currentEntitlements`，沒有考慮 StoreKit 1 遷移用戶
- **Sandbox 差異**：有 sandbox-only 的邏輯 hardcode 在 production path 中

#### 1.5 Security

- **Hardcoded Secrets**：API key、token、password 直接寫在 code 中（應使用 Keychain 或 xcconfig + .gitignore）
- **HTTP 明文**：使用 `http://` 而非 `https://`（ATS 例外未經必要）
- **Keychain 存取**：敏感資料存在 `UserDefaults` 而非 Keychain
- **Log 洩漏**：`print()` 或 `os_log` 輸出 token / password / PII

---

### Pass 2 — INFORMATIONAL

#### 2.1 SwiftUI State 管理

- **`@State` 放錯位置**：`@State` 放在 child view 中但其值由 parent 控制（會在 parent 重繪時重置）
- **`@Observable` Computed Property**：computed property 不會觸發 view update，需要改成 stored property + 手動更新
- **不必要的 `@StateObject`**：在 iOS 17+ 用了 `@StateObject` + `ObservableObject` 而可以簡化為 `@State` + `@Observable`
- **`.id()` Modifier 濫用**：用 `.id()` 強制 view recreation，但實際應修正 state flow
- **`@EnvironmentObject` 遺失**：子 view 使用 `@EnvironmentObject` 但 preview / parent chain 中沒有 inject

#### 2.2 API / Networking

- **Error 未處理**：`try?` 吞掉 error 沒有 logging 或 fallback；`catch { }` 空 block
- **Missing Timeout**：`URLSession` request 沒有設定 `timeoutInterval`
- **Codable Fragility**：Codable struct 沒有 `CodingKeys` 或 custom `init(from:)` 處理 optional field；API response 新增欄位會 decode 失敗
- **Retry 無上限**：自動重試機制沒有 max retry count 或 exponential backoff

#### 2.3 Dead Code & Consistency

- **Unused Import**：`import` 了但沒有使用的 framework
- **Unreachable Code**：`return` / `throw` / `fatalError()` 之後的 code
- **注解過時**：comment 描述的行為與修改後的 code 不符
- **TODO / FIXME 殘留**：忘記清理的暫時 workaround
- **Version Mismatch**：PR title / commit message 與 VERSION / CHANGELOG 不一致

#### 2.4 Test Gaps

- **只測 Happy Path**：有正向測試但缺少 error case / edge case 測試
- **Async Test 不完整**：`XCTestExpectation` 或 `async` test 沒有等待完成
- **Mock 不 verify**：mock 物件沒有驗證呼叫次數或參數
- **UI Test 缺失**：新增的 user flow 沒有對應 UI test
- **缺少 Regression Test**：修 bug 但沒有寫重現此 bug 的測試

#### 2.5 Accessibility

- **缺少 Accessibility Label**：互動元素（按鈕、輸入框）沒有 `.accessibilityLabel`
- **Image 缺少描述**：`.accessibilityElement()` 沒有 label 或 image 沒標 `.accessibilityHidden(true)`
- **Touch Target 過小**：互動區域小於 44x44 pt
- **Dynamic Type 未支援**：hardcoded font size 而非使用 `.font(.body)` 等 Dynamic Type 支援的方式

#### 2.6 App Store Review 風險

- **Private API 呼叫**：使用 `_` 開頭的 framework API 或 `performSelector` 呼叫非公開 method
- **IDFA 未宣告**：使用 `ASIdentifierManager` 或 AdSupport 但 Info.plist 未宣告 `NSUserTrackingUsageDescription`
- **Background Mode 未必要**：宣告了 background mode（audio、location、fetch）但沒有實際使用
- **Clipboard 讀取**：啟動時讀取 `UIPasteboard` 但沒有 `UIPasteboardDetectionPattern` 保護（iOS 16+ 會跳系統提示）

#### 2.7 Naming & Swift Style

- **命名不一致**：同概念在不同地方用不同名稱（如 `userId` vs `userID` vs `user_id`）
- **Force Unwrap**：`!` 出現在非 `@IBOutlet` / `fatalError` 的 context；production code 不應 force unwrap
- **Magic Number**：裸數字散落在多處，應該用 named constant
- **Overlong Function**：單一 function 超過 50 行，應該拆分
- **Nested Closure Hell**：超過 3 層 closure 嵌套，考慮用 async/await 或拆成 method

---

## Step 5：Fix-First Review

**每一項發現都要有 action — 不只是報告。**

### 5a：分類每項發現

```
AUTO-FIX（直接修，不問）:           ASK（需要人類判斷）:
├─ Unused import                   ├─ Concurrency safety（actor boundary 變更）
├─ Unreachable code                ├─ StoreKit 歸戶邏輯
├─ 注解過時                         ├─ Security（Keychain、ATS）
├─ Force unwrap → optional chain   ├─ 架構 / 設計決策
├─ Missing `[weak self]`           ├─ 大型修改（>20 行）
│  （在明確的 escaping closure 中）  ├─ 移除功能
├─ Missing accessibility label     ├─ 影響使用者可見行為的變更
│  （當 label 可從 context 推斷）    └─ Enum completeness
├─ TODO/FIXME cleanup
└─ Naming inconsistency（純 rename）
```

**經驗法則**：如果修改是機械式的、資深工程師會不經討論直接改，就是 AUTO-FIX。
如果合理的工程師可能有不同意見，就是 ASK。

CRITICAL 發現傾向 ASK（風險較高）。INFORMATIONAL 發現傾向 AUTO-FIX（較機械式）。

### 5b：AUTO-FIX

直接套用修改。每項輸出一行：
```
[AUTO-FIXED] [file:line] 問題 → 做了什麼
```

### 5c：批次詢問 ASK 項目

如果有需要判斷的項目，用一次提問統一詢問：

```
自動修了 5 項。還有 2 項需要你判斷：

1. [CRITICAL] ViewModels/ChatViewModel.swift:87 — @Published property 在 background Task 被 set
   修法: 加 @MainActor 或用 MainActor.run { }
   → A) 修  B) 跳過

2. [INFORMATIONAL] Services/StoreKitManager.swift:142 — originalTransactionId 歸戶邏輯缺少帳號切換處理
   修法: 加入 currentUserID 比對
   → A) 修  B) 跳過

建議: 兩個都修 — #1 在 strict concurrency 下會 crash，#2 會導致訂閱歸錯帳號。
```

### 5d：套用使用者核准的修改

使用者選「修」的項目，套用修改並輸出結果。

---

## Step 6：驗證聲明

在產出最終 review 結果前：

- 如果你聲稱「這個 pattern 是安全的」→ 引用證明安全的具體行
- 如果你聲稱「這在別處有處理」→ 讀取並引用處理的 code
- 如果你聲稱「測試有覆蓋」→ 指名測試檔案和 method
- 絕不說「可能有處理」或「應該有測試」→ 驗證或標為未知

**防止合理化**：「這看起來沒問題」不是 finding。要嘛引用證據證明沒問題，要嘛標為未驗證。

---

## 輸出格式

```
iOS Pre-Landing Review: N issues (X critical, Y informational)
Branch: <branch-name> → <base-branch>
Scope: [CLEAN / DRIFT DETECTED]

**AUTO-FIXED:**
- [file:line] 問題 → 修法

**NEEDS INPUT:**
- [SEVERITY] [file:line] 問題描述
  修法: 建議修法

**Status: DONE | DONE_WITH_CONCERNS | BLOCKED**
```

如果沒有問題：`iOS Pre-Landing Review: No issues found. ✅`

---

## 重要規則

- **先讀完整個 diff 再發表意見。** 不要標記 diff 裡已經處理的問題。
- **Fix-first，不是唯讀 review。** AUTO-FIX 直接改，ASK 經使用者同意才改。絕不 commit / push / 開 PR — 那是 ship 的工作。
- **精簡。** 一行描述問題，一行寫修法。不要前言、不要摘要、不要「整體看起來不錯」。
- **只標記真正的問題。** 沒問題的就跳過。

---

## Suppressions — 不要標記以下情況

- `guard let self else { return }` 中的 `self` — 這是 Swift 標準模式
- `@IBOutlet` 的 force unwrap — Interface Builder 保證非 nil
- `fatalError()` / `preconditionFailure()` 中的 force unwrap — 本來就是要 crash
- Test code 中的 force unwrap（`XCTUnwrap` 更好但不是 blocker）
- Playground / Sample code 中的簡化寫法
- SPM / CocoaPods 自動生成的檔案
- `Assets.xcassets` 裡的 JSON 變更
- Storyboard / XIB 的 auto-generated ID 變更
- 已在 diff 中處理的問題 — 讀完整個 diff 再 comment
- 單純的 code style 偏好差異（不影響正確性的 formatting）

---

## 附錄：iOS Review 快速參考

### Concurrency 安全等級速查

| Situation | Safe? | Action |
|-----------|-------|--------|
| `@MainActor class` + `Task { }` 內存取 self | ✅ 繼承 isolation | 不需修改 |
| `@MainActor class` + `Task.detached { }` 內存取 self | ❌ 不繼承 | 需要 `await MainActor.run {}` |
| `nonisolated func` 存取 stored property | ❌ Swift 6 error | 標為 CRITICAL |
| `Sendable` closure 捕獲 mutable var | ❌ Data race | 標為 CRITICAL |
| `actor` 的 method 被 `nonisolated` caller 呼叫 | ✅ 自動 await | 確認有 await |

### 常見 Retain Cycle 模式

```swift
// ❌ BAD — retain cycle
publisher.sink { value in
    self.update(value)  // self 被 sink closure retain
}
.store(in: &cancellables)

// ✅ GOOD
publisher.sink { [weak self] value in
    self?.update(value)
}
.store(in: &cancellables)

// ❌ BAD — Task retains self beyond view lifecycle
class MyViewModel {
    func load() {
        Task {
            let data = await fetchData()
            self.items = data  // self retained until Task completes
        }
    }
}

// ✅ GOOD — Task stored & cancelled in deinit
class MyViewModel {
    private var loadTask: Task<Void, Never>?
    
    func load() {
        loadTask = Task { [weak self] in
            let data = await fetchData()
            self?.items = data
        }
    }
    
    deinit { loadTask?.cancel() }
}
```

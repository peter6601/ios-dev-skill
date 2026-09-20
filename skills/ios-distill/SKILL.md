---
name: ios-distill
description: 移除不必要的複雜性——簡化 View 結構、State 管理、Navigation 層級，讓介面回歸本質。簡化不是移除功能，而是移除用戶和目標之間的障礙。與鄰居的分工：`ios-polish` 是加細節不是減、`ios-harden` 是補韌性、`ios-critique` 只報告不改。
user-invocable: true
arguments: [target]
argument-hint: "[要精煉的功能或元件]"
---

# iOS Distill — 精煉簡化

移除 SwiftUI 介面和程式碼中不必要的複雜性，揭示本質元素，透過無情的簡化創造清晰。

## 必要前置準備

### 上下文收集（先做這個）

沒有足夠的上下文就無法做好簡化。需要了解：
- **目標用戶**（關鍵）：誰在用這個功能？
- **核心用例**（關鍵）：他們要完成什麼任務？
- **本質 vs 附加**：什麼是真正必要的？什麼是 nice-to-have？

嘗試從程式碼和現有設計中推斷這些資訊。

1. 如果你需要推斷且信心不足，**必須停下來詢問用戶**確認
2. 如果完全無法推斷，**必須停下來詢問用戶**

**不要在上下文不清楚時就開始簡化。簡化錯誤的東西會摧毀可用性。**

---

## 評估現狀

分析是什麼讓設計感覺複雜或雜亂：

### 1. 辨識複雜性來源

- **太多元素**：互相競爭的按鈕、冗餘資訊、視覺雜亂
- **過多變化**：太多顏色、字體大小、style 沒有目的
- **資訊過載**：所有東西同時可見，沒有漸進揭露
- **視覺噪音**：不必要的 `overlay`、`.shadow`、`.background`、裝飾性元素
- **混亂的層級**：不清楚什麼最重要
- **功能蔓延**：太多選項、操作、前進路徑

### 2. 找到本質

- 主要用戶目標是什麼？（應該只有一個）
- 什麼是真正必要的 vs nice-to-have？
- 什麼可以移除、隱藏、或合併？
- 什麼是 20% 能帶來 80% 價值的東西？

**核心原則**：簡化不是移除功能——而是移除用戶和目標之間的障礙。每個元素都必須證明自己存在的理由。

## 規劃簡化策略

建立無情的編輯策略：

- **核心目的**：這個畫面應該完成的唯一任務是什麼？
- **必要元素**：完成該目的真正需要什麼？
- **漸進揭露**：什麼可以等到需要時再顯示？
- **合併機會**：什麼可以被整合？

## 系統化簡化

跨以下維度系統性地移除複雜性：

### View 結構簡化

- **減少嵌套深度**：SwiftUI View body 中 `VStack { HStack { VStack { ... }}}` 嵌套不超過 3 層
- **拆分巨大 View**：單一 View 的 `body` 超過 50 行是 soft smell（值得看一眼，不是硬規則）。工作流的 hard gate 是 `skill-router.md` §5 的 **body >80、per file**；51–80 行在這裡值得檢討，在閘門是 pass
- **移除 wrapper View**：不做任何事的中間容器 View，直接移除
- **善用 ViewBuilder**：用 `@ViewBuilder` computed property 替代不必要的中間 View

```swift
// 不好：過度嵌套
VStack {
    HStack {
        VStack {
            Text(title)
            Text(subtitle)
        }
        Spacer()
        VStack {
            Button(...) { }
            Button(...) { }
        }
    }
}

// 好：拆分為有意義的子 View
VStack {
    HStack {
        titleSection
        Spacer()
        actionButtons
    }
}
```

### State 管理簡化

- **減少 @State 數量**：單一 **View** 超過 5 個 `@State` 是 soft smell。閘門的 `@State >5` 算的是**整個檔案**（`swiftui-metrics.py`），同檔多個 View 時兩者結論會不同——以閘門為準
- **合併相關 State**：用 struct 或 enum 合併相關的狀態
- **下推 State**：State 應該放在最低的需要層級，不要所有 State 都在父 View
- **簡化 Binding 鏈**：過長的 Binding 傳遞鏈暗示架構問題
- **善用 Derived State**：可以從現有 State 計算出的值，不要另存一份

```swift
// 不好：太多獨立 State
@State private var isLoading = false
@State private var hasError = false
@State private var errorMessage = ""
@State private var data: [Item]? = nil

// 好：用 enum 表達互斥狀態
enum ViewState {
    case loading
    case loaded([Item])
    case error(String)
}
@State private var state: ViewState = .loading
```

### Navigation 簡化

- **減少層級**：超過 3 層 push navigation 就該重新考慮架構
- **合併相似畫面**：差異很小的畫面可以用參數化同一個 View
- **選擇正確的模態**：不是所有東西都需要 `.sheet`，有時 inline 展開更好
- **避免 Navigation 死胡同**：每個畫面都該有清楚的「下一步」

### 互動簡化

- **減少選擇**：更少的按鈕、更少的選項、更清晰的前進路徑（選擇悖論是真的）
- **聰明的預設值**：讓常見選擇自動化，只在必要時才問用戶
- **Inline 操作**：用 `.swipeActions` 或 inline editing 替代跳轉到新畫面
- **減少步驟**：註冊能不能一步完成？設定流程能不能更短？
- **清楚的 CTA**：一個明顯的下一步，而非五個互相競爭的操作

### 內容簡化

- **更短的文案**：把每句話砍掉一半，然後再砍一半
- **主動語氣**：「儲存變更」而非「變更將被儲存」
- **移除術語**：Plain language 永遠贏
- **可掃描的結構**：短段落、列表、清楚的標題
- **只保留必要資訊**：移除行銷文字、法律用語、模稜兩可的說法

### 程式碼簡化

- **移除未使用的 code**：dead code、unused Views、orphaned files
- **合併相似 style**：重複的 modifier 鏈提取為 `ViewModifier` 或 extension
- **減少 variants**：那個元件真的需要 12 種變體嗎？3 種能不能涵蓋 90% 的情況？
- **善用 SwiftUI 內建**：不要重新發明 `List`、`Form`、`NavigationStack` 已經提供的功能

## 絕對不要

- 移除必要功能（簡化 ≠ 沒功能）
- 犧牲 Accessibility（清楚的 label 和 accessibility modifier 仍然必要）
- 簡化到不清楚（神秘 ≠ 極簡）
- 移除用戶做決定需要的資訊
- 完全消除層級（有些東西應該突出）
- 過度簡化複雜領域（複雜度要匹配實際任務複雜度）

## 驗證簡化

確保簡化改善了可用性：

- **更快完成任務**：用戶能更快達成目標嗎？
- **降低認知負擔**：更容易理解該做什麼了嗎？
- **仍然完整**：所有必要功能仍然可用嗎？
- **更清晰的層級**：什麼最重要一目了然嗎？
- **更好的效能**：更簡單的 View 結構是否減少了重繪？

## 記錄移除的複雜性

如果移除了功能或選項：
- 記錄為什麼移除
- 考慮是否需要替代的存取方式
- 標註需要監控的用戶回饋

記住：簡化是一種自信的行為——知道該保留什麼，以及有勇氣移除其餘的。正如 Antoine de Saint-Exupery 所說：「完美不是沒有東西可以再加，而是沒有東西可以再拿掉的時候。」

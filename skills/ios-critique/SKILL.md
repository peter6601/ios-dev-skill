---
name: ios-critique
description: 對一個**已完成的 SwiftUI 介面**做設計審查，產出結構化批評報告：視覺層級、資訊架構、情感共鳴、HIG 合規性、SwiftUI anti-patterns。**只報告，不改任何檔案**——要動手改細節是 `ios-polish`，要移除複雜性是 `ios-distill`，要補邊界條件與 a11y 是 `ios-harden`，要看程式碼品質是 `ios-review`。
user-invocable: true
arguments: [area]
argument-hint: "[要批評的功能或畫面]"
---

# iOS Design Critique

對 SwiftUI 介面進行全面設計批評，像設計總監一樣給出誠實、具體、可執行的回饋。

## 前置準備

1. **讀取目標畫面的程式碼**：找到相關的 SwiftUI View 檔案，理解完整的 View 結構
2. **理解上下文**：這個畫面解決什麼問題？目標用戶是誰？在 App 中的位置？
3. **如果有 Preview**：嘗試理解不同 state 下的呈現

## 設計批評維度

依序評估以下 10 個維度：

### 1. AI Slop Detection（最關鍵）

**這是最重要的檢查。** 這個介面看起來像不像 2024-2025 年 AI 產生的千篇一律設計？

常見 AI Slop 特徵（SwiftUI 版）：
- 到處都是 `RoundedRectangle` + `.shadow` 的卡片，沒有層級區分
- 所有按鈕都用 `.buttonStyle(.borderedProminent)` 沒有視覺層級
- SF Symbols 全用 `.fill` 變體，size 都一樣
- 漸層色文字當裝飾（`.foregroundStyle(.linearGradient(...))`）
- 深色背景 + 霓虹色發光效果
- 千篇一律的 `LazyVGrid` 卡片網格，每張卡片 icon + title + description
- Hero metric 模板：大數字 + 小 label + 支撐統計
- 過度使用 `.blur` 和 `.ultraThinMaterial` 玻璃擬態效果
- 每個 Section 都加 Header icon，圓角方框裡放 SF Symbol

**檢驗標準**：如果你跟別人說「這是 AI 做的」，他們會立刻相信嗎？如果是，那就是問題。

### 2. Visual Hierarchy（視覺層級）
- 眼睛是否自然流向最重要的元素？
- 是否有清楚的主要操作？2 秒內能找到嗎？
- 大小、顏色、位置是否正確傳達重要性？
- 是否有視覺上互相競爭的元素（應有不同權重）？
- `NavigationTitle` 和內容的層級是否清晰？

### 3. Information Architecture（資訊架構）
- 結構是否直覺？新用戶能理解組織方式嗎？
- 相關內容是否合理分組？（`Section`、`Group` 使用得當？）
- 是否同時呈現太多選項？（認知過載）
- Navigation 是否清晰可預測？（`NavigationStack` vs `TabView` vs Modal）
- Deep linking 結構是否合理？

### 4. Emotional Resonance（情感共鳴）
- 這個介面喚起什麼情緒？是否有意為之？
- 是否匹配品牌個性？
- 是否感覺值得信賴、專業、愉悅——或者該有的感覺？
- 目標用戶會覺得「這是為我設計的」嗎？
- 動畫和過場是否增強了情感體驗？

### 5. Discoverability & Affordance（可發現性）
- 互動元素是否明顯可互動？
- 用戶不需說明就知道該做什麼嗎？
- Swipe actions、Long press、Context menu 是否有適當提示？
- 重要功能是否被藏在不明顯的位置？
- `Button` vs `NavigationLink` 的視覺區分是否清楚？

### 6. Composition & Balance（構圖與平衡）
- Layout 是否感覺平衡？
- 留白是否被有意使用？（而非 spacer 堆出的殘餘空間）
- 間距是否有節奏感？（緊湊分組 + 寬鬆分隔）
- 不對稱是否看起來是經過設計的？

### 7. Typography as Communication（文字排版）
- 字體層級是否清楚傳達閱讀順序？
- 正文是否舒適可讀？（Dynamic Type 支援？）
- `.font()` 使用的是語義化 style（`.title`、`.body`）還是硬編碼大小？
- 標題層級之間是否有足夠對比？

### 8. Color with Purpose（有意義的色彩）
- 色彩是用來溝通還是僅僅裝飾？
- 色板是否有凝聚感？
- 強調色是否引導注意力到正確的地方？
- 是否正確使用 semantic colors（`.primary`、`.secondary`、`.accentColor`）？
- Light/Dark mode 是否都有良好呈現？

### 9. States & Edge Cases（狀態與邊界）
- 空狀態：是否引導用戶採取行動？還是只說「沒有資料」？
- 載入狀態：是否使用 skeleton/placeholder 降低感知等待時間？
- 錯誤狀態：是否有幫助且不責怪用戶？
- 成功狀態：是否確認並引導下一步？
- Offline 狀態：是否有適當處理？

### 10. HIG Compliance & Platform Feel（平台一致性）
- 是否感覺像原生 iOS App？（而非 Web App 套殼）
- 是否正確使用 iOS 導航模式？（push、present、sheet）
- 手勢是否符合平台慣例？（swipe back、pull to refresh）
- 是否善用系統元件？（`DatePicker`、`Picker`、`Toggle`）
- Toolbar 和 Navigation bar 使用是否符合 HIG？

## 產出批評報告

以設計總監的角度結構化回饋：

### Anti-Patterns Verdict
**從這裡開始。** Pass/Fail：這看起來像 AI 生成的嗎？列出具體的 AI Slop 特徵。誠實到殘忍。

### Overall Impression
簡短的直覺反應——什麼有效、什麼無效、以及最大的改進機會。

### What's Working
點出 2-3 件做得好的事。具體說明為什麼有效。

### Priority Issues
按重要性排序的 3-5 個最有影響力的設計問題：

每個 Issue 需包含：
- **What**：清楚命名問題
- **Why it matters**：這如何傷害用戶或損害目標
- **Fix**：具體的修復建議（寫出 SwiftUI code 方向）
- **Command**：建議使用哪個 command 修復（`/ios-distill`、`/ios-harden`、`/ios-polish`、`/ios-review`、`/ios-investigate`）

### Minor Observations
較小但值得處理的問題的快速筆記。

### Questions to Consider
可能解鎖更好方案的挑戰性問題：
- 「如果主要操作更突出會怎樣？」
- 「這真的需要感覺這麼複雜嗎？」
- 「一個有自信的版本會長什麼樣？」
- 「這個畫面能不能只用一個手勢完成核心任務？」

## 規則

- **直接**——含糊的回饋浪費時間
- **具體**——說「登入按鈕」而非「某些元素」
- **說明問題和影響**——不只是「不好」，要說為什麼對用戶有害
- **給具體建議**——不只是「考慮探索...」
- **無情地排優先級**——如果一切都重要，那什麼都不重要
- **不要軟化批評**——開發者需要誠實的回饋才能做出好設計

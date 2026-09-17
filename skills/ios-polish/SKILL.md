---
name: ios-polish
description: SwiftUI 出貨前的最終品質打磨。系統化檢查對齊、間距、一致性、互動狀態、動畫、Accessibility 細節——區分「能用」和「精緻」的最後一哩路。在功能完成後使用。
user-invokable: true
args:
  - name: target
    description: 要打磨的功能或區域（選填）
    required: false
---

# iOS Polish — 最終打磨

執行一絲不苟的最終品質檢查，捕捉所有區分好作品和優秀作品的小細節。

**前提**：Polish 是最後一步，不是第一步。不要打磨功能尚未完成的東西。

## 打磨前評估

1. **確認完成度**：
   - 功能上是否完整？
   - 是否有已知問題需要保留？（標記 TODO）
   - 品質標準是什麼？（MVP vs 旗艦功能？）
   - 什麼時候出貨？（有多少時間打磨？）

2. **辨識打磨區域**：
   - 視覺不一致
   - 間距和對齊問題
   - 互動狀態缺失
   - 文案不一致
   - 邊界情況和錯誤狀態
   - 載入和轉場的流暢度

---

## 系統化打磨

依序檢查以下維度：

### 1. 視覺對齊與間距

- **對齊到網格**：所有元素對齊到 8pt 網格（4pt 用於小元素）
- **一致的間距**：所有間距使用標準化數值（8、12、16、20、24、32、40），沒有隨機的 13pt 或 19pt
- **光學對齊**：視覺重心調整（圖標可能需要偏移才能看起來居中）
- **各尺寸一致**：不同 iPhone 尺寸和 iPad 上的間距和對齊一致

```swift
// 建立間距常數，不要到處寫 magic number
enum Spacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
}

// 使用
.padding(.horizontal, Spacing.md)
.padding(.vertical, Spacing.sm)
```

**檢查方式**：
- 用 Xcode Preview 的 grid overlay 驗證對齊
- 在不同裝置尺寸上測試
- 用眼睛看——「感覺」不對的地方通常真的不對

### 2. Typography 精修

- **層級一致性**：相同層級的元素全部使用相同的 `.font()` style
- **行高 (Line Spacing)**：正文適當的行距（`.lineSpacing(4)` 左右）
- **Widows 處理**：最後一行不要只有一個字（較難在 SwiftUI 中控制，但長文案注意）
- **Dynamic Type**：所有文字在 Accessibility 字體大小下仍可讀
- **字體載入**：自訂字體不應造成閃爍（FOUT）

```swift
// 一致的文字 style 定義
extension Font {
    static let sectionTitle: Font = .headline
    static let cardTitle: Font = .subheadline.weight(.semibold)
    static let cardBody: Font = .subheadline
    static let caption: Font = .caption.weight(.medium)
}
```

### 3. 色彩與對比

- **對比度**：所有文字符合 WCAG AA 標準（4.5:1 正文、3:1 大字）
- **Semantic Colors**：使用 `.primary`、`.secondary` 等語義色彩，不要硬編碼色值
- **Dark Mode 一致性**：Light/Dark 切換時所有元素都正確顯示
- **色彩意義一致**：相同顏色在整個 App 中代表相同含義
- **Focus 指示器**：焦點指示器在所有主題下都可見

```swift
// 使用 Asset Catalog 的 Color Set 管理顏色
// 自動支援 Light/Dark Mode
Color("BrandPrimary")

// 或使用語義化顏色
.foregroundStyle(.primary)    // 非 Color.black
.foregroundStyle(.secondary)  // 非 Color.gray
```

### 4. 互動狀態

每個互動元素都需要所有狀態：

- **Default**：靜止狀態
- **Pressed**：按下回饋（SwiftUI 的 `ButtonStyle` 中處理）
- **Disabled**：明確不可互動（`.disabled(true)` + 視覺變化）
- **Loading**：異步操作回饋（`ProgressView` 替換按鈕文字）
- **Error**：驗證或錯誤狀態
- **Success**：完成確認

```swift
// 自訂 ButtonStyle 處理所有狀態
struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) var isEnabled

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(
                isEnabled
                    ? (configuration.isPressed ? Color.accentColor.opacity(0.8) : Color.accentColor)
                    : Color.gray.opacity(0.3)
            )
            .foregroundStyle(isEnabled ? .white : .secondary)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeOut(duration: 0.15), value: configuration.isPressed)
    }
}
```

**缺少的狀態 = 混亂和糟糕的體驗。**

### 5. 動畫與微互動

- **流暢過場**：所有狀態變化都有適當動畫（150-300ms）
- **一致的 Easing**：使用 `.easeOut` 或 `.spring` 作為自然減速，避免 `.bouncy`（感覺過時）
- **60fps**：只動畫 `opacity`、`scaleEffect`、`offset`，避免動畫 `frame` 變化
- **有目的的動畫**：動畫服務於目的，不是裝飾
- **Reduce Motion 支援**：尊重 `accessibilityReduceMotion`

```swift
// 好的 spring 動畫參數
withAnimation(.spring(duration: 0.3, bounce: 0.15)) {
    isExpanded.toggle()
}

// 列表項目的交錯動畫
ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
    ItemRow(item: item)
        .transition(.move(edge: .bottom).combined(with: .opacity))
        .animation(.easeOut(duration: 0.25).delay(Double(index) * 0.05), value: items)
}
```

### 6. Haptic Feedback

- **成功操作**：`.success` haptic
- **錯誤/警告**：`.warning` 或 `.error` haptic
- **選擇變化**：`.selectionChanged` haptic
- **不要過度使用**：haptic 過多會變成噪音

```swift
// 適當的 haptic feedback
let impact = UIImpactFeedbackGenerator(style: .light)
let notification = UINotificationFeedbackGenerator()

// 按鈕點擊
impact.impactOccurred()

// 操作成功
notification.notificationOccurred(.success)

// Toggle/選擇變化
UISelectionFeedbackGenerator().selectionChanged()

// SwiftUI 原生
.sensoryFeedback(.selection, trigger: selectedTab)
.sensoryFeedback(.success, trigger: didSave)
```

### 7. 內容與文案

- **術語一致**：相同的東西在整個 App 中叫相同的名字
- **大小寫一致**：Title Case vs Sentence case 一致使用
- **無錯字**：文法和拼字正確
- **適當長度**：不要太囉嗦，也不要太簡短
- **標點符號一致**：Labels 不加句號，句子加句號

### 8. SF Symbols 與圖片

- **一致的 style**：所有 SF Symbols 用同一種 rendering mode（`.monochrome`、`.hierarchical`、`.palette`、`.multicolor`）
- **適當的大小**：圖標大小跟相鄰文字一致
- **光學對齊**：圖標和文字的視覺對齊（可能需要微調 offset）
- **Accessibility label**：所有有意義的圖片都有 accessibility label
- **佔位圖**：圖片載入時不造成 Layout shift

```swift
// 一致的圖標用法
Label("設定", systemImage: "gear")
    .symbolRenderingMode(.hierarchical)

// 確保圖標和文字大小匹配
Image(systemName: "star.fill")
    .font(.body)  // 和周圍文字一樣大
```

### 9. 表單與輸入

- **Label 一致性**：所有輸入都有正確的 label
- **必填指示器**：清楚且一致
- **Keyboard 類型**：email 欄位用 `.emailAddress`、數字用 `.numberPad`
- **Content Type**：設定 `.textContentType` 啟用 AutoFill
- **Tab 順序**：邏輯性的鍵盤導航（`.submitLabel`、`@FocusState`）
- **驗證時機**：一致的驗證行為（失焦時 vs 送出時）

```swift
@FocusState private var focusedField: Field?

TextField("Email", text: $email)
    .textContentType(.emailAddress)
    .keyboardType(.emailAddress)
    .submitLabel(.next)
    .focused($focusedField, equals: .email)
    .onSubmit { focusedField = .password }
```

### 10. 響應式設計

- **所有 iPhone 尺寸**：SE 到 Pro Max
- **iPad**：如果支援的話，Multitasking Split View
- **觸控目標**：最小 44x44pt
- **可讀文字**：Mobile 上不小於 11pt（理想 14pt+）
- **Landscape**：如果支援，Layout 在橫向是否合理

```swift
// 根據 size class 調整 Layout
@Environment(\.horizontalSizeClass) var sizeClass

var body: some View {
    if sizeClass == .compact {
        compactLayout
    } else {
        regularLayout
    }
}
```

### 11. 程式碼品質

- **移除 print/debugPrint**：production code 中不留 debug 輸出
- **移除註解掉的程式碼**：清理 dead code
- **移除未使用的 import**：清理不需要的依賴
- **一致的命名**：變數和函式遵循 Swift naming convention
- **Type Safety**：沒有 force unwrap（`!`）在 production code 中
- **Accessibility**：正確的 `.accessibilityLabel` 和語義化 View

---

## Polish Checklist

系統化檢查：

- [ ] 視覺對齊在所有裝置上完美
- [ ] 間距使用標準化數值，一致
- [ ] Typography 層級一致
- [ ] 所有互動狀態都已實作
- [ ] 所有過場流暢（60fps）
- [ ] 文案一致且打磨過
- [ ] SF Symbols 風格一致且大小適當
- [ ] 所有表單有正確的 label 和驗證
- [ ] 錯誤狀態有幫助性
- [ ] 載入狀態清楚
- [ ] 空狀態友善
- [ ] 觸控目標最小 44x44pt
- [ ] 對比度符合 WCAG AA
- [ ] VoiceOver 可用
- [ ] Focus 指示器可見
- [ ] 沒有 console warning 或 runtime issue
- [ ] 沒有 Layout shift
- [ ] Dark Mode 完整支援
- [ ] 尊重 Reduce Motion 偏好設定
- [ ] 程式碼乾淨（沒有 TODO、print、註解掉的 code）
- [ ] Haptic feedback 適當且不過度

## 絕對不要

- 功能尚未完成就開始打磨
- 如果 30 分鐘後就要出貨，花數小時打磨（要 triage）
- 打磨時引入 bug（徹底測試）
- 忽略系統性問題（如果間距到處都不對，修系統而非個別）
- 只打磨一個地方，其他地方仍然粗糙（品質水準要一致）

## 最終驗證

在標記為完成之前：

- **自己使用它**：真正互動操作這個功能
- **在真機上測試**：不只是 Simulator
- **請別人 review**：新鮮的眼睛能抓到你忽略的東西
- **對比設計稿**：符合預期的設計
- **檢查所有狀態**：不只是 happy path

記住：打磨直到它感覺毫不費力、看起來有意圖、運作無瑕。注重細節——它們很重要。

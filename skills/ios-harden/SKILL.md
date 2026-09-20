---
name: ios-harden
description: 補上 **production 才會遇到的邊界條件**：空／滿／超長／錯誤／載入狀態、國際化、Dynamic Type、VoiceOver、Reduce Motion、效能韌性，讓介面從「Demo 能跑」進化到「Production 可靠」。與鄰居的分工：`ios-review` 看程式碼品質、`ios-polish` 修視覺細節、`ios-distill` 減複雜性、`ios-critique` 只報告。
user-invocable: true
arguments: [target]
argument-hint: "[要強化的功能或區域]"
---

# iOS Harden — 強化韌性

強化 SwiftUI 介面對邊界條件、錯誤、國際化問題、以及真實世界使用情境的抵抗力。

**核心信念**：只在完美資料下能運作的設計不是 production-ready。要為現實強化。

## 評估強化需求

系統化辨識弱點和邊界條件：

### 1. 極端輸入測試

- **超長文字**：名字、描述、標題超過 100 字元
- **超短文字**：空字串、單一字元
- **特殊字元**：emoji、RTL 文字、重音符號、CJK 字元
- **大數字**：百萬、十億、超過 Int 範圍
- **大量項目**：1000+ 列表項目、50+ 選項
- **無資料**：所有 empty states

### 2. 錯誤情境測試

- 網路失敗（offline、慢速、timeout）
- API 錯誤（400、401、403、404、500）
- 驗證錯誤
- 權限錯誤（相機、麥克風、通知、位置）
- 併發操作（重複點擊、race condition）
- 背景 / 前景切換中的請求

### 3. 國際化測試

- 長翻譯（德文通常比英文長 30%）
- RTL 語言（阿拉伯文、希伯來文）
- CJK 字元集（中文、日文、韓文）
- 日期/時間格式（不同 locale）
- 數字格式（1,000 vs 1.000）
- 貨幣符號

---

## 強化維度

### 一、文字溢出與換行

**SwiftUI 文字處理**：

```swift
// 單行截斷
Text(longTitle)
    .lineLimit(1)
    .truncationMode(.tail)

// 多行限制
Text(description)
    .lineLimit(3)

// 允許自適應，設定最小字體
Text(dynamicContent)
    .minimumScaleFactor(0.7)
    .lineLimit(2)
```

**Layout 溢出防護**：

```swift
// 防止 HStack 中的文字推擠其他元素
HStack {
    Text(userName)
        .lineLimit(1)
        .layoutPriority(-1)  // 讓其他元素優先佔空間
    Spacer()
    statusBadge
}

// 使用 fixedSize 控制擴展方向
Text(label)
    .fixedSize(horizontal: false, vertical: true)  // 允許垂直擴展，限制水平
```

**動態字體（Dynamic Type）**：

```swift
// 確保在所有 Dynamic Type 大小下都可用
// 使用語義化字體 style，不要硬編碼大小
Text(title).font(.headline)    // 會跟隨 Dynamic Type
Text(title).font(.system(size: 17))  // 不會跟隨，避免使用

// 在 Accessibility 大字體下調整 Layout
@Environment(\.dynamicTypeSize) var dynamicTypeSize

var body: some View {
    if dynamicTypeSize.isAccessibilitySize {
        VStack { content }  // 大字體時垂直排列
    } else {
        HStack { content }  // 正常時水平排列
    }
}
```

### 二、國際化（i18n / Localization）

**文字擴展空間**：
- 為翻譯預留 30-40% 的空間預算
- 使用彈性 Layout（`VStack`、`HStack` 配合 `Spacer`），不要固定寬度
- 用最長的語言測試（通常是德文）

```swift
// 不好：假設短英文文字
Button("Submit")
    .frame(width: 100)

// 好：自適應內容
Button("Submit")
    .padding(.horizontal, 16)
```

**RTL 支援**：

```swift
// SwiftUI 自動處理大部分 RTL
// 但需注意以下情況：

// 使用 .leading/.trailing 而非 .left/.right
.padding(.leading, 16)  // 好：RTL 時自動翻轉
.padding(.left, 16)     // 不好：RTL 時不會翻轉

// 圖標方向
Image(systemName: "arrow.right")
    .flipsForRightToLeftLayoutDirection(true)
```

**String Catalog（Xcode 15+）**：

```swift
// 使用 String Catalog (.xcstrings) 管理翻譯
// 所有 user-facing 的字串都用 LocalizedStringKey
Text("welcome_message")  // 自動查找翻譯

// 帶參數的翻譯
Text("items_count \(count)")  // String Catalog 支援 plural rules

// 不要拼接字串
// 不好：Text("Hello " + userName)  // 不同語言語序不同
// 好：Text("greeting \(userName)")  // 讓翻譯者控制語序
```

**日期/數字格式**：

```swift
// 使用 Foundation 的格式化 API
Text(date, format: .dateTime.month().day().year())
Text(price, format: .currency(code: "USD"))
Text(count, format: .number)

// 不要手動格式化日期或數字
// 不好：Text("\(month)/\(day)/\(year)")
```

### 三、錯誤處理

**網路錯誤**：

```swift
// 提供清楚的錯誤訊息 + 重試按鈕
struct ErrorView: View {
    let error: Error
    let retry: () -> Void

    var body: some View {
        ContentUnavailableView {
            Label("無法載入", systemImage: "wifi.slash")
        } description: {
            Text(error.localizedDescription)
        } actions: {
            Button("重試") { retry() }
        }
    }
}
```

**Permission 錯誤**：

```swift
// 權限被拒時提供清楚指引
if authorizationStatus == .denied {
    ContentUnavailableView {
        Label("需要相機權限", systemImage: "camera")
    } description: {
        Text("請在設定中開啟相機權限")
    } actions: {
        Button("前往設定") {
            if let url = URL(string: UIApplication.openSettingsURLString) {
                UIApplication.shared.open(url)
            }
        }
    }
}
```

**表單驗證**：

```swift
// Inline 錯誤，靠近輸入欄位
TextField("Email", text: $email)
    .textContentType(.emailAddress)
    .keyboardType(.emailAddress)
if !email.isEmpty && !isValidEmail(email) {
    Text("請輸入有效的 Email 地址")
        .font(.caption)
        .foregroundStyle(.red)
}
```

**優雅降級**：
- 核心功能在沒有網路時仍然可用（如果合理）
- 圖片載入失敗時顯示 placeholder
- 功能不支援時提供替代方案

### 四、邊界條件

**空狀態**：

```swift
// 每個列表/集合都需要空狀態設計
if items.isEmpty {
    ContentUnavailableView(
        "還沒有任何項目",
        systemImage: "tray",
        description: Text("點擊右上角的 + 開始新增")
    )
} else {
    List(items) { item in ... }
}

// 搜尋無結果
ContentUnavailableView.search(text: searchText)
```

**載入狀態**：

```swift
// 初始載入
ProgressView("載入中...")

// 列表分頁載入
List {
    ForEach(items) { item in ... }
    if hasMore {
        ProgressView()
            .onAppear { loadMore() }
    }
}

// 下拉刷新
List { ... }
    .refreshable { await reload() }

// 說明在載入什麼
ProgressView("正在載入你的專案...")
```

**大量資料**：

```swift
// 使用 LazyVStack / LazyVGrid，不要一次載入所有項目
ScrollView {
    LazyVStack {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}

// 提供搜尋和篩選功能
// 考慮分頁載入
```

**併發操作防護**：

```swift
// 防止重複提交
Button("送出") { submit() }
    .disabled(isSubmitting)

// 使用 .task 自動管理生命週期
.task(id: selectedItem) {
    await loadDetails(for: selectedItem)
}

// Debounce 搜尋輸入
.onChange(of: searchText) {
    searchTask?.cancel()
    searchTask = Task {
        try await Task.sleep(for: .milliseconds(300))
        await performSearch(searchText)
    }
}
```

**App 生命週期**：

```swift
// Scene phase 變化處理
@Environment(\.scenePhase) var scenePhase

.onChange(of: scenePhase) { _, newPhase in
    switch newPhase {
    case .active:
        refreshDataIfNeeded()
    case .background:
        saveState()
    default: break
    }
}
```

### 五、Accessibility 韌性

**VoiceOver 支援**：

```swift
// 所有有意義的 UI 元素都需要 accessibility label
Image("profile")
    .accessibilityLabel("個人頭像")

// 裝飾性元素標記為隱藏
Image(decorative: "background-pattern")
// 或
Image("divider")
    .accessibilityHidden(true)

// 自訂元素的 role
HStack { ... }
    .accessibilityElement(children: .combine)
    .accessibilityLabel("使用者 \(name)，\(status)")
```

**Dynamic Type 支援**：
- 所有文字都用語義化 `.font()` style
- 在 Accessibility 大字體下測試 Layout 是否斷裂
- 考慮用 `@ScaledMetric` 讓自訂尺寸跟隨 Dynamic Type

```swift
@ScaledMetric(relativeTo: .body) var iconSize: CGFloat = 24
```

**Reduce Motion 尊重**：

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

withAnimation(reduceMotion ? .none : .spring()) {
    isExpanded.toggle()
}
```

**色彩對比與色盲**：
- 不要只依賴顏色傳達資訊
- 搭配圖標、文字、形狀來區分狀態
- 確保 Dark Mode 下對比度足夠

### 六、效能韌性

**慢網路處理**：
- 圖片使用 `AsyncImage` 配合 placeholder
- 提供離線快取（如果合理）
- 長時間操作顯示進度而非 spinner

**記憶體管理**：

```swift
// 在 .onDisappear 取消不需要的工作
.onDisappear {
    loadingTask?.cancel()
}

// 使用 .task 自動管理
.task {
    await loadData()  // View 消失時自動取消
}

// 避免在 ObservableObject 中持有大量數據
// 考慮分頁或只保留可視範圍的數據
```

**Main Actor 安全**：

```swift
// UI 更新必須在 Main Actor
@MainActor
class ViewModel: ObservableObject {
    @Published var items: [Item] = []

    func loadItems() async {
        let result = await api.fetchItems()  // 背景執行
        self.items = result  // 自動在 Main Actor 更新
    }
}
```

---

## 驗證強化

用邊界條件徹底測試：

- [ ] **長文字**：嘗試 100+ 字元的名字
- [ ] **Emoji**：在所有文字欄位中使用 emoji
- [ ] **CJK**：用中日韓文字測試
- [ ] **Dynamic Type**：在所有 Accessibility 大小下測試
- [ ] **VoiceOver**：完整走一次 VoiceOver 流程
- [ ] **網路問題**：關閉網路、節流連線
- [ ] **大量資料**：用 1000+ 項目測試
- [ ] **快速操作**：快速連續點擊送出按鈕 10 次
- [ ] **錯誤**：強制 API 錯誤，測試所有錯誤狀態
- [ ] **空狀態**：移除所有資料，測試空狀態
- [ ] **Dark Mode**：確認所有狀態在 Dark Mode 下正常
- [ ] **背景/前景**：App 切換時狀態是否正確恢復
- [ ] **Reduce Motion**：開啟減少動態效果測試

記住：你是在為 production 現實做強化，不是 demo 完美。預期用戶會輸入奇怪的資料、在操作中途失去網路、以意想不到的方式使用你的產品。把韌性建入每個元件中。

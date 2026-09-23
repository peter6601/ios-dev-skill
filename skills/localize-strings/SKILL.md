---
name: localize-strings
description: SwiftUI 專案的多語系處理：掃出指定範圍裡 hardcoded 的中英文字串、把呼叫點換成 `LocalizedStringKey`／`String(localized:)`、產生對應的 `Localizable.xcstrings` 條目（key 用 `模組.畫面.元素`），並附上繁中與英文的預設文案；含字串插值情境。用在 Phase 4 出貨準備，或使用者說「抽字串」「做多語系」「localize」「i18n」時。**不做**：不改 UI 版面、不判斷譯文品質（預設文案是草稿，要譯者複核）、不處理 App Store metadata 的在地化（那是 `asc-localize-metadata`）。
user-invocable: true
arguments: [target]
argument-hint: "[要處理的檔案或功能區域]"
---

請協助處理 SwiftUI 專案的多語系（Localization），根據以下內容執行：

- 掃描指定檔案中所有硬編碼的中文/英文字串
- 將字串替換為 LocalizedStringKey 或 String(localized:)
- 生成對應的 Localizable.xcstrings 條目：
  - 有 Xcode MCP（Xcode 27+）**而且**已載入 Xcode 附帶的 `xcode-integration` plugin 時，譯文用 MCP 寫：換完呼叫點先 build 一次讓 Xcode 把新 key 抽進 catalog；新增語言先呼叫 `LocalizationPlanner` → `StringCatalogRead` 看哪些 key 待翻 → 每個 key 先 `StringCatalogContext` 取原文、再 `StringCatalogEdit` 寫入。這組工具規定先載入 plugin 裡的 `translation`／`translation-coordinator` skill；plugin 路徑用 `xcrun agent plugin path --plugin-format claude` 取得，以 `claude --plugin-dir <路徑>` 啟動
  - 兩者缺一就直接編輯 `.xcstrings` 的 JSON
- Key 的命名規則：模組名.畫面名.元素描述，例如 "settings.profile.title"
  <!-- touchpoint: localize-strings-001 kind=product -->
- 預設提供繁體中文（zh-Hant）與英文（en）翻譯
- 處理帶有變數的字串插值情境

處理範圍：$ARGUMENTS

（Codex 不會代換上面的變數。看到字面上的 `$ARGUMENTS` 時，改用使用者訊息裡描述的檔案或功能區域；沒描述就問一句要處理哪裡。）

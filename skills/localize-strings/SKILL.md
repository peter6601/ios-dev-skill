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
- 生成對應的 Localizable.xcstrings 條目（JSON 格式）
- Key 的命名規則：模組名.畫面名.元素描述，例如 "settings.profile.title"
- 預設提供繁體中文（zh-Hant）與英文（en）翻譯
- 處理帶有變數的字串插值情境

$ARGUMENTS

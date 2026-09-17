---
name: localize-strings
description: 請協助處理 SwiftUI 專案的多語系（Localization），根據以下內容執行：
user-invokable: true
args:
  - name: target
    description: 要處理的檔案或功能區域（選填）
    required: false
---

請協助處理 SwiftUI 專案的多語系（Localization），根據以下內容執行：

- 掃描指定檔案中所有硬編碼的中文/英文字串
- 將字串替換為 LocalizedStringKey 或 String(localized:)
- 生成對應的 Localizable.xcstrings 條目（JSON 格式）
- Key 的命名規則：模組名.畫面名.元素描述，例如 "settings.profile.title"
- 預設提供繁體中文（zh-Hant）與英文（en）翻譯
- 處理帶有變數的字串插值情境

$ARGUMENTS

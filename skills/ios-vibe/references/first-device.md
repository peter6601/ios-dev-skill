# 第一次把 app 裝到使用者的 iPhone

第一張會出試用卡的 ticket 完成時做。使用者沒有 iPhone，就跳過這份，試用卡改在模擬器上試。

## 先講清楚一件事

開始前用一句話告訴使用者：「用免費的 Apple 帳號裝上去的 app，大約 7 天後會打不開，到時候跟我說一聲，我重新幫你裝就好。免費帳號同時最多裝 3 個自己做的 app。」

## 三件你不能代做的事：一步一步帶

<!-- touchpoint: ios-vibe-013 kind=command -->
一次只講一步，每步等使用者回「好了」才講下一步。某一步卡住就原地排除，不往下走。

### 第 1 步：在 Xcode 登入 Apple ID

> 「打開 Xcode，點左上角選單的 Xcode → Settings（設定）→ 上方的 Accounts，按左下角的 +，選 Apple ID，登入你的 Apple 帳號。好了跟我說。」

- 密碼由使用者自己輸入，你不要經手，也不要請他把密碼告訴你。
- 常見卡點：沒看到 Accounts 分頁（請他確認開的是 Xcode 不是別的 app）；雙重認證碼（請他看自己的其他 Apple 裝置）。

### 第 2 步：接上 iPhone、打開開發者模式

> 「用線把 iPhone 接到這台 Mac。iPhone 如果跳出『要信任這部電腦嗎？』，按信任並輸入手機密碼。接著在 iPhone 打開 設定 → 隱私權與安全性 → 最下面的『開發者模式』，打開它，手機會要求重新開機。開完機再確認一次開啟。好了跟我說。」

- 常見卡點：找不到「開發者模式」：iPhone 要先接過一次 Xcode 才會出現這個選項。請他保持接線，你執行 `xcrun devicectl list devices` 讓 Xcode 認得這支手機，再請他重看一次。

### 第 3 步：第一次裝完後，信任這個開發者

先做下面「你自己做的事」把 app 裝上去。第一次打開 app 時 iPhone 會擋下來，這時再講：

> 「iPhone 會說這個開發者不受信任。到 設定 → 一般 → VPN 與裝置管理，點你的 Apple 帳號那一項，按『信任』。再回到主畫面打開 app。打得開跟我說。」

## 你自己做的事

1. **找到手機**：`xcrun devicectl list devices`，記下使用者 iPhone 的識別碼。
<!-- touchpoint: ios-vibe-014 kind=command -->
2. **找到簽署團隊**：先試著從 Xcode 設定讀出使用者的 Team ID（例如 `defaults read com.apple.dt.Xcode` 裡跟 provisioning team 有關的項目）。讀不到時才請使用者看：「在 Xcode → Settings → Accounts 點你的帳號，右邊『Team』那一欄寫什麼？」這是例外，問之前照 `SKILL.md` 規則 2 記錄。
3. **設定專案**：把 Team ID 寫進專案的簽署設定（自動簽署），bundle id 維持 `new-app.py` 給的值；和別的 app 衝突時，在後面加使用者名稱或日期讓它唯一。
4. **build 並安裝**：
   - `xcodebuild -project <App>.xcodeproj -scheme <App> -destination 'generic/platform=iOS' -allowProvisioningUpdates DEVELOPMENT_TEAM=<Team ID> build`
   - `xcrun devicectl device install app --device <識別碼> <build 出來的 .app 路徑>`
   - `xcrun devicectl device process launch --device <識別碼> <bundle id>`
5. 裝好後出這張 ticket 的試用卡。

之後每次要裝新版，重做第 4 步即可，不用再帶三件事。App 過了 7 天打不開時，也是重做第 4 步。

## 失敗時

- build 報簽署錯誤：先確認第 1 步真的登入成功（Accounts 裡看得到帳號），再重試。
- 同一個錯誤重試兩次還不行：用白話描述卡在哪一步，請使用者截圖 Xcode 或 iPhone 上看到的畫面給你看，不要叫他自己改 Xcode 設定。

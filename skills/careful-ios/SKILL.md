---
name: careful-ios
description: >
  iOS 開發專用的破壞性指令防護。攔截 git force-push（特別是 release/main/develop 分支）、
  刪除 .xcodeproj/.xcworkspace、清除 Provisioning Profiles、Simulator erase all、
  Keychain 刪除、pod deintegrate、rm -rf 非安全目標等危險操作。
  安全例外自動放行：DerivedData、Pods、.build、xcuserdata、SourcePackages、node_modules。
  觸發場景：使用者說「小心一點」、「careful」、「安全模式」、「be careful」、
  「保護模式」、「prod mode」、「上線前」，或在操作 release branch、production 環境、
  DevOps workflow 時主動建議使用。
  即使使用者沒有明確要求，在偵測到即將對 release/** 或 main branch 進行危險操作時，
  也應主動建議啟用此 skill。
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash ${CLAUDE_SKILL_DIR}/bin/check-careful-ios.sh"
          statusMessage: "檢查破壞性指令..."
---

# /careful-ios — iOS 破壞性指令防護

安全模式已**啟動**。每一個 bash 指令都會在執行前檢查是否包含破壞性 pattern。
如果偵測到危險指令，會先警告並讓你選擇繼續或取消。

---

## 防護清單

### 🚨 CRITICAL — 高風險操作

| Pattern | 範例 | 風險 |
|---------|------|------|
| Force-push 到保護分支 | `git push -f origin release/1.2.0` | 覆寫 release branch 歷史，破壞 CI/CD 和同事的分支 |
| Force-push（一般） | `git push -f origin feature/xxx` | 覆寫 remote 歷史，其他人的 work 可能遺失 |
| 刪除 Xcode 專案檔 | `rm -rf MyApp.xcodeproj` | 專案無法建構 |
| 刪除 entitlements | `rm MyApp.entitlements` | App capabilities 全部失效 |
| `git reset --hard` | `git reset --hard HEAD~3` | 永久丟失未 commit 的變更 |
| `git checkout` / `git restore` 指向整個工作區 | `git checkout .`、`git restore :/` | 丟失所有未 commit 的變更 |
| `git branch -D` | `git branch -D feature/unmerged` | 未合併的 commit 可能遺失 |

### ⚠️ DESTRUCTIVE — 需要注意

| Pattern | 範例 | 風險 |
|---------|------|------|
| `rm -rf`（非安全目標） | `rm -rf Sources/` | 永久刪除檔案 |
| `xcrun simctl erase all` | `xcrun simctl erase all` | 所有 Simulator 重設為出廠狀態 |
| `xcrun simctl delete` | `xcrun simctl delete all` | 刪除 Simulator，需從 Xcode 重建 |
| 刪除 Keychain 項目 | `security delete-generic-password` | 儲存的憑證和 token 永久刪除 |
| 刪除 Provisioning Profiles | `rm ~/Library/...Provisioning Profiles/` | 需從 Apple Developer Portal 重新下載 |
| `pod deintegrate` | `pod deintegrate` | CocoaPods 從專案移除，xcworkspace 失效 |
| `DROP TABLE` / `TRUNCATE`（交給資料庫執行時）| `sqlite3 app.db "DROP TABLE users"` | SQLite / Core Data 資料永久遺失；`echo`／`grep` 只是提到關鍵字不算 |

### ⚡ CAUTION — 較低風險但值得注意

| Pattern | 範例 | 風險 |
|---------|------|------|
| 刪除全域 DerivedData | `rm -rf ~/Library/.../DerivedData` | 所有專案的 build cache 清除，下次 full rebuild |
| `swift package reset` | `swift package reset` | SPM 依賴重新下載 |
| `defaults delete` | `defaults delete com.example.myapp` | App 的 UserDefaults 全部清除 |

---

## 安全例外 — 自動放行

`rm -rf` 的安全例外看**路徑形狀**，不是只看最後一段的名字——專案裡真的有
`Modules/Feature/build` 這種 source 目錄，只比對名字會把它靜靜刪掉。

**A. 這些名字出現在路徑的任何一段，整條就當 cache**（它們不會是 source 目錄的名字）：

| 目標 | 原因 | 放行的例子 |
|------|------|------|
| `DerivedData` | Xcode build cache，隨時可重建 | `~/Library/Developer/Xcode/DerivedData/MyApp-abc123` |
| `Pods` | CocoaPods 依賴，`pod install` 可恢復 | `./Pods` |
| `.build` | SPM build 目錄，build 時自動恢復 | `.build/checkouts` |
| `xcuserdata` | 個人 Xcode 設定（breakpoint、UI state） | `MyApp.xcworkspace/xcuserdata/...` |
| `xcshareddata` | 共享 scheme 設定（通常版控中可恢復） | |
| `SourcePackages` | SPM 下載的 package cache | `build/SourcePackages` |
| `ModuleCache` | Swift module cache | |
| `node_modules` | npm 依賴 | |

**B. 這些名字太泛用，只有當它是相對路徑的第一段**（＝專案自己的頂層產物）才放行：

| 目標 | 放行 | 仍會問 |
|------|------|------|
| `build` / `dist` / `coverage` | `build`、`./dist`、`coverage` | `Modules/Feature/build`、`/tmp/app/Sources/build`、`src/coverage` |

含 `..` 的路徑、以及 `/` 或 `~` 開頭又不含 A 類名字的路徑，一律問。
整個 `~/Library/Developer/Xcode/DerivedData` 資料夾本身仍是 CAUTION（清掉所有專案的 cache）。

---

## 運作方式

Hook 會讀取每一個 Bash 指令的內容，比對以上 pattern。指令會先拆成 `;`、`&&`、`||`、`|`
分隔的段落；`sudo -u root …`、`env -i …`、`nice -n 10 …` 這類前綴會剝掉再比對，
`bash -c '…'`／`sh -c '…'` 會往裡面再看一層（最多 4 層）。如果命中：

1. 顯示警告訊息，說明風險
2. 你可以選擇「繼續執行」或「取消」
3. 如果選擇繼續，指令正常執行

**Hook 不會阻擋任何操作** — 它只是在你踩到地雷前提醒你。

---

## 搭配使用建議

| 場景 | 建議 |
|------|------|
| 在 `release/**` branch 上作業 | 啟用 `/careful-ios` |
| Debug 生產環境問題 | 啟用 `/careful-ios` + `/ios-investigate`（找到 root cause 前不改 code） |
| CI/CD workflow 修改 | 啟用 `/careful-ios`，特別注意 force-push pattern |
| 執行 GitHub Actions 相關操作 | 啟用 `/careful-ios` |
| 帳號歸戶 / StoreKit 相關修改 | 啟用 `/careful-ios`，防止意外清除 Keychain 測試資料 |

---

## 停用方式

結束對話或開始新對話即可。Hook 是 session-scoped 的。

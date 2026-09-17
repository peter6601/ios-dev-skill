# Codebase Grounding — 整合面盤點（Step 1.5）

> **目的**：寫文件前，先把「feature 會碰/引用的既有符號」對當前 codebase 驗證為真。
> **不是**讀整個 codebase（浪費 token），**是**讀「整合面」（~6-10 檔）。
> **觸發**：有既有 codebase（既有 app 加新功能 / 改既有系統）→ 必做；全新 greenfield 專案（無 code）→ 跳過。

---

## 為什麼必做

design doc 通常是「某個時間點的 codebase audit + 前瞻計畫」。直接照抄會踩兩個雷：
1. **前瞻假設被當現況**：doc 寫「`boundPeerName` 改成 `boundEndpointID`」「加 `.entitlements`」——當前 code 可能還是舊名 / 檔根本不存在
2. **發明不存在的符號**：doc 提到「DI 容器 / factory」，實際可能是建構子注入，無中央 factory

→ 規劃文件一旦寫死錯的符號名，下游 agent 會照錯的做。**grep 5 秒能擋掉。**

---

## 整合面 = 要盤點的 7 類符號

從 design doc + intake 答案，列出這個 feature 會碰到的既有符號：

| 類別 | 找什麼 | 處理 |
|---|---|---|
| 1. **要實作的 protocol / 介面** | feature 的新 service 要符合的既有 protocol | **完整 Read**（method 簽名是 ticket 的 source of truth）|
| 2. **被取代 / 被 mirror 的主檔** | 要參照其行為重寫的既有實作 | **完整 Read**（不讀＝不知道要 mirror 什麼）|
| 3. **注入點 / composition root** | 誰建構/注入這個 service（DI 怎麼接）| grep `init(.*Service`，Read 關鍵注入點；**確認有無中央 factory** |
| 4. **紅線檔 + Delta 會改的既有檔** | context.md 要列「絕不改」+ ticket Delta 要改的 | grep 定位；Delta 會改的 **完整 Read** |
| 5. **既有 test / mock** | 新 service 能不能共用既有 mock | find `*Mock*` / `*Tests*`；確認 mock 對 protocol 還是 concrete |
| 6. **build config** | Info.plist / *.entitlements / Constants 既有值 | find + grep；**確認檔是否存在**（常被 doc 假設存在）|
| 7. **被引用的 model / enum / 常數** | doc 提到的型別是否真的 Codable / 屬性名 | grep 定義行 |

---

## 執行步驟

```
1. 列整合面清單（從 design doc 的「改動範圍」「模組對映」「reuse 策略」段抽符號）
2. 一輪 grep/find 定位全部符號（一個 Bash 多指令搞定）
3. 主檔完整 Read：類別 1（protocol）+ 類別 2（被 mirror 主檔）+ 類別 3 關鍵注入點
4. 建「verified facts」表（見下）
5. 寫文件時只用 verified 欄位；unverified / 不存在 → 標 (新建) 或 stop+問
```

### Verified facts 表（範例，來自一次換連線層的 feature retro）

| 符號 | design doc 說 | 當前 code 真相 | 文件怎麼寫 |
|---|---|---|---|
| `ConnectionServiceProtocol` | 實作它 | ✅ 存在，13 method（完整讀過） | 直接用真實簽名 |
| DI factory | 「DI 容器 / factory」 | ❌ 無中央 factory，各 VM `init(connectionService:)` 注入 | 標「無 factory，新增 or composition root」|
| `.entitlements` | 「編輯 .entitlements」 | ❌ 檔不存在 | 標「(新建)」|
| `MockConnectionService` | 「新建 mock」 | ✅ 已存在同 protocol | 改「驗證既有是否已涵蓋」|
| `PairingView` 注入 | （未提）| ⚠️ `:44` 注入 concrete `MultipeerConnectionService` | 加 Delta 註記：切換前先抽象化 |
| `serviceType` | `_myapp._tcp` | 真實 `"myapp"`（Constants.swift）| 用真實值 |

---

## grep pattern 速查（iOS / Swift）

```bash
# 注入點 / 有無 factory
grep -rn "init(.*Service\|Factory\|: <Protocol>" <repo> --include="*.swift"

# 屬性 / 方法真實名
grep -rn "var <name>\|func <name>\|<property>:" <repo> --include="*.swift"

# 既有 mock
find <repo> -iname "*mock*" -name "*.swift"

# build config 是否存在
find <repo> -name "*.entitlements" -o -name "Info.plist"
grep -rn "serviceType\|static let" <repo>/.../Constants.swift

# model 是否 Codable
grep -rn "struct <Name>\|enum <Name>" <repo> --include="*.swift"
```

---

## 成本控制

- **讀**：類別 1+2+3 的主檔（通常 3-5 檔）完整讀；其餘 grep 定位即可
- **不讀**：無關 feature、UI theme、第三方、utility
- 預算感：grounding pass ≈ 5-15 分鐘 / ~10-30k token。比起「文件寫錯害下游 agent 做錯」便宜太多
- 全新專案無 code → 整個跳過，直接 Step 2

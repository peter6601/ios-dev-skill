---
type: phase-doc
feature: {FEATURE_NAME}
doc: architecture
status: active
updated: {TODAY}
---

# Architecture — Backend Integration Overview

> **Status**：v1（{TODAY}）
> **定位**：**AI onboarding 必讀** — {DOMAIN} 跟 backend 串接的核心架構原則
> **範圍**：只涵蓋「跟後端串接」相關的設計

---

## 📂 文件導覽

### 本章 scope：{DOMAIN} ↔ {BACKEND_NAME} 串接設計

本檔只回答「{DOMAIN} 和 backend 之間的協定長什麼樣」，不處理 {DOMAIN} 內部架構 / 時程 / 時序細節。

### 串接細節分檔（如有）

| 想查什麼 | 讀哪份 |
|---|---|
| REST API endpoints 的 request / response / header | [`networking-rest.md`](./networking-rest.md) |
| WebSocket outbound messages | [`networking-messages.md`](./networking-messages.md) § 3 |
| WebSocket inbound notify types | [`networking-messages.md`](./networking-messages.md) § 4 |

### 其他（不在本檔範圍）

| 想查什麼 | 讀哪份 |
|---|---|
| {DOMAIN} 內部架構 / 新增元件清單 | [`../overview.md`](../overview.md) § 技術模組清單 |
| Sprint 時程 / Stage 規劃 | [`../sprint-roadmap.md`](../sprint-roadmap.md) |
| 未決題追蹤（backend / PM / Design） | [`../coordination/open-questions.md`](../coordination/open-questions.md) |
| AI 行為準則 / 已決事項 | [`../{FEATURE_CONTEXT_FILE}.md`](../{FEATURE_CONTEXT_FILE}.md) |

---

## 1. 核心架構原則

### 1.1 職責劃分

| 角色 | 職責 |
|---|---|
| **{DOMAIN}**（主控端 / client）| {CLIENT_RESPONSIBILITIES} |
| **{BACKEND_NAME}**（後端） | {BACKEND_RESPONSIBILITIES} |

```
{DATA_FLOW_DIAGRAM}
```

**對 {DOMAIN} 的實作含意**：
- {KEY_IMPLICATION_1}
- {KEY_IMPLICATION_2}

---

### 1.2 ID 設計 / 命名規則（如有）

{ID_DESIGN_DESCRIPTION}

```swift
struct {ENTITY_NAME}: Codable {
    {FIELDS}
}
```

---

### 1.3 認證機制

| 通道 | Token 帶法 |
|---|---|
| REST | {REST_AUTH_METHOD} |
| WebSocket | {WS_AUTH_METHOD} |

Token 來源：{TOKEN_SOURCE}

---

## 2. 系統架構圖

```
{SYSTEM_ARCHITECTURE_ASCII}
```

**關鍵資料流**：
1. **{DOMAIN} → backend**：{OUTBOUND_FLOW}
2. **backend → {DOMAIN}**：{INBOUND_FLOW}
3. **{DOMAIN} 本地**：{LOCAL_STATE}

---

## 3. 網路層架構（{DOMAIN} 端）

```
{LAYERED_DIAGRAM}
```

**原則**：
- UI / Session 層**不直接碰** `URLSession` / `URLSessionWebSocketTask`，都走 Service facade
- 每層都有 Protocol，方便 mock
- REST 和 WebSocket 共用同一個 token

---

## 4. REST API 串接規劃（如有）

**base URL**：`{BASE_URL}`
**認證**：{AUTH_HEADER}
**細節**：[`networking-rest.md`](./networking-rest.md)

### 4.1 Endpoint 用途速查

| Endpoint | {DOMAIN} 用來做什麼 | 必要性 |
|---|---|---|
| `{METHOD} {PATH}` | {USE_CASE} | {NECESSITY} |

### 4.2 Lifecycle

```
{LIFECYCLE_FLOW}
```

---

## 5. WebSocket 串接規劃（如有）

**URL**：`{WS_URL}`
**細節**：[`networking-messages.md`](./networking-messages.md)

### 5.1 送訊息（outbound）

{DOMAIN} 送的 message types：

| type | {DOMAIN} 送？ | 備註 |
|---|---|---|

### 5.2 收訊息（inbound）

關心的 notify_type：

| 欄位 / notify_type | 用來做什麼 |
|---|---|

### 5.3 Ping / Reconnect / Recovery 防護機制

```
{RECONNECT_STRATEGY}
```

---

## 6. Backend 串接狀態總覽

### 已解決的串接規格

{RESOLVED_ITEMS}

### 仍需 backend 回覆的項目

完整清單見 [`coordination/backend-requirements.md`](../coordination/backend-requirements.md)。

| Priority | 題號 | 簡述 |
|---|---|---|

---

## 變更紀錄

| 日期 | 變更 |
|---|---|
| {TODAY} | 初版 |

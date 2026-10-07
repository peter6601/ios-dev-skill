# 平台模型對應

本檔只管理級別與平台模型的對應；何時選哪個級別見 `plan-template.md`「Phase 2 實作任務」。

| 級別 | Claude Code | Codex |
|---|---|---|
| 實作級 | `sonnet` | `gpt-6-luna` |
| 審查級 | `opus` | `gpt-6-astra` |

Codex 對應依 2026-10-06 本機可派出的模型：Luna 定位是較簡單任務的快速、經濟模型；Astra 定位是處理最困難的工作。這是分派建議，還不是本專案的品質或成本實測結果。

Claude Code 用 Agent 的 `model` 參數；Codex 用 `spawn_agent` 的 `model` 參數。Codex 覆寫模型時要用 `fork_turns="none"` 或有限回合，不能用 `all`，所以要把 Task、架構契約與驗證方法明確附給子代理。

分派前核對當下可用的模型；不可用時講明擋在哪裡，不默默繼承主 session 或降級。plan 裡記的是當次解析結果，不是另一份平台對應規則。

`gen-codex-agents.py` 不寫死模型：角色 TOML 管角色與權限，派遣時依本表明確指定模型。

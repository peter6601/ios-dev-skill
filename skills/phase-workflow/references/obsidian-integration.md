# Obsidian 整合（phase-workflow 產出文件的格式約定；選配）

> 從 SKILL.md 搬出（2026-09-20）。Step 5 寫檔、Step 6 跑 lint 時讀這份。

> **這一整節是選配。** 預設 output_root 是 `<ios-repo>/docs/features/<feature>/`，不需要 Obsidian、不需要 vault、
> 也不需要另一個 git repo；`board.base` 照產，只是沒有 Obsidian 就看不到看板，其餘完全照常。
>
> **workspace**＝你另外放跨 repo 規劃文件的地方（建議是 git 管理的 Obsidian vault，`newLinkFormat: relative`）。
> 只有你在 Step 1 明確指定它，本 skill 才會把產出寫到 `<workspace>/Projects/…`，也才會提功能 MOC。
> 文件**同時要在 GitHub render**（overview 是給同事的 kickoff），所以**link 語法保持 relative markdown `[text](./x.md)`，不用 wikilink**。

## 1. Frontmatter（每份檔頂都加）

Reference 文件：
```yaml
---
type: phase-doc
feature: {FEATURE_NAME}
doc: {overview|rd-spec|sprint-roadmap|context|ai-prompts|architecture|tickets-index}
status: active
updated: {TODAY}
scale: {medium|large}     # 只有 overview.md 有；Step 4 確認規模後才寫入
---
```

Ticket 檔：見 `template-ticket-single.md` frontmatter（`ticket / stage / type / layers / status / estimate / covers / deps / owner / pr / tags:[phase-ticket]`）。

> frontmatter 在 GitHub 上隱形或 render 成表，無害；在 Obsidian 驅動 Bases / Dataview。

## 2. Bases 看板（= 使用者最早想要的 Jira dev board）

產 `tickets/board.base`（複製 `references/template-tickets-board.base`）。三個 view：
- **🗂️ 看板**：cards，依 `status` 分欄（backlog / in-progress / review / done / blocked）
- **📋 全部 ticket**：table，依 `stage` 分組
- **🚧 進行中/卡住**：filter status ∈ {in-progress, review, blocked}

ticket `status` 改值 → 看板自動移欄。這就是跟文件放在一起的輕量 dev board，不需外部工具。

## 3. GitHub 標準 callouts（兩邊都 render）

只用這 5 個（Obsidian + GitHub 都認）：
| Callout | 用途 |
|---|---|
| `> [!WARNING]` | 紅線檔 / 絕不修改 / regression 風險 |
| `> [!IMPORTANT]` | 已決事項 / 核心策略定案 |
| `> [!NOTE]` | 一般補充 |
| `> [!TIP]` | 實作提示 |
| `> [!CAUTION]` | 高風險操作 |

❌ 不用 Obsidian 自訂 callout（`[!decision]` 等）— GitHub 不 render。

## 4. Lint

reference 檔標 `type: phase-doc`、ticket 檔標 `tags:[phase-ticket]`，讓 `scripts/lint-tickets.py` 挑得出來檢查；你有自己的文件健檢排程就讓它呼叫 `lint-tickets.py --scan`，沒有就手動跑。規則見 `lint-rules.md`（同資料夾）。Phase A → B 切換前跑一次。

## Graph view

relative link 已驗證會出現在 Obsidian graph（全部 resolve）。不需改 link 語法就有 graph + backlinks。

# README 圖解維護說明

這三張圖用來輔助閱讀，不是工作流規則的來源。規則以各 skill 的 `SKILL.md`、`skill-router.md` 與 `handoff-checklist.md` 為準。

## 圖片清單

| 圖片 | README 位置 | 說明重點 |
|---|---|---|
| [development-workflow.png](development-workflow.png) | 使用流程 → 從需求到交付 | 從描述需求到人工審閱與交付的順序 |
| [planning-and-review.png](planning-and-review.png) | 使用流程 → 完成後審查 | 架構影響、審查強度、審查路線是三個不同判斷 |
| [roles-and-tools.png](roles-and-tools.png) | 內含工具 | 使用者、入口、執行工作階段與審查 agent 的分工 |

三張圖皆為 1536 × 1024 PNG，使用內建 `imagegen` 生成。流程圖另經一次背景與對比修正。英文版另有三張對應圖，見下方 English localization。只收錄最終版本，README 以相對路徑載入，不依賴生成工具的快取目錄。

## 更新原則

- 修改流程、責任或名稱時，先修改文字文件，再核對圖片與替代文字。
- 維持繁體中文、白底深色文字、藍綠配色與短標籤。縮到 README 寬度後，內文仍需清楚可讀。
- 圖片旁保留簡短圖說，詳細規則留在文字中。流程總覽另保留可展開的 Mermaid。
- 檢查所有箭頭方向；不要用視覺排列暗示不存在的對應關係。
- 不在圖片中加入版本敏感的安裝指令或過多 skill 名稱，避免難以維護。

## 生成提示

以下保留各圖的生成提示，供後續更新時使用。重新生成可能產生不同排版，應再次檢查文字、箭頭與對比。

### 1. 開發流程總覽

```text
Create ONE polished technical documentation infographic for a Traditional Chinese GitHub README for ios-dev-skill. Wide landscape 1536x1024, near-white #F8FAFC background, dark navy highly legible Traditional Chinese typography, muted teal and blue accents, flat vector-like editorial diagram, rounded rectangular cards, thin arrows, generous negative space, no gradients, no mascot, no fake screenshots, no decorative code. Readability at 850px display width is paramount: few words, large labels, exact text only.

Title at upper left:「從需求到交付」 subtitle「ios-dev 開發流程」.
Diagram: top row four clearly separated cards LEFT TO RIGHT connected with arrows:
01「描述需求」small「目標・範圍・驗收」;
02「確認流程」small「情境・架構影響」;
03「規劃或讀契約」small「短計畫／規格／ticket」;
04「實作與驗證」small「測試・Preview・量測」.
Second row three cards RIGHT TO LEFT (serpentine, arrow from top right card DOWN to bottom right):
bottom right 05「審查與修復」small「依風險選擇路線」;
bottom center 06「人工審閱」small「diff・證據・未解決事項」;
bottom left 07「依授權交付」small「提交・回寫・接續工作」.
Arrow direction must match sequence 01→02→03→04→05→06→07 without crossing cards or text.
Footer note「已有完整契約的 ticket，沿用規劃，不重跑需求訪談。」.
These are workflow overview labels, not an exact executable state machine. All text must be Traditional Chinese as quoted, Latin ticket/diff/Preview as provided. No additional text. Crisp clean professional document figure, not a marketing poster.
```

背景修正提示（以初版流程圖作為 edit target）：

```text
Edit this documentation diagram. Preserve every text label, card, number, icon, arrow, and layout exactly. Fix ONLY the background and contrast: make the ENTIRE canvas SOLID OPAQUE WHITE (#FFFFFF), absolutely no transparency anywhere, no gradient, no dark vignette, no glow or shadow. Make heading and footer solid dark navy fully readable. Cards can retain very light flat teal/blue fills but must be opaque. Produce a crisp flat infographic on a completely solid white paper background.
```

### 2. 三個判斷，分開決定

```text
Create ONE Traditional Chinese technical README infographic. 1536x1024 landscape. Entire canvas SOLID OPAQUE WHITE #FFFFFF; absolutely no transparency, no gradients, no glow, no vignette, no texture. Crisp flat vector-like diagram, dark navy labels, muted teal blue accents, thin borders, generous whitespace, large legible typography.
Title「三個判斷，分開決定」.
Three full-width stacked horizontal rows, each with a clearly numbered short left heading and 3 spacious cards to its right.
Row 01 left heading「架構影響」 smaller「開工前判斷」; its three cards「直接擴充」「局部整理」「模組邊界」.
Under this row, one short dark text sentence「決定需要補哪些規劃與契約」.
Row 02 left heading「審查強度」 smaller「依風險判斷」; only TWO cards in row「輕」「重」.
Under this row sentence「決定檢查範圍與投入的審查工具」.
Row 03 left heading「審查路線」 smaller「選擇審查方式」; its three cards「A 共識審查」 smaller「加 Codex 審核」;「B 純 agent」 smaller「預設路線」;「C 輕量審查」 smaller「需符合門檻」.
Under this row sentence「決定誰參與審查與如何收尾」.
Footer「小功能也可能需要重審查；ticket 數不決定架構路線。」.
Separate rows with ample whitespace and fine divider lines. NO arrows between the rows because they are separate decisions, not a 3-step sequential flow. Do not imply direct extension maps to light or C; categories are independent. Exact Traditional Chinese text, no extra captions. Typography must remain readable at 850px display width. Professional clean educational figure, no ornament.
```

### 3. 誰負責哪一段

```text
Create ONE Traditional Chinese technical README infographic on SOLID OPAQUE WHITE background, absolutely no transparent pixels, no gradients, glow, vignette or shadows. Landscape 1536x1024. Clean flat editorial diagram, dark navy typography, restrained teal and blue accents, generous whitespace and large text legible at 850px width.
Title「誰負責哪一段？」 subtitle「Skill 是工作指引，agent 是審查助手」.
Four large cards in spacious 2x2 grid, reading order top left then top right then bottom left then bottom right.
Card top left label「你」 small subtitle「需求與決策」 with exactly two lines「說明目標、範圍與驗收」「閱讀成果並確認交付」.
Card top right label「ios-dev」 small subtitle「流程入口」 with lines「辨識情境與架構影響」「選擇 skill 與審查 agent」.
Card bottom left label「主 session ＋ skills」 small subtitle「執行工作」 with lines「依指引規劃、實作與驗證」「整合 findings，統一修復」.
Card bottom right label「審查 agents」 small subtitle「獨立檢查」 with lines「檢查程式碼、體驗與風險」「回報問題，不修改程式碼」.
Between bottom left and bottom right cards two short horizontal arrows at different vertical positions, one left→right labelled「送審」 and one right→left labelled「findings」. No other arrows needed. Leave plenty of space between bottom cards to fit arrow labels without collisions.
Small footer「依任務啟動需要的 agent，並非每次全開。」.
Use simple thin outline icons person / route / code document / magnifier, one per card, subtle and small. Every text Traditional Chinese verbatim except technical identifiers as given. No marketing branding, no extra invented text.
```


<a id="english-localization"></a>

## English localization

The English guide uses three localized diagrams generated with the built-in `imagegen` tool. Each Chinese diagram was used as its edit target, preserving its structure and arrow directions. Final assets:

- [development-workflow.en.png](development-workflow.en.png)
- [planning-and-review.en.png](planning-and-review.en.png)
- [roles-and-tools.en.png](roles-and-tools.en.png)

### Localization prompts

#### development-workflow.en

```text
Localize this technical README infographic into English. Preserve the diagram structure, icon meanings, white opaque background, navy text, teal/blue palette, and arrow directions. Adjust font sizes and line breaks to accommodate English naturally, maintain generous whitespace and readability at 850px display width. Every label must be English, no Chinese remains. 1536x1024 landscape. No new concepts. Title "From request to delivery"; subtitle "The ios-dev workflow". Top row left-to-right cards: 01 "Describe the task", detail "Goal · Scope · Acceptance"; 02 "Confirm the workflow", detail "Task type · Architecture"; 03 "Plan or read contracts", detail "Plan / Spec / Ticket"; 04 "Implement and verify", detail "Tests · Previews · Metrics". Bottom row right-to-left: 05 "Review and fix", detail "Choose a route by risk"; 06 "Human review", detail "Diff · Evidence · Open issues"; 07 "Authorized delivery", detail "Commit · Update · Continue". Preserve arrows 01→02→03→04 down to05 then left to06 then left to07. Footer "Tickets with complete contracts reuse the plan; no repeat requirements interview."
```

#### planning-and-review.en

```text
Localize this technical README infographic into English. Preserve the diagram structure, icon meanings, white opaque background, navy text, teal/blue palette, and arrow directions. Adjust font sizes and line breaks to accommodate English naturally, maintain generous whitespace and readability at 850px display width. Every label must be English, no Chinese remains. 1536x1024 landscape. No new concepts. Title "Three separate decisions". Row 01 heading "Architecture impact", subtitle "Before implementation"; three cards "Extend directly", "Refactor locally", "Module boundaries"; caption "Determines the plans and contracts you need". Row 02 heading "Review depth", subtitle "Based on risk"; TWO cards "Light", "Heavy"; caption "Determines the scope and tools for checks". Row 03 heading "Review route", subtitle "Choose the approach"; three cards "A · Consensus", detail "Add Codex review"; "B · Agent-only", detail "Default route"; "C · Lightweight", detail "Must meet eligibility rules"; caption "Determines who reviews and how work is finalized". Footer "Small features may need heavy review. Ticket count does not decide architecture." No arrows between independent rows.
```

#### roles-and-tools.en

```text
Localize this technical README infographic into English. Preserve the diagram structure, icon meanings, white opaque background, navy text, teal/blue palette, and arrow directions. Adjust font sizes and line breaks to accommodate English naturally, maintain generous whitespace and readability at 850px display width. Every label must be English, no Chinese remains. 1536x1024 landscape. No new concepts. Title "Who does what?"; subtitle "Skills guide the work. Agents review it.". Top left card heading "You", subtitle "Goals and decisions", lines "Define goals, scope, and acceptance" and "Review results and approve delivery". Top right heading "ios-dev", subtitle "Workflow entry point", lines "Identify task type and architecture impact" and "Select skills and review agents". Bottom left heading "Main session + skills", subtitle "Execute the work", lines "Plan, implement, and verify" and "Consolidate findings and apply fixes". Bottom right heading "Review agents", subtitle "Independent checks", lines "Check code, usability, and risk" and "Report issues without changing code". Between bottom cards preserve right arrow labeled "Review" and left arrow labeled "Findings". Footer "Only the agents needed for the task are activated."
```

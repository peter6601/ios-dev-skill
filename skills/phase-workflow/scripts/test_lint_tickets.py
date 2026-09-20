#!/usr/bin/env python3
"""Tests for lint-tickets.py — one per rule, plus the cases that came out of the dry runs
(2026-09-20): `covers: [{FR1}]` filled literally, template comment lines left above `---`,
a title that dodges the conjunction check with a 、, `%20` in a link, legacy folders.

Fixtures are built in a temp dir by code on purpose: the whole skill folder gets installed
into Claude's skill directory, where a stray `.md` fixture could be picked up as a command.

Run: python3 skills/phase-workflow/scripts/test_lint_tickets.py
"""
import json, os, subprocess, sys, tempfile, unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint-tickets.py")

OVERVIEW = """---
type: phase-doc
doc: overview
scale: medium
---
# 收藏

## 📏 功能範圍（做 / 不做）

### ✅ 這次要做

| # | 使用者能…… | 優先序 |
|---|---|---|
| FR1 | 讀者能把文章加入收藏 | P1 |
| FR2 | 讀者能看到收藏清單 | P1 |
| FR3 | 收藏能透過 iCloud 同步 | P3 |

### ❌ 這次不做
- 收藏資料夾

---

## 📱 頁面清單
"""

README = """---
type: phase-doc
doc: tickets-index
---
# Tickets

| Ticket | 標題 |
|---|---|
| [`1-F1`](./1-F1.md) | 地基 |
| [`2-B1`](./2-B1.md) | 加入收藏 |
| [`2-B2`](./2-B2.md) | 收藏清單 |

## ✅ 需求涵蓋表

| 需求 | Ticket | 狀態 |
|---|---|---|
| FR1 | [`2-B1`](./2-B1.md) | 已切 |
| FR2 | [`2-B2`](./2-B2.md) | 已切 |
| FR3 | — | deferred: Stage 3 |
"""


def ticket(tid, kind, title, *, stage=2, layers="[Service, UI]", covers="[]", deps="[]",
           estimate=0.5, files=(), demo="開 app → 點愛心 → 愛心變實心", criteria=2, extra=""):
    demo_line = f"> **Demo**: {demo}\n" if demo is not None else ""
    file_lines = "\n".join(f"- `{name}`（{mode}）" for name, mode in files) or "- `New.swift`（新建）"
    checks = "\n".join(f"- [ ] 條件 {n}" for n in range(1, criteria + 1))
    return f"""---
ticket: "{tid}"
title: "{title}"
feature: "收藏"
stage: {stage}
type: "{kind}"
layers: {layers}
status: backlog
estimate: {estimate}
covers: {covers}
deps: {deps}
owner:
pr:
tags:
  - phase-ticket
---

# {tid} {title}

> **Type**: {kind}
{demo_line}
## Refs

- [`../overview.md`](../overview.md) § 功能範圍

## Files

{file_lines}

## 架構約束

- 所屬模組：FavoriteStore

## Tasks

- [ ] 做

## Acceptance Criteria

{checks}

## Verification

- [ ] 測試：`xcodebuild test -scheme PocketReads`
{extra}
"""


def baseline():
    return {
        "overview.md": OVERVIEW,
        "context.md": "---\ntype: phase-doc\n---\n# context\n",
        "tickets/README.md": README,
        "tickets/1-F1.md": ticket("1-F1", "Foundation", "收藏的契約、Model、注入點就位", stage=1,
                                  layers="[Service]", demo="不適用——2-B1、2-B2 靠它",
                                  files=[("FavoriteStore.swift", "新建")]),
        "tickets/2-B1.md": ticket("2-B1", "Behavior", "讀者能把文章加入收藏", covers="[FR1]",
                                  deps='["1-F1"]', files=[("ArticleDetailView.swift", "編輯")]),
        "tickets/2-B2.md": ticket("2-B2", "Behavior", "讀者能看到收藏清單", covers="[FR2]",
                                  deps='["1-F1"]', files=[("FavoritesListView.swift", "新建")]),
    }


class LintTickets(unittest.TestCase):
    def run_lint(self, files, *flags):
        with tempfile.TemporaryDirectory() as root:
            for rel, body in files.items():
                path = os.path.join(root, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(body)
            proc = subprocess.run([sys.executable, SCRIPT, root, "--json", *flags],
                                  capture_output=True, text=True)
        return proc.returncode, json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else proc

    def messages(self, result, key="errors"):
        return " | ".join(f"§{item['rule']} {item['where']} {item['message']}" for item in result[key])

    # ── baseline ──
    def test_clean_folder_passes(self):
        code, result = self.run_lint(baseline())
        self.assertEqual((code, result["errors"], result["warnings"]), (0, [], []), self.messages(result))
        self.assertEqual((result["mode"], result["scale"], result["tickets"]), ("current", "medium", 3))

    def test_missing_folder_exits_2(self):
        proc = subprocess.run([sys.executable, SCRIPT, "/nonexistent/feature"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_strict_fails_on_warnings(self):
        files = baseline()
        files["tickets/2-B1.md"] = ticket("2-B1", "Behavior", "讀者能把文章加入收藏", covers="[FR1]",
                                          deps='["1-F1"]', estimate=1.0)
        self.assertEqual(self.run_lint(files)[0], 0)
        self.assertEqual(self.run_lint(files, "--strict")[0], 1)

    # ── § A ──
    def test_template_comment_above_front_matter(self):
        files = baseline()
        files["tickets/2-B1.md"] = "# 填值範例：……\n" + files["tickets/2-B1.md"]
        code, result = self.run_lint(files)
        self.assertEqual(code, 1)
        self.assertIn("front matter 不在檔案第一行", self.messages(result))

    def test_literal_placeholder_in_front_matter(self):
        files = baseline()
        files["tickets/2-B1.md"] = files["tickets/2-B1.md"].replace('feature: "收藏"', 'feature: "{FEATURE_NAME}"')
        code, result = self.run_lint(files)
        self.assertEqual(code, 1)
        self.assertIn("feature 還留著 placeholder", self.messages(result))

    def test_behavior_needs_a_real_demo_line(self):
        for demo in (None, "{從哪個入口進去}"):
            files = baseline()
            files["tickets/2-B1.md"] = ticket("2-B1", "Behavior", "讀者能把文章加入收藏", covers="[FR1]",
                                              deps='["1-F1"]', demo=demo)
            code, result = self.run_lint(files)
            self.assertEqual(code, 1)
            self.assertIn("Demo 行空白或還是 placeholder", self.messages(result))

    def test_id_letter_type_file_name_and_sections(self):
        files = baseline()
        files["tickets/2-B9.md"] = ticket("2-F9", "Behavior", "讀者能做別的事", covers="[FR1]").replace(
            "## Verification", "## Verify")
        code, result = self.run_lint(files)
        text = self.messages(result)
        self.assertEqual(code, 1)
        for expected in ("字母跟 type Behavior 對不上", "檔名跟 ticket ID 2-F9 不一致", "缺「Verification」段"):
            self.assertIn(expected, text)

    def test_unknown_type_status_and_layer(self):
        files = baseline()
        files["tickets/2-B1.md"] = (ticket("2-B1", "Behavior", "讀者能把文章加入收藏", covers="[FR1]",
                                           deps='["1-F1"]', layers="[Service, Network]")
                                    .replace("status: backlog", "status: in_progress"))
        files["tickets/2-B2.md"] = files["tickets/2-B2.md"].replace('type: "Behavior"', 'type: "Feature"')
        code, result = self.run_lint(files)
        text = self.messages(result)
        self.assertEqual(code, 1)
        for expected in ("status 值不合法：in_progress", "layers 有不認得的值", "type 值不合法：Feature"):
            self.assertIn(expected, text)

    # ── § B / C ──
    def test_links_wikilinks_markers_and_callouts(self):
        files = baseline()
        files["context.md"] += ("\n見 [[README]]。\n{IF_LARGE：大型才有}\n> [!NOTE] 完工回寫\n> 內容\n"
                                "[壞](./missing.md) [好](./overview.md) [外](https://example.com)\n")
        code, result = self.run_lint(files)
        text = self.messages(result)
        self.assertEqual(code, 1)
        for expected in ("wikilink", "殘留 {IF_", "callout 標記後面接了標題", "斷鏈：./missing.md"):
            self.assertIn(expected, text)
        self.assertNotIn("overview.md)", text)

    def test_if_marker_inside_a_fenced_prompt_is_caught(self):
        files = baseline()
        files["ai-prompts.md"] = "# prompts\n\n```\n{IF_LARGE：3. architecture/<topic>.md}\n```\n"
        code, result = self.run_lint(files)
        self.assertEqual(code, 1)
        self.assertIn("ai-prompts.md 殘留 {IF_", self.messages(result))

    def test_callout_alone_on_its_line_and_code_are_fine(self):
        files = baseline()
        files["context.md"] += "\n> [!NOTE]\n> **完工回寫**\n\n寫法範例：`[[wikilink]]`、`{IF_LARGE：…}`\n"
        self.assertEqual(self.run_lint(files)[0], 0)

    def test_percent_encoded_link_resolves(self):
        files = baseline()
        files["docs/my note.md"] = "# note\n"
        files["context.md"] += "\n[筆記](./docs/my%20note.md)\n"
        code, result = self.run_lint(files)
        self.assertEqual(code, 0, self.messages(result))

    def test_medium_must_not_link_large_only_files(self):
        files = baseline()
        files["sprint-roadmap.md"] = "# roadmap\n"
        files["context.md"] += "\n[roadmap](./sprint-roadmap.md)\n"
        code, result = self.run_lint(files)
        self.assertEqual(code, 1)
        self.assertIn("中型連到大型專屬檔", self.messages(result))
        files["overview.md"] = OVERVIEW.replace("scale: medium", "scale: large")
        self.assertEqual(self.run_lint(files)[0], 0)

    def test_orphan_ticket_warns(self):
        files = baseline()
        files["tickets/README.md"] = README.replace("| [`2-B2`](./2-B2.md) | 收藏清單 |\n", "").replace(
            "[`2-B2`](./2-B2.md) | 已切", "2-B2 | 已切")
        code, result = self.run_lint(files)
        self.assertEqual(code, 0)
        self.assertIn("沒有被 tickets/README.md 連入", self.messages(result, "warnings"))

    # ── § F ──
    def test_uncovered_requirement(self):
        files = baseline()
        files["tickets/README.md"] = README.replace("| FR3 | — | deferred: Stage 3 |\n", "| FR3 | — | |\n")
        code, result = self.run_lint(files)
        self.assertEqual(code, 1)
        self.assertIn("FR3 沒有任何 ticket 接", self.messages(result))

    def test_requirement_missing_from_readme_table(self):
        files = baseline()
        files["overview.md"] = OVERVIEW.replace("| FR3 |", "| FR3 | x |\n| FR4 | 讀者能分享收藏 | P2 |\n| FR9 |")
        code, result = self.run_lint(files)
        self.assertEqual(code, 1)
        self.assertIn("FR4 tickets/README.md 的需求涵蓋表沒有這一列", self.messages(result))

    def test_covers_unknown_requirement_and_empty_behavior(self):
        files = baseline()
        files["tickets/2-B1.md"] = ticket("2-B1", "Behavior", "讀者能把文章加入收藏", covers="[FR1, FR7]", deps='["1-F1"]')
        files["tickets/2-B2.md"] = ticket("2-B2", "Behavior", "讀者能看到收藏清單", covers="[]", deps='["1-F1"]')
        code, result = self.run_lint(files)
        text = self.messages(result)
        self.assertEqual(code, 1)
        self.assertIn("covers 列了 overview.md 沒有的 FR7", text)
        self.assertIn("Behavior 的 covers 是空的", text)

    def test_requirement_moved_to_not_doing_counts_as_handled(self):
        files = baseline()
        files["overview.md"] = OVERVIEW.replace("- 收藏資料夾", "- 收藏資料夾\n- FR3 iCloud 同步（移到下一版）")
        files["tickets/README.md"] = README.replace("deferred: Stage 3", "不做")
        code, result = self.run_lint(files)
        self.assertEqual(code, 0, self.messages(result))

    def test_one_requirement_covered_by_two_behaviors_warns(self):
        files = baseline()
        files["tickets/2-B2.md"] = ticket("2-B2", "Behavior", "讀者能看到收藏清單", covers="[FR1, FR2]", deps='["1-F1"]')
        code, result = self.run_lint(files)
        self.assertEqual(code, 0)
        self.assertIn("FR1 被 2 張 Behavior 涵蓋", self.messages(result, "warnings"))

    def test_rd_spec_entry(self):
        files = baseline()
        del files["overview.md"]
        rd_spec = ("---\ntype: phase-doc\ndoc: rd-spec\n---\n# spec\n\n## 需求對照（PM spec 條目 → T 卡）\n\n"
                   "| # | 條目 | T 卡／處置 |\n|---|---|---|\n| FR1 | 加入 | T1 |\n| FR2 | 清單 | T2 |\n"
                   "| FR3 | 同步 | Out of Scope——下一版 |\n\n## 現況總覽\n")
        files["rd-spec.md"] = rd_spec
        for name in ("1-F1", "2-B1", "2-B2"):
            files[f"tickets/{name}.md"] = files[f"tickets/{name}.md"].replace("../overview.md", "../rd-spec.md")
        code, result = self.run_lint(files)
        self.assertEqual(code, 0, self.messages(result))
        files["rd-spec.md"] = rd_spec.replace("| FR3 | 同步 | Out of Scope——下一版 |", "| FR3 | 同步 | |")
        code, result = self.run_lint(files)
        self.assertEqual(code, 1)
        self.assertIn("FR3：需求對照表的「T 卡／處置」是空的", self.messages(result))

    # ── § G ──
    def test_deps_missing_forward_cycle_and_string(self):
        files = baseline()
        files["tickets/1-F1.md"] = ticket("1-F1", "Foundation", "地基", stage=1, layers="[Service]",
                                          deps='["2-B1"]', demo="不適用")
        files["tickets/2-B1.md"] = ticket("2-B1", "Behavior", "讀者能把文章加入收藏", covers="[FR1]",
                                          deps='["1-F1", "9-B9"]')
        files["tickets/2-B2.md"] = ticket("2-B2", "Behavior", "讀者能看到收藏清單", covers="[FR2]", deps='"1-F1"')
        code, result = self.run_lint(files)
        text = self.messages(result)
        self.assertEqual(code, 1)
        for expected in ("deps 指向不存在的 9-B9", "前向依賴：2-B1", "循環依賴", "deps 不是 YAML list"):
            self.assertIn(expected, text)

    # ── § H ──
    def test_same_file_needs_a_deps_chain(self):
        files = baseline()
        edit = [("FavoriteStore.swift", "編輯")]
        files["tickets/2-B1.md"] = ticket("2-B1", "Behavior", "讀者能把文章加入收藏", covers="[FR1]", deps='["1-F1"]', files=edit)
        files["tickets/2-B2.md"] = ticket("2-B2", "Behavior", "讀者能看到收藏清單", covers="[FR2]", deps='["1-F1"]', files=edit)
        code, result = self.run_lint(files)
        self.assertEqual(code, 0)
        self.assertIn("同檔未排序：2-B1、2-B2", self.messages(result, "warnings"))
        files["tickets/2-B2.md"] = ticket("2-B2", "Behavior", "讀者能看到收藏清單", covers="[FR2]", deps='["2-B1"]', files=edit)
        self.assertNotIn("同檔未排序", self.messages(self.run_lint(files)[1], "warnings"))

    def test_split_signals(self):
        files = baseline()
        many = [(f"File{n}.swift", "新建") for n in range(6)] + [("FileTests.swift", "新建")]
        files["tickets/2-B1.md"] = ticket("2-B1", "Behavior", "讀者能加入收藏、看到提示", covers="[FR1]",
                                          deps='["1-F1"]', files=many, criteria=5, estimate=0.75)
        text = self.messages(self.run_lint(files)[1], "warnings")
        for expected in ("production 檔 6 個", "estimate 0.75 >0.5", "Acceptance Criteria 5 條", "可能並列兩件事"):
            self.assertIn(expected, text)

    def test_foundation_title_is_exempt_from_conjunction_check(self):
        text = self.messages(self.run_lint(baseline())[1], "warnings")
        self.assertNotIn("並列兩件事", text)

    def test_foundation_file_used_by_one_behavior_and_oversized_foundation(self):
        files = baseline()
        files["tickets/1-F1.md"] = ticket("1-F1", "Foundation", "地基", stage=1, layers="[Service]", demo="不適用",
                                          estimate=1.5, files=[("FavoriteStore.swift", "新建"), ("ShareLinkBuilder.swift", "新建"),
                                                               ("PocketReadsApp.swift", "編輯"), ("Favorite.swift", "新建")])
        files["tickets/2-B1.md"] += "\n用 FavoriteStore 與 ShareLinkBuilder。\n"
        files["tickets/2-B2.md"] += "\n用 FavoriteStore；PocketReadsApp 改成 TabView。\n"
        text = self.messages(self.run_lint(files)[1], "warnings")
        self.assertIn("`ShareLinkBuilder.swift` 只被一張 Behavior（2-B1）提到", text)
        self.assertNotIn("`FavoriteStore.swift` 只被", text)
        self.assertNotIn("`PocketReadsApp.swift` 只被", text)   # edited = composition root, not misplaced
        self.assertNotIn("`Favorite.swift` 只被", text)          # nobody mentions it: whole type lives in the Foundation
        self.assertIn("大於每一張 Behavior", text)

    # ── --scan ──
    def test_scan_finds_every_feature_folder_and_fails_on_a_current_error(self):
        legacy = ("---\nticket: \"2-S1\"\nstage: 2\ntype: Service\nstatus: backlog\nestimate: 0.5\n"
                  "tags:\n  - phase-ticket\n---\n# 2-S1\n")
        with tempfile.TemporaryDirectory() as root:
            trees = {"Projects/A/feature-new": baseline(),
                     "Projects/B/archive/old": {"tickets/2-S1-old.md": legacy, "tickets/README.md": "[x](./2-S1-old.md)\n"},
                     "Projects/C/not-a-feature": {"tickets/notes.md": "# 只是筆記，沒有 phase-ticket\n"},
                     ".hidden/feature": baseline()}
            for folder, files in trees.items():
                for rel, body in files.items():
                    path = os.path.join(root, folder, rel)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as handle:
                        handle.write(body)
            run = lambda: subprocess.run([sys.executable, SCRIPT, "--scan", root, "--json"], capture_output=True, text=True)
            proc = run()
            results = json.loads(proc.stdout)
            self.assertEqual(proc.returncode, 0, proc.stdout)
            self.assertEqual([(os.path.relpath(r["folder"], root), r["mode"]) for r in results],
                             [("Projects/A/feature-new", "current"), ("Projects/B/archive/old", "legacy")])
            os.remove(os.path.join(root, "Projects/A/feature-new/tickets/1-F1.md"))   # 2-B1 / 2-B2 now depend on nothing
            self.assertEqual(run().returncode, 1)

    def test_folder_and_scan_are_mutually_exclusive(self):
        for argv in ([], ["some/folder", "--scan", "."]):
            proc = subprocess.run([sys.executable, SCRIPT, *argv], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)

    # ── legacy ──
    def test_legacy_folder_never_fails(self):
        old = """---
ticket: "2-S1"
title: Service skeleton
stage: 2
type: Service
status: in_progress
estimate: 0.5
deps: "1-S4, none"
tags:
  - phase-ticket
---
# 2-S1

> **Parent**: [[README]]
"""
        code, result = self.run_lint({"tickets/2-S1-service-skeleton.md": old, "tickets/README.md": "# index\n"})
        self.assertEqual((code, result["mode"], result["errors"]), (0, "legacy", []))
        text = self.messages(result, "warnings")
        self.assertIn("status 值不合法", text)
        self.assertIn("wikilink", text)


if __name__ == "__main__":
    unittest.main()

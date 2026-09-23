#!/usr/bin/env python3
"""Tests for the free half of the layer-3 evals: screen parsing, field matching, fixtures.

No model is called.  The first screen below is what headless opus really printed for
case 3 on 2026-09-19 — it does not follow `skill-router.md` §6 to the letter, and the
parser has to cope with that.

Run: python3 skills/ios-dev/evals/test_run_evals.py
"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixtures, run_evals  # noqa: E402

REAL_SCREEN = """情境認定完成，需要你確認一次再往下。

## Step 0 路由結果

**情境 3　純呈現畫面**（內容＝畫面）
`SettingsView.swift` 目前是一個乾淨的 `List`。

```
載入：swiftui-specialist、swiftui-ui-patterns
Phase 3 派：ux-critique（設計總監視角的介面批評，只報告不改）
            architecture-auditor（檢查有沒有偷長出第二份狀態真相、會不會重繪）
            → 輕（風險三條全綠）
Review 路線：C 輕量（ios-review 兩輪 → verification）
架構結論：直接擴充。五問第 3 問＝不會
交棒：直接 Phase 2 實作，收尾照 handoff-checklist §3
會問你：不問
```

要照這組跑嗎？
"""

SPEC_SCREEN = """題目：情境＝接 ticket（內容＝功能）。這次會：
  載入：swift-concurrency
  Phase 3 派：concurrency-auditor（待定（預判重，理由：碰 actor））
  Review 路線：A 共識（預設）
  架構結論：契約已備（來源：tickets/T3.md）直接實作
  交棒：`/writing-plans`（只為這一張）
  會問你：不問
"""


TABLE_SCREEN = """情境＝**小功能**（內容＝功能）。既有固定 3 秒 → 改為指數退避。

| 項目 | 這次的決定 |
|---|---|
| 載入 | `swift-concurrency` |
| Phase 3 | **重**（風險三條踩到 concurrency＋網路協定） |
| 派 agent | `concurrency-auditor`；`ux-critique` 建議裁掉，輕量帶過 |
| Review 路線 | **B 純 agent**（C 被 §3 擋下） |
| 架構結論 | **直接擴充**——owner 清楚 |
| 交棒 | 留在 `/ios-dev` Step 1 |
"""


def verdicts(expected, screen):
    return {k: ok for k, _, _, ok in run_evals.check_fields(expected, run_evals.screen_fields(screen))}


class ScreenParsing(unittest.TestCase):
    def test_real_headless_screen(self):
        f = run_evals.screen_fields(REAL_SCREEN)
        self.assertTrue(f["情境"].startswith("3"))  # not 「情境認定完成」
        self.assertEqual(f["內容"], "畫面")
        self.assertIn("→ 輕", f["Phase 3 派"])      # the value spans its continuation lines
        self.assertEqual(f["會問你"], "不問")        # the last field stops at the fence
        self.assertEqual(verdicts(dict(scenario="3", content_axis="畫面", gate="輕", review_route=["A", "C"],
                                       architecture="直接擴充", handoff=None), REAL_SCREEN),
                         dict(scenario=True, content_axis=True, gate=True, review_route=True, architecture=True))

    def test_gate_ignores_the_word_inside_other_words(self):
        # 「重繪」 must not read as 重
        self.assertFalse(verdicts(dict(gate="重"), REAL_SCREEN)["gate"])

    def test_spec_format_by_name_and_pending_gate(self):
        got = verdicts(dict(scenario="7", content_axis="功能", gate="待定", review_route="A",
                            architecture="契約已備", handoff="writing-plans"), SPEC_SCREEN)
        self.assertTrue(all(got.values()), got)

    def test_table_form_from_the_case_13_run(self):
        got = verdicts(dict(scenario=["2", "4"], content_axis="功能", gate="重", review_route=["A", "B"],
                            architecture="直接擴充", handoff="留在"), TABLE_SCREEN)
        self.assertTrue(all(got.values()), got)
        self.assertEqual(run_evals.screen_fields(TABLE_SCREEN)["Phase 3 派"], "**重**（風險三條踩到 concurrency＋網路協定）")

    # --- Codex review 2026-09-19: reproductions that used to pass wrongly ---
    def test_no_screen_at_all_is_a_hard_fail(self):
        prose = "這張碰 concurrency，所以走重，review 走 B，收尾人工看過 diff 才 commit。"
        f = run_evals.screen_fields(prose)
        self.assertTrue(run_evals.screen_problems(f))
        self.assertEqual(verdicts(dict(gate="重", review_route="B"), prose), dict(gate=False, review_route=False))

    def test_route_that_is_ruled_out_is_not_the_answer(self):
        self.assertEqual(run_evals.route_of("C 不成立，走 B"), "?C")
        self.assertEqual(run_evals.route_of("**B 純 agent**（C 被 §3 擋下）"), "B")
        self.assertEqual(run_evals.route_of("預設 B"), "")  # §6 puts the route first; anything else is drift

    def test_gate_naming_two_answers_is_ambiguous(self):
        self.assertEqual(run_evals.gate_of("ux-critique（不是 輕，走 重）"), "?輕,重")
        self.assertEqual(run_evals.gate_of("concurrency-auditor（待定（預判 重，理由：碰 actor））"), "待定")
        # forms seen in real headless runs
        self.assertEqual(run_evals.gate_of("perf-auditor 必跑\n（輕重＝待定，預判「輕」，理由：單一畫面）"), "待定")
        self.assertEqual(run_evals.gate_of("`resilience-auditor`（輕閘門）"), "輕")
        self.assertEqual(run_evals.gate_of("改後再量一次 —— **輕重待定（預判輕，理由：單畫面）**"), "待定")
        self.assertEqual(run_evals.gate_of("resilience-auditor（輕；實作完成後依風險三條重判一次）"), "輕")
        self.assertEqual(run_evals.gate_of("ux-critique（會不會重繪）、review（輕量）"), "")

    def test_scenario_naming_two_answers_is_ambiguous(self):
        self.assertEqual(run_evals.scenario_of("情境 3 不成立，實際是情境 2"), "?2,3")

    def test_scenario_prefers_the_screen_over_prose(self):
        screen = "這是情境 3 ），走最輕的一條路線。\n\n情境＝2 小功能（內容＝兩者）\n載入：x\nPhase 3 派：y（輕）\nReview 路線：B\n"
        self.assertEqual(run_evals.scenario_of(screen), "2")

    def test_axis_is_the_first_word_not_any_word(self):
        f = run_evals.screen_fields("情境＝2 小功能（內容＝兩者：持久化屬功能、預選呈現屬畫面）")
        self.assertEqual(f["內容"], "兩者")
        self.assertEqual(run_evals.screen_fields("情境＝2（內容＝功能＋畫面）")["內容"], "兩者")

    def test_label_with_a_note_before_the_colon(self):
        screen = "情境＝1 新專案\n- **載入**：無\n- **Phase 3 派**：依每張 ticket\n- **Review 路線**：預設 B\n- **交棒**（建議開新 session 執行）：\n  /phase-workflow 入口 B：<issue>\n"
        self.assertIn("入口 B", run_evals.screen_fields(screen)["交棒"])

    def test_answer_inside_the_label_note(self):
        screen = "情境＝7 接 ticket\n- **載入**：x\n- **Phase 3 派（重）：** `concurrency-auditor`，判重的理由是 actor\n- **Review 路線**：B\n"
        self.assertEqual(run_evals.gate_of(run_evals.screen_fields(screen)["Phase 3 派"]), "重")

    def test_wrong_scenario_fails(self):
        self.assertFalse(verdicts(dict(scenario="2"), REAL_SCREEN)["scenario"])

    def test_gate_per_ticket_and_missing_axis(self):
        screen = "情境＝新專案／大功能\n  Phase 3 派：依每張 ticket（情境 7）五條件決定\n  交棒：留在 `/ios-dev` Step 1\n"
        self.assertEqual(verdicts(dict(scenario="1", content_axis="不適用", gate=["重", "依每張 ticket"], handoff="留在"), screen),
                         dict(scenario=True, content_axis=True, gate=True, handoff=True))

    def test_null_fields_are_not_checked(self):
        self.assertEqual(verdicts(dict(scenario=None, gate=None), REAL_SCREEN), {})


class Fixtures(unittest.TestCase):
    def test_every_case_builds_a_clean_repo(self):
        with open(run_evals.CASES_FILE, encoding="utf-8") as fh:
            ids = [c["id"] for c in json.load(fh)["evals"]]
        for cid in ids:
            with tempfile.TemporaryDirectory() as d:
                files = fixtures.build(cid, d)
                self.assertIn("CLAUDE.md", files)
                self.assertEqual(run_evals.repo_changes(d), [], f"case {cid}")

    def test_repo_changes_sees_edits_and_commits(self):
        with tempfile.TemporaryDirectory() as d:
            fixtures.build(3, d)
            with open(os.path.join(d, "new.swift"), "w") as fh:
                fh.write("// x\n")
            self.assertEqual(run_evals.repo_changes(d), ["?? new.swift"])
            git = ["git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
            subprocess.run(git + ["add", "-A"], check=True)
            subprocess.run(git + ["commit", "-qm", "x"], check=True)
            self.assertEqual(run_evals.repo_changes(d), ["1 new commit(s)"])

    def test_fixture_docs_match_the_code(self):
        """What a fixture's ticket or log says exists must exist (case 7 once tested a fixture bug)."""
        import re
        with open(run_evals.CASES_FILE, encoding="utf-8") as fh:
            ids = [c["id"] for c in json.load(fh)["evals"]]
        for cid in ids:
            with tempfile.TemporaryDirectory() as d:
                fixtures.build(cid, d)
                for dp, _, fs in os.walk(d):
                    for f in fs:
                        if not f.endswith(".md") or ".git" in dp:
                            continue
                        text = open(os.path.join(dp, f), encoding="utf-8").read()
                        for path in re.findall(r"`(FixtureApp[^`]*?\.swift)`（編輯）", text):
                            self.assertTrue(os.path.exists(os.path.join(d, path)), f"case {cid}: {f} edits missing {path}")
                        for path in re.findall(r"repo `(docs/[^`]+\.md)`", text):
                            self.assertTrue(os.path.exists(os.path.join(d, path)), f"case {cid}: {f} refers to missing {path}")
                        for sym in re.findall(r"`(\w+)` protocol 與 `(\w+)` 注入點已建立", text):
                            for name in sym:
                                hit = subprocess.run(["grep", "-rq", name, os.path.join(d, "FixtureApp")]).returncode == 0
                                self.assertTrue(hit, f"case {cid}: log claims {name} exists")
                        if f.startswith("T") and "feature:" in text:
                            self.assertNotIn("MultiLicense", text if "watchdog" in text else "", f"case {cid}: {f} carries another feature's metadata")

    def test_case_1_has_no_agent_skills_block(self):
        with tempfile.TemporaryDirectory() as d:
            fixtures.build(1, d)
            with open(os.path.join(d, "CLAUDE.md"), encoding="utf-8") as fh:
                self.assertNotIn("## Agent skills", fh.read())


if __name__ == "__main__":
    unittest.main()

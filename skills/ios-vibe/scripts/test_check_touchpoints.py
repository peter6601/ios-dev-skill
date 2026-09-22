#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-touchpoints.py 的測試：用暫存目錄造假的 skill 檔與假的例外表。"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location("check_touchpoints", os.path.join(HERE, "check-touchpoints.py"))
ct = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ct)

MARK = "<!-- touchpoint: {id} kind={kind} -->"
NONE = "<!-- touchpoint: none -->"


class Base(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="touchpoints-test-")
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)

    def write(self, relpath, text):
        path = os.path.join(self.repo, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def skill(self, name, text, filename="SKILL.md"):
        return self.write(os.path.join("skills", name, filename), text)

    def run_check(self, *extra, skills="fake-skill", registry_skills=""):
        argv = ["--repo", self.repo, "--skills", skills, "--registry-skills", registry_skills]
        argv += list(extra)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ct.main(argv)
        return code, buf.getvalue()


class MissingMarkerTests(Base):
    def test_keyword_line_with_marker_above_passes(self):
        self.skill("fake-skill", "\n".join([
            "# 假 skill",
            "",
            MARK.format(id="fake-skill-001", kind="product"),
            "列完之後**停下來**問使用者要不要調整。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)
        self.assertNotIn("error", out)

    def test_keyword_line_without_marker_fails(self):
        self.skill("fake-skill", "\n".join([
            "# 假 skill",
            "",
            "列完之後**停下來**問使用者要不要調整。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("skills/fake-skill/SKILL.md:3", out)

    def test_none_exempts_a_false_positive(self):
        self.skill("fake-skill", "\n".join([
            "# 假 skill",
            "",
            NONE,
            "這裡的「人工」指的是人工 X 天的估時單位。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)
        self.assertIn("none 豁免 1 個", out)

    def test_marker_more_than_three_lines_above_fails(self):
        self.skill("fake-skill", "\n".join([
            "# 假 skill",
            "",
            MARK.format(id="fake-skill-001", kind="product"),
            "第一句。",
            "",
            "另一段。",
            "",
            "這段會停下來問使用者。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn(":8", out)

    def test_marker_before_paragraph_covers_the_whole_paragraph(self):
        self.skill("fake-skill", "\n".join([
            "# 假 skill",
            "",
            MARK.format(id="fake-skill-001", kind="gate"),
            "這一段很長，第一行先講別的，",
            "第二行也還在講別的，",
            "第三行才說人工核准前不得 commit。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)

    def test_table_needs_one_marker_per_hit_row(self):
        table = "\n".join([
            "# 假 skill",
            "",
            MARK.format(id="fake-skill-001", kind="product"),
            "| 情況 | 怎麼做 |",
            "|---|---|",
            "| 範圍不清 | stop + 問使用者 |",
            "| 規格衝突 | stop + 問使用者 |",
            "",
        ])
        self.skill("fake-skill", table)
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("這張表格有 2 列", out)

        self.skill("fake-skill", table.replace(
            MARK.format(id="fake-skill-001", kind="product"),
            MARK.format(id="fake-skill-001", kind="product") + "\n" + MARK.format(id="fake-skill-002", kind="mixed"),
        ))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)

    def test_code_block_marker_inside_or_before_the_fence(self):
        inside = "\n".join([
            "# 假 skill",
            "",
            "```",
            "Step 1. 做事",
            "  │  " + MARK.format(id="fake-skill-001", kind="engineering"),
            "  └─ STOP，等使用者 review 大綱",
            "```",
            "",
        ])
        self.skill("fake-skill", inside)
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)

        before = "\n".join([
            "# 假 skill",
            "",
            MARK.format(id="fake-skill-001", kind="engineering"),
            "```",
            "Step 1. 做事",
            "  └─ STOP，等使用者 review 大綱",
            "```",
            "",
        ])
        self.skill("fake-skill", before)
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)

        bare = before.replace(MARK.format(id="fake-skill-001", kind="engineering") + "\n", "")
        self.skill("fake-skill", bare)
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("code block", out)

    def test_html_comment_block_marker_goes_before_the_comment(self):
        self.skill("fake-skill", "\n".join([
            "# 假 skill",
            "",
            MARK.format(id="fake-skill-001", kind="mixed"),
            "<!-- 這一段是給填模板的人看的。",
            "會擋 Stage 1–2 的，Step 3 STOP 時就問使用者。 -->",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)

    def test_frontmatter_is_not_scanned(self):
        self.skill("fake-skill", "\n".join([
            "---",
            "name: fake-skill",
            "description: 需要判斷的批次詢問，會停下來問使用者",
            "---",
            "",
            "# 假 skill",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)

    def test_reference_files_are_scanned_too(self):
        self.skill("fake-skill", "# 假 skill\n")
        self.write("skills/fake-skill/references/guide.md", "先停下來問使用者要不要繼續。\n")
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("references/guide.md:1", out)


class MarkerFormatTests(Base):
    def test_bad_kind_is_reported(self):
        self.skill("fake-skill", "\n".join([
            MARK.format(id="fake-skill-001", kind="ui-review"),
            "停下來問使用者。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("kind=`ui-review` 不是合法的種類", out)

    def test_duplicate_id_is_reported(self):
        self.skill("fake-skill", "\n".join([
            MARK.format(id="fake-skill-001", kind="product"),
            "停下來問使用者甲。",
            "",
            MARK.format(id="fake-skill-001", kind="product"),
            "停下來問使用者乙。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("重複", out)

    def test_malformed_marker_is_reported(self):
        self.skill("fake-skill", "\n".join([
            "<!-- touchpoint: fake-skill-1 product -->",
            "停下來問使用者。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("格式", out)

    def test_prefix_must_match_the_skill_folder(self):
        self.skill("fake-skill", "\n".join([
            MARK.format(id="other-skill-001", kind="product"),
            "停下來問使用者。",
            "",
        ]))
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("前綴", out)


class RulesTests(Base):
    def setUp(self):
        super().setUp()
        self.skill("fake-skill", "\n".join([
            MARK.format(id="fake-skill-001", kind="gate"),
            "人工核准前不得 commit。",
            "",
            MARK.format(id="fake-skill-002", kind="product"),
            "停下來問使用者這要給誰用。",
            "",
        ]))

    def rules(self, body):
        return self.write("skills/ios-vibe/references/touchpoint-rules.md", body)

    def test_missing_rules_file_only_warns(self):
        code, out = self.run_check("--rules", os.path.join(self.repo, "nope.md"))
        self.assertEqual(code, 0, out)
        self.assertIn("warn", out)
        self.assertIn("跳過第 3、4 項", out)

    def test_gate_without_a_row_fails(self):
        path = self.rules("\n".join([
            "# 接觸點規則",
            "",
            "## 例外表",
            "",
            "| ios-dev 的點 | vibe 版怎麼做 |",
            "|---|---|",
            "| `fake-skill-002` 問給誰用 | 白話問 |",
            "",
        ]))
        code, out = self.run_check("--rules", path)
        self.assertEqual(code, 1, out)
        self.assertIn("`fake-skill-001` 是 kind=gate", out)

    def test_gate_with_a_row_passes(self):
        path = self.rules("\n".join([
            "# 接觸點規則",
            "",
            "## 例外表",
            "",
            "| ios-dev 的點 | vibe 版怎麼做 |",
            "|---|---|",
            "| `fake-skill-001`、`fake-skill-002` | 工作分支可以自動存 local commit |",
            "",
        ]))
        code, out = self.run_check("--rules", path)
        self.assertEqual(code, 0, out)

    def test_rules_row_pointing_at_a_missing_marker_fails(self):
        path = self.rules("\n".join([
            "# 接觸點規則",
            "",
            "## 例外表",
            "",
            "| ios-dev 的點 | vibe 版怎麼做 |",
            "|---|---|",
            "| `fake-skill-001` | 照舊 |",
            "| `fake-skill-404` | 照舊 |",
            "",
        ]))
        code, out = self.run_check("--rules", path)
        self.assertEqual(code, 1, out)
        self.assertIn("`fake-skill-404`", out)
        self.assertIn("沒有這個標記", out)

    def test_ids_outside_the_exception_table_are_ignored(self):
        path = self.rules("\n".join([
            "# 接觸點規則",
            "",
            "## 四條規則",
            "",
            "| 編號 | 說明 |",
            "|---|---|",
            "| `fake-skill-999` | 這張表不是例外表 |",
            "",
            "## 例外表",
            "",
            "| ios-dev 的點 | vibe 版怎麼做 |",
            "|---|---|",
            "| `fake-skill-001` | 照舊 |",
            "",
        ]))
        code, out = self.run_check("--rules", path)
        self.assertEqual(code, 0, out)


class RegistryOnlyTests(Base):
    def test_registry_skill_is_not_keyword_scanned_but_ids_count(self):
        self.skill("fake-skill", "\n".join([
            MARK.format(id="fake-skill-001", kind="product"),
            "停下來問使用者。",
            "",
        ]))
        self.skill("vibe-like", "\n".join([
            "# 規則說明（這份檔整篇都在講停下來問使用者、人工核准、不得 commit）",
            "",
            MARK.format(id="vibe-like-001", kind="product"),
            "第一次使用時問使用者要 a 還是 b。",
            "",
            "格式長這樣：",
            "",
            "```markdown",
            MARK.format(id="fake-skill-001", kind="gate"),
            "```",
            "",
        ]))
        code, out = self.run_check(
            "--rules", os.path.join(self.repo, "nope.md"), registry_skills="vibe-like"
        )
        self.assertEqual(code, 0, out)  # 沒有漏標錯誤，也沒有把範例當成重複編號
        self.assertIn("標記 2 個", out)


class LogTests(Base):
    def setUp(self):
        super().setUp()
        self.skill("fake-skill", "\n".join([
            MARK.format(id="fake-skill-001", kind="product"),
            "停下來問使用者這要給誰用。",
            "",
        ]))

    def log(self, entries):
        path = os.path.join(self.repo, "touchpoint-log.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for e in entries:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        return path

    def test_known_ids_pass(self):
        path = self.log([{"id": "fake-skill-001", "question": "這個 app 給誰用？"}])
        code, out = self.run_check("--log", path)
        self.assertEqual(code, 0, out)
        self.assertIn("問題 0 個", out)

    def test_unmapped_is_reported_with_the_question(self):
        path = self.log([{"id": "unmapped", "question": "要不要順便加一個匯出功能？"}])
        code, out = self.run_check("--log", path)
        self.assertEqual(code, 1, out)
        self.assertIn("unmapped", out)
        self.assertIn("要不要順便加一個匯出功能？", out)

    def test_unknown_id_is_reported(self):
        path = self.log([{"id": "fake-skill-404", "question": "這題問什麼"}])
        code, out = self.run_check("--log", path)
        self.assertEqual(code, 1, out)
        self.assertIn("找不到對應的標記", out)

    def test_missing_fields_and_broken_json(self):
        path = os.path.join(self.repo, "touchpoint-log.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write('{"question": "沒有 id"}\n')
            fh.write('{"id": "fake-skill-001"}\n')
            fh.write("這行不是 JSON\n")
        code, out = self.run_check("--log", path)
        self.assertEqual(code, 1, out)
        self.assertIn("沒有 id 欄位", out)
        self.assertIn("沒有 question 欄位", out)
        self.assertIn("不是合法 JSON", out)

    def test_missing_log_file_is_an_error(self):
        code, out = self.run_check("--log", os.path.join(self.repo, "nope.jsonl"))
        self.assertEqual(code, 1, out)
        self.assertIn("找不到執行期紀錄", out)


if __name__ == "__main__":
    unittest.main()

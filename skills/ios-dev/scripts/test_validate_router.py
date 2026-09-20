#!/usr/bin/env python3
"""Tests for validate-router.py — every check, plus the two bugs hit while writing it
(2026-09-19): slash commands read as absolute paths, and fenced blocks skipped by the
path check.

Run: python3 skills/ios-dev/scripts/test_validate_router.py
"""
import json, os, subprocess, sys, tempfile, unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validate-router.py")

SKILL = """---
name: ios-dev
description: entry point
---
讀 `references/skill-router.md` §0，交棒附 `references/handoff-checklist.md` 的「共通收尾」。
用 `/ios-dev` 進場，計畫走 `/writing-plans`，根文件是 `overview.md`。
"""

ROUTER = """# Router
## 0. Step 0
照 §9 檢查；收尾見 `handoff-checklist.md` §3。
## 9. 本表引用的名字
- 自家 skill（workspace `skills/`）：`ios-dev`、`ios-review`
- 第三方 skill（`~/.claude/skills`）：`swift-concurrency`、`asc-*` 2 個
- plugin：`superpowers:writing-plans`
- agent（`~/.claude/agents`）：`ux-critique`
"""

HANDOFF = """# Handoff
## 共通收尾（每個情境都跑）
輕重照 router §0。
## §3 純呈現畫面
"""


def write(path, body=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)


class Fixture:
    """A fake workspace, ~/.claude and plugin cache that pass every check."""

    def __init__(self, root):
        self.root = root
        self.ws = os.path.join(root, "ws")
        self.home = os.path.join(root, "home")
        self.skill = os.path.join(self.ws, "skills", "ios-dev")
        write(os.path.join(self.skill, "SKILL.md"), SKILL)
        write(os.path.join(self.skill, "references", "skill-router.md"), ROUTER)
        write(os.path.join(self.skill, "references", "handoff-checklist.md"), HANDOFF)
        write(os.path.join(self.ws, "skills", "ios-review", "SKILL.md"))
        os.makedirs(os.path.join(self.home, "commands"))
        for name in ("ios-dev", "ios-review"):
            os.symlink(os.path.join(self.ws, "skills", name), os.path.join(self.home, "commands", name))
        for name in ("swift-concurrency", "asc-a", "asc-b"):
            write(os.path.join(self.home, "skills", name, "SKILL.md"))
        write(os.path.join(self.home, "agents", "ux-critique.md"))
        plugin = os.path.join(root, "plugin")
        write(os.path.join(plugin, "skills", "writing-plans", "SKILL.md"))
        write(os.path.join(self.home, "plugins", "installed_plugins.json"),
              json.dumps({"plugins": {"superpowers@mkt": [{"installPath": plugin}]}}))

    def doc(self, rel):
        return os.path.join(self.skill, rel)

    def append(self, rel, text):
        with open(self.doc(rel), "a", encoding="utf-8") as f:
            f.write(text)

    def replace(self, rel, old, new):
        with open(self.doc(rel), encoding="utf-8") as f:
            body = f.read()
        assert old in body, old
        write(self.doc(rel), body.replace(old, new))

    def run(self, *args, env=None):
        p = subprocess.run([sys.executable, SCRIPT, "--skill-dir", self.skill, "--workspace", self.ws,
                            "--claude-home", self.home, "--json", *args],
                           capture_output=True, text=True, env=env)
        return p.returncode, json.loads(p.stdout)


class ValidateRouter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(os.path.realpath(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self, check, *args, **kw):
        code, out = self.fx.run(*args, **kw)
        return code, [e["message"] for e in out["errors"] if e["check"] == check]

    def test_clean_fixture_passes(self):
        code, out = self.fx.run()
        self.assertEqual((code, out["errors"], out["warnings"]), (0, [], []))
        # `/ios-dev` is absolute by syntax only — it must be counted as a command, never as a path
        self.assertEqual(out["checked"]["slash"], 2)

    def test_declared_agent_missing(self):
        os.remove(os.path.join(self.fx.home, "agents", "ux-critique.md"))
        code, msgs = self.errors("declared")
        self.assertEqual(code, 1)
        self.assertIn("ux-critique", msgs[0])

    def test_workspace_skill_without_symlink(self):
        os.remove(os.path.join(self.fx.home, "commands", "ios-review"))
        code, msgs = self.errors("declared")
        self.assertEqual(code, 1)
        self.assertIn("not linked", msgs[0])

    def test_broken_symlink(self):
        os.symlink(os.path.join(self.fx.root, "gone"), os.path.join(self.fx.home, "commands", "old-skill"))
        code, msgs = self.errors("declared")
        self.assertEqual((code, msgs), (1, ["broken symlink"]))

    def test_asc_count_mismatch(self):
        self.fx.replace("references/skill-router.md", "`asc-*` 2 個", "`asc-*` 10 個")
        code, msgs = self.errors("declared")
        self.assertEqual(code, 1)
        self.assertIn("2 installed", msgs[0])

    def test_plugin_skill_missing(self):
        self.fx.replace("references/skill-router.md", "superpowers:writing-plans", "superpowers:no-such-skill")
        code, msgs = self.errors("declared")
        self.assertEqual(code, 1)
        self.assertIn("has no skill", msgs[0])

    def test_slash_command_unresolved(self):
        self.fx.append("SKILL.md", "再跑 `/not-a-skill --flag`。\n")
        code, msgs = self.errors("slash")
        self.assertEqual(code, 1)
        self.assertIn("/not-a-skill", msgs[0])

    def test_section_numbers(self):
        self.fx.append("SKILL.md", "見 router §11 與 `handoff-checklist.md` §8。\n")
        code, msgs = self.errors("section")
        self.assertEqual(code, 1)
        self.assertEqual(len(msgs), 2)
        self.assertIn("skill-router.md", msgs[0])
        self.assertIn("handoff-checklist.md", msgs[1])

    def test_section_title(self):
        self.fx.append("SKILL.md", "照 `handoff-checklist.md` 的「不存在的段」。\n")
        code, msgs = self.errors("title")
        self.assertEqual(code, 1)
        self.assertIn("不存在的段", msgs[0])

    def test_paths(self):
        self.fx.append("SKILL.md", "讀 `references/missing.md`、`gone-file.md`、`docs/plans/<feature>.md`。\n")
        code, msgs = self.errors("path")
        self.assertEqual(code, 1)
        self.assertEqual(len(msgs), 2)  # the placeholder path and `overview.md` are not checked

    def test_absolute_path_inside_fence_warns(self):
        target = self.fx.doc("references/handoff-checklist.md")
        self.fx.append("references/skill-router.md", f"```markdown\n來源 `{target}`\n```\n")
        code, out = self.fx.run(env=dict(os.environ, HOME=self.fx.root))
        self.assertEqual(code, 0)
        self.assertEqual([w["check"] for w in out["warnings"]], ["path"])

    def test_undeclared_name_warns_and_strict_fails(self):
        write(os.path.join(self.fx.home, "agents", "perf-auditor.md"))
        self.fx.append("SKILL.md", "改前派 `perf-auditor`，CLI 是 `ai-review`。\n")
        code, out = self.fx.run()
        self.assertEqual((code, len(out["warnings"])), (0, 1))
        self.assertIn("not listed in router §9", out["warnings"][0]["message"])
        self.assertEqual(self.fx.run("--strict")[0], 1)

    def test_frontmatter_name(self):
        self.fx.replace("SKILL.md", "name: ios-dev", "name: ios-develop")
        code, msgs = self.errors("frontmatter")
        self.assertEqual(code, 1)
        self.assertIn("ios-develop", msgs[0])

    # --- Codex review 2026-09-19: broken docs that used to validate clean ---
    def test_slash_command_inside_a_code_block(self):
        self.fx.append("references/skill-router.md", "```\n/ios-dev tickets/T1.md\n/definitely-missing <x>\n```\n")
        code, msgs = self.errors("slash")
        self.assertEqual(code, 1)
        self.assertEqual(len(msgs), 1)
        self.assertIn("/definitely-missing", msgs[0])

    def test_path_with_a_space_is_still_checked(self):
        self.fx.append("SKILL.md", "見 `references/no such.md`。\n")
        code, msgs = self.errors("path")
        self.assertEqual(code, 1)
        self.assertIn("no such.md", msgs[0])

    def test_absolute_path_under_a_missing_root(self):
        self.fx.append("SKILL.md", "見 `/definitely-no-root/no.md`，但 `/consensus-review --profile ios` 是指令。\n")
        code, msgs = self.errors("path")
        self.assertEqual(code, 1)
        self.assertEqual(len(msgs), 1)
        self.assertIn("/definitely-no-root/no.md", msgs[0])

    def test_bare_section_in_handoff_must_be_its_own(self):
        self.fx.append("references/handoff-checklist.md", "收尾照 §9，架構以根文件 §0 架構形狀為準。\n")
        code, msgs = self.errors("section")
        self.assertEqual(code, 1)
        self.assertEqual(len(msgs), 1)  # §9 is the router's; §0 架構形狀 is the design doc's and is skipped
        self.assertIn("§9", msgs[0])

    def test_bullet_listing_skills_and_agents_together(self):
        """`skill …；agent …` in one bullet: each name is checked where its own keyword says."""
        self.fx.replace("references/skill-router.md", "- agent（`~/.claude/agents`）：`ux-critique`",
                        "- 第三方 skill `swift-concurrency`；agent `ux-critique`")
        self.assertEqual(self.fx.run()[0], 0)
        os.remove(os.path.join(self.fx.home, "agents", "ux-critique.md"))
        code, msgs = self.errors("declared")
        self.assertEqual(code, 1)
        self.assertTrue(any("~/.claude/agents" in m for m in msgs), msgs)

    def test_published_wording_resolves_against_the_repo(self):
        """The published copy words §9 as 「本 repo 附的」: skills ship in the repo, not in a workspace."""
        self.fx.replace("references/skill-router.md",
                        "- 自家 skill（workspace `skills/`）：`ios-dev`、`ios-review`",
                        "- **本 repo 附的**：skill `ios-dev`、`ios-review`；agent `ux-critique`")
        self.fx.replace("references/skill-router.md", "- agent（`~/.claude/agents`）：`ux-critique`",
                        "- **共識審查**（另一個 repo）：`consensus-review`")
        self.assertEqual(self.fx.run()[0], 0)
        os.remove(os.path.join(self.fx.ws, "skills", "ios-review", "SKILL.md"))
        os.remove(os.path.join(self.fx.home, "commands", "ios-review"))
        code, msgs = self.errors("declared")
        self.assertEqual(code, 1)
        self.assertTrue(any("not shipped in this repo" in m for m in msgs), msgs)

    def test_missing_skill_md_is_bad_input(self):
        os.remove(self.fx.doc("SKILL.md"))
        code, out = self.fx.run()
        self.assertEqual((code, out["error"]), (2, "SKILL.md not found"))


if __name__ == "__main__":
    unittest.main()

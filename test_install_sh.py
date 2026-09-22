#!/usr/bin/env python3
"""install.sh 的 smoke test：語法、相依表、symlink 行為，在幾種 locale 下都要一致。

跑法：python3 test_install_sh.py
"""
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.abspath(__file__))
INSTALL = os.path.join(REPO, "install.sh")

# 這幾種 locale 都要過：macOS 終端機預設、明示 UTF-8、純 C。
LOCALES = [
    ("預設", {}),
    ("LANG=C.UTF-8", {"LANG": "C.UTF-8", "LC_ALL": ""}),
    ("LANG=zh_TW.UTF-8", {"LANG": "zh_TW.UTF-8", "LC_ALL": ""}),
    ("LC_ALL=C", {"LC_ALL": "C", "LANG": "C"}),
]


def run(args, claude_home, extra_env=None):
    env = dict(os.environ)
    env["CLAUDE_HOME"] = claude_home
    env.pop("LC_ALL", None)
    env.pop("LANG", None)
    if extra_env:
        for k, v in extra_env.items():
            if v == "":
                env.pop(k, None)
            else:
                env[k] = v
    return subprocess.run(
        ["/bin/bash", INSTALL] + args,
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
    )


class TestSyntax(unittest.TestCase):
    def test_bash_n(self):
        r = subprocess.run(["/bin/bash", "-n", INSTALL], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


class TestCheck(unittest.TestCase):
    def test_check_runs_clean_in_every_locale(self):
        for label, env in LOCALES:
            with self.subTest(locale=label):
                home = tempfile.mkdtemp()
                try:
                    r = run(["--check"], home, env)
                finally:
                    shutil.rmtree(home, ignore_errors=True)
                self.assertNotIn("unbound variable", r.stderr)
                self.assertNotIn("unbound variable", r.stdout)
                self.assertEqual(r.returncode, 0, r.stderr)
                # 相依表要完整印出來，不能中途中止
                self.assertIn("swiftui-expert-skill", r.stdout)
                self.assertIn("spm-build-analysis", r.stdout)

    def test_check_does_not_touch_files(self):
        home = tempfile.mkdtemp()
        try:
            run(["--check"], home)
            self.assertEqual(os.listdir(home), [])
        finally:
            shutil.rmtree(home, ignore_errors=True)


class TestInstall(unittest.TestCase):
    def test_install_then_uninstall(self):
        home = tempfile.mkdtemp()
        try:
            r = run([], home)
            self.assertNotIn("unbound variable", r.stderr)
            self.assertEqual(r.returncode, 0, r.stderr)
            link = os.path.join(home, "skills", "ios-dev")
            self.assertTrue(os.path.islink(link))
            self.assertEqual(os.readlink(link), os.path.join(REPO, "skills", "ios-dev"))

            r = run(["--uninstall"], home)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(os.path.lexists(link))
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_existing_foreign_target_is_skipped_not_overwritten(self):
        """跳過分支的訊息也有變數緊鄰全形字元，一樣要能印出來。"""
        for label, env in LOCALES:
            with self.subTest(locale=label):
                home = tempfile.mkdtemp()
                try:
                    foreign = os.path.join(home, "skills", "ios-dev")
                    os.makedirs(foreign)
                    marker = os.path.join(foreign, "SKILL.md")
                    with open(marker, "w") as fh:
                        fh.write("not ours\n")
                    r = run([], home, env)
                    self.assertNotIn("unbound variable", r.stderr)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertIn("跳過", r.stdout)
                    with open(marker) as fh:
                        self.assertEqual(fh.read(), "not ours\n")
                finally:
                    shutil.rmtree(home, ignore_errors=True)


class TestHasSkill(unittest.TestCase):
    """相依檢查要認得 Claude Code 的三種安裝形狀。"""

    def _check_line(self, layout):
        home = tempfile.mkdtemp()
        try:
            for rel, content in layout.items():
                path = os.path.join(home, rel)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as fh:
                    fh.write(content)
            r = run(["--check"], home)
            self.assertEqual(r.returncode, 0, r.stderr)
            for line in r.stdout.splitlines():
                if "swift-concurrency" in line:
                    return line
            self.fail("相依表沒有 swift-concurrency 這列")
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_skills_directory(self):
        self.assertIn("✓", self._check_line({"skills/swift-concurrency/SKILL.md": "x"}))

    def test_commands_directory(self):
        """作者機器上的形狀：commands/<name>/ 是 symlink 目錄，Claude Code 讀得到。"""
        self.assertIn("✓", self._check_line({"commands/swift-concurrency/SKILL.md": "x"}))

    def test_flat_legacy_command(self):
        """官方 legacy command 形狀：commands/<name>.md。"""
        self.assertIn("✓", self._check_line({"commands/swift-concurrency.md": "x"}))

    def test_absent(self):
        self.assertIn("✗", self._check_line({}))


FAKE_BIN = """#!/bin/bash
echo "$(basename "$0") $*" >> "$FAKE_LOG"
if [ "$(basename "$0")" = "claude" ] && [ "$1" = "mcp" ] && [ "$2" = "get" ]; then
  [ -f "$FAKE_MCP_PRESENT" ] && exit 0
  exit 1
fi
if [ "$(basename "$0")" = "claude" ] && [ "$1" = "mcp" ] && [ "$2" = "add" ]; then
  touch "$FAKE_MCP_PRESENT"
fi
exit 0
"""


class TestVibe(unittest.TestCase):
    """--vibe 流程：先列清單、要同意才動、寫入的全域路由可以乾淨移除。npx／claude 換成假指令。"""

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.bindir = tempfile.mkdtemp()
        self.log = os.path.join(self.bindir, "calls.log")
        for name in ("npx", "claude"):
            path = os.path.join(self.bindir, name)
            with open(path, "w") as fh:
                fh.write(FAKE_BIN)
            os.chmod(path, 0o755)
        self.env = {
            "NPX_BIN": os.path.join(self.bindir, "npx"),
            "CLAUDE_BIN": os.path.join(self.bindir, "claude"),
            "VIBE_SKIP_PREREQ": "1",
            "FAKE_LOG": self.log,
            "FAKE_MCP_PRESENT": os.path.join(self.bindir, "mcp-present"),
        }

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.bindir, ignore_errors=True)

    def calls(self):
        if not os.path.exists(self.log):
            return ""
        with open(self.log) as fh:
            return fh.read()

    def routing(self):
        path = os.path.join(self.home, "CLAUDE.md")
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def test_dry_run_lists_plan_and_touches_nothing(self):
        r = run(["--vibe", "--dry-run"], self.home, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("vibe 版會做這些事", r.stdout)
        self.assertIn("swift-architecture-skill", r.stdout)
        self.assertIn("XcodeBuildMCP", r.stdout)
        self.assertEqual(os.listdir(self.home), [])
        self.assertNotIn("npx", self.calls())
        self.assertNotIn("plugin install", self.calls())

    def test_without_yes_and_no_tty_refuses(self):
        r = run(["--vibe"], self.home, self.env)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--yes", r.stdout)
        self.assertEqual(os.listdir(self.home), [])

    def test_dry_run_requires_vibe(self):
        r = run(["--dry-run"], self.home, self.env)
        self.assertEqual(r.returncode, 2)

    def test_yes_installs_everything_once(self):
        r = run(["--vibe", "--yes"], self.home, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("unbound variable", r.stderr)
        self.assertTrue(os.path.islink(os.path.join(self.home, "skills", "ios-vibe")))
        calls = self.calls()
        self.assertIn("npx skills add https://github.com/efremidze/swift-architecture-skill", calls)
        self.assertIn("--skill review-swarm", calls)
        self.assertIn("claude plugin install superpowers@claude-plugins-official", calls)
        self.assertIn("XCODEBUILDMCP_ENABLED_WORKFLOWS=simulator,simulator-management,ui-automation", calls)
        body = self.routing()
        self.assertEqual(body.count("ios-vibe:begin"), 1)
        self.assertIn("ios-vibe", body)

        # 第二次執行：路由不重複寫，MCP 已存在就不再加
        r = run(["--vibe", "--yes"], self.home, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.routing().count("ios-vibe:begin"), 1)
        self.assertEqual(self.calls().count("mcp add"), 1)

    def test_uninstall_removes_only_our_block(self):
        path = os.path.join(self.home, "CLAUDE.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# 我自己的設定\n\n保留這行\n")
        run(["--vibe", "--yes"], self.home, self.env)
        self.assertIn("ios-vibe:begin", self.routing())
        r = run(["--vibe", "--uninstall"], self.home, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        body = self.routing()
        self.assertNotIn("ios-vibe", body)
        self.assertIn("保留這行", body)
        self.assertFalse(os.path.lexists(os.path.join(self.home, "skills", "ios-vibe")))

    def test_vibe_check_touches_nothing(self):
        r = run(["--vibe", "--check"], self.home, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("vibe 版檢查", r.stdout)
        self.assertEqual(os.listdir(self.home), [])


class TestDepsListsAgree(unittest.TestCase):
    """install.sh 的相依表是唯一真相；README「相依一覽」與 router §9 不得漏名字。"""

    def _dep_names(self):
        with open(os.path.join(REPO, "install.sh"), encoding="utf-8") as fh:
            body = fh.read()
        block = body.split("DEPS='", 1)[1].split("'\n", 1)[0]
        names = []
        for line in block.splitlines():
            if not line.strip():
                continue
            names.append(line.split("|")[2])
        self.assertGreater(len(names), 10)
        return names

    def test_readme_lists_every_dep(self):
        with open(os.path.join(REPO, "README.md"), encoding="utf-8") as fh:
            readme = fh.read()
        for name in self._dep_names():
            with self.subTest(dep=name):
                self.assertIn("`" + name + "`", readme)

    def test_router_lists_every_skill_dep(self):
        router = os.path.join(REPO, "skills", "ios-dev", "references", "skill-router.md")
        with open(router, encoding="utf-8") as fh:
            body = fh.read()
        section = body.split("## 9. ", 1)[1].split("\n## 10.", 1)[0]
        with open(os.path.join(REPO, "install.sh"), encoding="utf-8") as fh:
            install = fh.read()
        block = install.split("DEPS='", 1)[1].split("'\n", 1)[0]
        for line in block.splitlines():
            if not line.strip():
                continue
            tier, kind, name, _ = line.split("|", 3)
            if kind != "skill":
                continue
            with self.subTest(dep=name):
                self.assertIn("`" + name + "`", section)


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""new-app.py 的測試。

跑法：
    python3 -m unittest discover -s skills/ios-vibe/scripts -p 'test_*.py'
 或 python3 skills/ios-vibe/scripts/test_new_app.py

重點：產出來的專案不能殘留任何 VibeApp 字樣（殘留代表某個檔案沒改到，
Xcode 會開不起來或 build 不過），而且第一個 commit 要做好。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(SCRIPT_DIR, "new-app.py")
BOUNDARIES = os.path.join(SCRIPT_DIR, "check-boundaries.py")


def run_new_app(destination, name="TestApp", prefix="com.example.vibe", env=None):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, SCRIPT, destination, name, prefix],
        capture_output=True, text=True, env=full_env,
    )


def isolated_git_env(tmpdir, identity=None):
    """把 git 的全域／系統設定隔離掉，測試才不會被這台電腦的設定影響。"""
    config = os.path.join(tmpdir, "gitconfig")
    with open(config, "w", encoding="utf-8") as handle:
        if identity:
            handle.write(f"[user]\n\tname = {identity[0]}\n\temail = {identity[1]}\n")
    return {"GIT_CONFIG_GLOBAL": config, "GIT_CONFIG_NOSYSTEM": "1"}


def git_out(path, *args):
    return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True).stdout.strip()


class GeneratesAProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.project = os.path.join(cls.tmp, "my-app")
        cls.result = run_new_app(cls.project, env=isolated_git_env(cls.tmp, ("測試員", "tester@example.com")))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_exits_cleanly(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr + self.result.stdout)

    def test_structure_is_renamed(self):
        for relative in [
            "TestApp.xcodeproj/project.pbxproj",
            "TestApp.xcodeproj/xcshareddata/xcschemes/TestApp.xcscheme",
            "TestApp/TestAppApp.swift",
            "TestApp/Data/DataBootstrapper.swift",
            "TestApp/Debug/NetworkBlocker.swift",
            "TestAppTests/DataBootstrapperTests.swift",
            "TestAppUITests/MainFlowUITests.swift",
            "CLAUDE.md",
            "AGENTS.md",
            ".gitignore",
        ]:
            self.assertTrue(
                os.path.exists(os.path.join(self.project, relative)),
                f"少了 {relative}",
            )

    def test_nothing_is_still_called_vibeapp(self):
        leftovers = []
        for dirpath, dirnames, filenames in os.walk(self.project):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for entry in dirnames + filenames:
                if "VibeApp" in entry:
                    leftovers.append(os.path.join(dirpath, entry))
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        text = handle.read()
                except (UnicodeDecodeError, OSError):
                    continue
                if "VibeApp" in text:
                    leftovers.append(path)
        self.assertEqual(leftovers, [], "還有地方叫 VibeApp")

    def test_bundle_ids_use_the_given_prefix(self):
        with open(os.path.join(self.project, "TestApp.xcodeproj/project.pbxproj"), encoding="utf-8") as handle:
            pbxproj = handle.read()
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER = com.example.vibe.TestApp;", pbxproj)
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER = com.example.vibe.TestAppTests;", pbxproj)
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER = com.example.vibe.TestAppUITests;", pbxproj)
        self.assertNotIn("com.example.TestApp", pbxproj)

    def test_docs_are_identical_and_mention_the_app(self):
        with open(os.path.join(self.project, "CLAUDE.md"), encoding="utf-8") as handle:
            claude = handle.read()
        with open(os.path.join(self.project, "AGENTS.md"), encoding="utf-8") as handle:
            agents = handle.read()
        self.assertEqual(claude, agents)
        self.assertIn("TestApp", claude)

    def test_first_commit_is_made_with_the_folders_own_identity(self):
        self.assertEqual(git_out(self.project, "rev-list", "--count", "HEAD"), "1")
        self.assertEqual(git_out(self.project, "log", "-1", "--format=%an <%ae>"), "測試員 <tester@example.com>")
        self.assertEqual(git_out(self.project, "status", "--porcelain"), "")

    def test_generated_project_passes_the_boundary_check(self):
        proc = subprocess.run(
            [sys.executable, BOUNDARIES, self.project], capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)


class GitIdentityFallback(unittest.TestCase):
    def test_uses_a_placeholder_identity_and_says_so(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        project = os.path.join(tmp, "app")
        result = run_new_app(project, env=isolated_git_env(tmp))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git_out(project, "log", "-1", "--format=%an <%ae>"), "ios-vibe <noreply@example.com>")
        self.assertIn("git 身分", result.stdout)


class RefusesBadInput(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_rejects_names_that_are_not_letters_and_digits(self):
        for name in ["My App", "9Lives", "money-log", "", "記帳", "App.Two"]:
            project = os.path.join(self.tmp, f"dest-{abs(hash(name))}")
            result = run_new_app(project, name=name)
            self.assertEqual(result.returncode, 2, f"「{name}」應該被擋下來")
            self.assertFalse(os.path.exists(project))

    def test_rejects_names_that_clash_with_the_template(self):
        for name in ["Entry", "DataFiles", "SwiftUI", "view"]:
            project = os.path.join(self.tmp, f"clash-{name}")
            result = run_new_app(project, name=name)
            self.assertEqual(result.returncode, 2, f"「{name}」應該被擋下來")

    def test_rejects_a_bad_bundle_prefix(self):
        project = os.path.join(self.tmp, "dest-prefix")
        result = run_new_app(project, prefix="com example!")
        self.assertEqual(result.returncode, 2)

    def test_refuses_to_write_into_a_folder_that_has_things_in_it(self):
        project = os.path.join(self.tmp, "busy")
        os.makedirs(project)
        with open(os.path.join(project, "使用者的檔案.txt"), "w", encoding="utf-8") as handle:
            handle.write("不要蓋掉我")
        result = run_new_app(project)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(os.path.exists(os.path.join(project, "使用者的檔案.txt")))


if __name__ == "__main__":
    unittest.main()

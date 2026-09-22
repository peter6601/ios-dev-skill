#!/usr/bin/env python3
"""Regression tests for check-careful-ios.sh — every row of SKILL.md's 防護清單 and 安全例外.

Run: python3 skills/careful-ios/bin/test_check_careful_ios.py

每一組 Warns／Allows 都跑兩次：Claude 模式（不帶參數，命中回 ask）與 Codex 模式
（--codex，命中回 deny）。兩個模式共用同一份案例，規則分叉會直接讓其中一邊失敗。
"""
import json, os, subprocess, unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-careful-ios.sh")


def run(command, codex=False):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    args = ["bash", SCRIPT] + (["--codex"] if codex else [])
    p = subprocess.run(args, input=payload, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    if not p.stdout.strip():
        return None
    out = json.loads(p.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse", out
    assert out["permissionDecision"] == ("deny" if codex else "ask"), out
    return out["permissionDecisionReason"]


class Mode:
    """CODEX = False 跑 Claude 模式；子類別設 True 就用同一份案例跑 --codex。"""
    CODEX = False

    def hook(self, command):
        return run(command, codex=self.CODEX)


class Warns(Mode, unittest.TestCase):
    def check(self, command, level):
        reason = self.hook(command)
        self.assertIsNotNone(reason, f"should warn: {command}")
        self.assertIn(level, reason, reason)

    def test_critical(self):
        for c in [
            "git push -f origin release/1.2.0",
            "git push --force origin main",
            "git push --force-with-lease origin feature/xxx",
            "git push origin +feature/xxx",
            "rm -rf MyApp.xcodeproj",
            "rm -rf MyApp.xcworkspace/",
            "rm MyApp.entitlements",
            "git reset --hard HEAD~3",
            "git checkout .",
            "git restore .",
            "git branch -D feature/unmerged",
        ]:
            self.check(c, "CRITICAL")

    def test_protected_branch_is_named(self):
        self.assertIn("保護分支", self.hook("git push -f origin release/1.2.0"))
        self.assertNotIn("保護分支", self.hook("git push -f origin feature/maintenance"))

    def test_destructive(self):
        for c in [
            "rm -rf Sources/",
            "rm -fr ./Sources",
            "rm -r -f Sources",
            "xcrun simctl erase all",
            "xcrun simctl delete all",
            "security delete-generic-password -s myservice",
            "rm ~/Library/MobileDevice/Provisioning\\ Profiles/abc.mobileprovision",
            "pod deintegrate",
            'sqlite3 app.db "DROP TABLE users;"',
        ]:
            self.check(c, "DESTRUCTIVE")

    def test_caution(self):
        for c in [
            "rm -rf ~/Library/Developer/Xcode/DerivedData",
            "swift package reset",
            "defaults delete com.example.myapp",
        ]:
            self.check(c, "CAUTION")

    def test_compound_command_reports_the_worst(self):
        reason = self.hook("cd app && swift package reset && git reset --hard")
        self.assertIn("CRITICAL", reason)
        self.assertIn("另有 1 項", reason)

    def test_prefixes_are_seen_through(self):
        self.check("sudo rm -rf Sources", "DESTRUCTIVE")
        self.check("FOO=1 git reset --hard", "CRITICAL")

    def test_unbalanced_quotes_fall_back_to_regex(self):
        self.check("git reset --hard 'oops", "CRITICAL")

    def test_shell_wrapper_is_looked_inside(self):
        """`bash -c '...'` 以前整段靜默放行。"""
        self.check("bash -c 'git reset --hard'", "CRITICAL")
        self.check('sh -c "rm -rf Sources"', "DESTRUCTIVE")
        self.check("zsh -c 'git push -f origin main'", "CRITICAL")
        self.check("bash -lc 'git reset --hard'", "CRITICAL")

    def test_wrapper_options_are_stripped(self):
        """`sudo -u root` 的 `-u root` 以前被當成指令本體。"""
        self.check("sudo -u root git reset --hard", "CRITICAL")
        self.check("env -i git reset --hard", "CRITICAL")
        self.check("nice -n 10 git reset --hard", "CRITICAL")

    def test_nested_wrappers_terminate(self):
        self.check("bash -c \"sh -c 'git reset --hard'\"", "CRITICAL")
        deep = "git reset --hard"
        for _ in range(8):
            deep = "bash -c " + json.dumps(deep)
        self.hook(deep)  # 遞迴要有上限：深到看不見也只是放行，不能掛掉或吃光 CPU

    def test_git_whole_tree_pathspec(self):
        for c in ["git restore :/", "git checkout :/", "git checkout -- .", "git restore ./"]:
            self.check(c, "CRITICAL")

    def test_safe_rm_name_buried_in_a_path_is_not_safe(self):
        """白名單只看 basename 時，真的叫 build/dist 的 source 目錄會被靜靜刪掉。"""
        for c in [
            "rm -rf /tmp/app/Sources/build",
            "rm -rf ~/Projects/MyApp/Sources/dist",
            "rm -rf src/coverage",
            "rm -rf Modules/Feature/build",
        ]:
            self.check(c, "DESTRUCTIVE")

    def test_sql_through_a_real_db_client(self):
        self.check('sqlite3 db.sqlite "DROP TABLE users"', "DESTRUCTIVE")
        self.check("printf 'DROP TABLE users' | sqlite3 db.sqlite", "DESTRUCTIVE")


class Allows(Mode, unittest.TestCase):
    def test_safe_rm_targets(self):
        """相對路徑第一段就是 cache 目錄，或位於已知 cache root 底下。"""
        for c in [
            "rm -rf DerivedData",
            "rm -rf ./Pods",
            "rm -rf .build",
            "rm -rf build/SourcePackages",
            "rm -rf node_modules dist coverage",
            "rm -rf .build/checkouts",
            "rm -rf ~/Library/Developer/Xcode/DerivedData/MyApp-abc123",
            "rm -rf MyApp.xcodeproj/xcuserdata",
            "rm -rf MyApp.xcworkspace/xcuserdata/alice.xcuserdatad",
            "rm -rf .build/artifacts/SourcePackages",
        ]:
            self.assertIsNone(self.hook(c), c)

    def test_ordinary_commands(self):
        for c in [
            "git status",
            "git push origin feature/xxx",
            "git checkout -b feature/new",
            "git branch -d merged-branch",
            "git restore --staged file.swift",
            "rm notes.txt",
            "xcrun simctl list",
            "defaults read com.example.myapp",
            "xcodebuild test -scheme App",
            'echo "git reset --hard is dangerous"',
            "git restore --staged file.swift",
            "bash -c 'git status'",
            "bash scripts/build.sh",
        ]:
            self.assertIsNone(self.hook(c), c)

    def test_sql_keywords_in_plain_output_are_not_destructive(self):
        """grep／echo 提到 SQL 關鍵字不是破壞性動作。"""
        for c in [
            "echo 'DROP TABLE users'",
            "rg TRUNCATE",
            'grep -rn "DROP TABLE" .',
            'printf "TRUNCATE TABLE x"',
        ]:
            self.assertIsNone(self.hook(c), c)

    def test_garbage_input_is_let_through(self):
        args = ["bash", SCRIPT] + (["--codex"] if self.CODEX else [])
        p = subprocess.run(args, input="not json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.strip(), "")


class WarnsCodex(Warns):
    """同一份命中案例，--codex 下全部變成 deny。"""
    CODEX = True


class AllowsCodex(Allows):
    """同一份放行案例，--codex 下仍全部放行。"""
    CODEX = True


class ClaudeOutputUnchanged(unittest.TestCase):
    """不帶 --codex 的輸出要和加 Codex 模式之前一字不差。"""

    def test_exact_payload(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}})
        p = subprocess.run(["bash", SCRIPT], input=payload, capture_output=True, text=True)
        self.assertEqual(json.loads(p.stdout), {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "[careful-ios] 🚨 CRITICAL：git reset --hard：永久丟失未 commit 的變更。",
            }
        })

    def test_unknown_argument_does_not_switch_mode(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}})
        p = subprocess.run(["bash", SCRIPT, "--something"], input=payload, capture_output=True, text=True)
        self.assertEqual(json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")


class CodexReason(unittest.TestCase):
    """Codex 模式的理由要讓不懂指令的人看得懂：擋了什麼、為什麼、要做請自己來。"""

    def test_reason_says_what_why_and_who(self):
        reason = run("git reset --hard HEAD~3", codex=True)
        self.assertIn("已擋下", reason)
        self.assertIn("擋下的指令：git reset --hard HEAD~3", reason)
        self.assertIn("原因：git reset --hard：永久丟失未 commit 的變更。", reason)
        self.assertIn("請使用者自己在終端機執行", reason)

    def test_worst_hit_and_count_are_kept(self):
        reason = run("cd app && swift package reset && git reset --hard", codex=True)
        self.assertIn("CRITICAL", reason)
        self.assertIn("另有 1 項", reason)

    def test_long_command_is_truncated(self):
        reason = run("git reset --hard " + "x" * 1000, codex=True)
        self.assertIn("…", reason)
        self.assertLess(len(reason), 700)


if __name__ == "__main__":
    unittest.main()

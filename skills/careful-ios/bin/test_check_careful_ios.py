#!/usr/bin/env python3
"""Regression tests for check-careful-ios.sh — every row of SKILL.md's 防護清單 and 安全例外.

Run: python3 skills/careful-ios/bin/test_check_careful_ios.py
"""
import json, os, subprocess, unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-careful-ios.sh")


def run(command):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    p = subprocess.run(["bash", SCRIPT], input=payload, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    if not p.stdout.strip():
        return None
    out = json.loads(p.stdout)["hookSpecificOutput"]
    assert out["permissionDecision"] == "ask"
    return out["permissionDecisionReason"]


class Warns(unittest.TestCase):
    def check(self, command, level):
        reason = run(command)
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
        self.assertIn("保護分支", run("git push -f origin release/1.2.0"))
        self.assertNotIn("保護分支", run("git push -f origin feature/maintenance"))

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
        reason = run("cd app && swift package reset && git reset --hard")
        self.assertIn("CRITICAL", reason)
        self.assertIn("另有 1 項", reason)

    def test_prefixes_are_seen_through(self):
        self.check("sudo rm -rf Sources", "DESTRUCTIVE")
        self.check("FOO=1 git reset --hard", "CRITICAL")

    def test_unbalanced_quotes_fall_back_to_regex(self):
        self.check("git reset --hard 'oops", "CRITICAL")


class Allows(unittest.TestCase):
    def test_safe_rm_targets(self):
        for c in [
            "rm -rf DerivedData",
            "rm -rf ./Pods",
            "rm -rf .build",
            "rm -rf MyApp.xcodeproj/xcuserdata",
            "rm -rf build/SourcePackages",
            "rm -rf node_modules dist coverage",
        ]:
            self.assertIsNone(run(c), c)

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
        ]:
            self.assertIsNone(run(c), c)

    def test_garbage_input_is_let_through(self):
        p = subprocess.run(["bash", SCRIPT], input="not json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()

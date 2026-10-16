#!/usr/bin/env python3
"""Tests for test-file-guard.py (the /ios-dev PreToolUse hook).

Run: python3 skills/ios-dev/scripts/test_test_file_guard.py
"""
import json, os, subprocess, sys, unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-file-guard.py")


def run(stdin):
    p = subprocess.run([sys.executable, SCRIPT], input=stdin, capture_output=True, text=True)
    return p.returncode, p.stdout


def hook(tool, path):
    return json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool,
                       "tool_input": {"file_path": path, "content": "x"}})


class TestFileGuard(unittest.TestCase):
    def test_tests_file_injects_rules(self):
        code, out = run(hook("Edit", "/repo/AppTests/LoginViewModelTests.swift"))
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "PreToolUse")
        self.assertIn("LoginViewModelTests.swift", ctx["additionalContext"])
        self.assertIn("AC", ctx["additionalContext"])
        self.assertNotIn("permissionDecision", ctx)  # remind, never block

    def test_write_new_tests_file_also_injects(self):
        code, out = run(hook("Write", "Tests/PaywallTests.swift"))
        self.assertEqual(code, 0)
        self.assertIn("additionalContext", out)

    def test_production_file_is_silent(self):
        for path in ("/repo/App/LoginViewModel.swift", "/repo/AppTests/Helpers.swift",
                     "/repo/AppTests/LoginTests.swift.orig", "/repo/docs/Tests.md"):
            with self.subTest(path=path):
                self.assertEqual(run(hook("Edit", path)), (0, ""))

    def test_bad_input_passes_silently(self):
        for stdin in ("", "not json", "[]", json.dumps({"tool_input": None})):
            with self.subTest(stdin=stdin):
                self.assertEqual(run(stdin), (0, ""))


if __name__ == "__main__":
    unittest.main()

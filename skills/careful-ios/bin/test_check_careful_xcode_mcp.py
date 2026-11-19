#!/usr/bin/env python3
"""Regression tests for check-careful-xcode-mcp.sh — the Xcode MCP rows of SKILL.md's 防護清單.

Run: python3 skills/careful-ios/bin/test_check_careful_xcode_mcp.py

每個案例跑兩次：Claude 模式（命中回 ask）與 Codex 模式（--codex，命中回 deny）。
"""
import json, os, subprocess, unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-careful-xcode-mcp.sh")
PREFIX = "mcp__plugin_xcode-integration_xcode__"


def run(tool, tool_input, codex=False, raw=None):
    payload = raw if raw is not None else json.dumps({"tool_name": PREFIX + tool, "tool_input": tool_input})
    args = ["bash", SCRIPT] + (["--codex"] if codex else [])
    p = subprocess.run(args, input=payload, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    if not p.stdout.strip():
        return None
    out = json.loads(p.stdout)["hookSpecificOutput"]
    assert out["permissionDecision"] == ("deny" if codex else "ask"), out
    return out["permissionDecisionReason"]


class Mode:
    CODEX = False

    def hook(self, tool, tool_input):
        return run(tool, tool_input, codex=self.CODEX)


class Warns(Mode, unittest.TestCase):
    def check(self, tool, tool_input, level):
        reason = self.hook(tool, tool_input)
        self.assertIsNotNone(reason, f"should warn: {tool} {tool_input}")
        self.assertIn(level, reason, reason)

    def test_rm_source_file(self):
        self.check("XcodeRM", {"path": "App/Sources/Feature.swift"}, "DESTRUCTIVE")

    def test_rm_recursive_folder(self):
        self.check("XcodeRM", {"path": "App/Sources", "recursive": True}, "DESTRUCTIVE")

    def test_rm_entitlements(self):
        self.check("XcodeRM", {"path": "App/App.entitlements"}, "CRITICAL")

    def test_rm_privacy_manifest(self):
        self.check("XcodeRM", {"path": "App/PrivacyInfo.xcprivacy"}, "CRITICAL")

    def test_mv_overwrite(self):
        self.check("XcodeMV", {"sourcePath": "App/A.swift", "destinationPath": "App/B.swift", "overwriteExisting": True}, "DESTRUCTIVE")

    def test_mv_info_plist(self):
        self.check("XcodeMV", {"sourcePath": "App/Info.plist", "destinationPath": "App/Config/Info.plist"}, "CRITICAL")

    def test_write_entitlements(self):
        self.check("XcodeWrite", {"filePath": "App/App.entitlements", "content": "<plist/>"}, "CRITICAL")

    def test_write_info_plist(self):
        self.check("XcodeWrite", {"filePath": "App/Info.plist", "content": "<plist/>"}, "CRITICAL")

    def test_signing_setting(self):
        self.check("UpdateTargetBuildSetting", {"targetName": "App", "buildSettingName": "DEVELOPMENT_TEAM", "buildSettingValue": "ABCDE12345"}, "DESTRUCTIVE")

    def test_bundle_id(self):
        self.check("UpdateTargetBuildSetting", {"targetName": "App", "buildSettingName": "PRODUCT_BUNDLE_IDENTIFIER", "buildSettingValue": "com.x.y"}, "DESTRUCTIVE")

    def test_delete_setting(self):
        self.check("UpdateTargetBuildSetting", {"targetName": "App", "buildSettingName": "SWIFT_VERSION"}, "CAUTION")


class Allows(Mode, unittest.TestCase):
    def allow(self, tool, tool_input):
        self.assertIsNone(self.hook(tool, tool_input), f"should allow: {tool} {tool_input}")

    def test_rm_cache(self):
        self.allow("XcodeRM", {"path": "App/DerivedData/Build", "recursive": True})

    def test_mv_plain_rename(self):
        self.allow("XcodeMV", {"sourcePath": "App/Old.swift", "destinationPath": "New.swift"})

    def test_copy_info_plist(self):
        self.allow("XcodeMV", {"sourcePath": "App/Info.plist", "destinationPath": "App/Info-Copy.plist", "operation": "copy"})

    def test_write_swift(self):
        self.allow("XcodeWrite", {"filePath": "App/Sources/View.swift", "content": "import SwiftUI"})

    def test_plist_lookalike(self):
        self.allow("XcodeWrite", {"filePath": "App/Resources/MyInfo.plist.swift", "content": ""})

    def test_ordinary_setting(self):
        self.allow("UpdateTargetBuildSetting", {"targetName": "App", "buildSettingName": "SWIFT_VERSION", "buildSettingValue": "6.0"})

    def test_read_tool(self):
        self.allow("XcodeRead", {"filePath": "App/App.entitlements"})

    def test_bad_json(self):
        self.assertIsNone(run("", {}, codex=self.CODEX, raw="not json"))


class WarnsCodex(Warns):
    CODEX = True


class AllowsCodex(Allows):
    CODEX = True


if __name__ == "__main__":
    unittest.main()

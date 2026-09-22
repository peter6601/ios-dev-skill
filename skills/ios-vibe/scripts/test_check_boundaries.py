#!/usr/bin/env python3
"""check-boundaries.py 的測試。

跑法：
    python3 -m unittest discover -s skills/ios-vibe/scripts -p 'test_*.py'
 或 python3 skills/ios-vibe/scripts/test_check_boundaries.py

兩件事要顧：乾淨的範本不能有任何命中（不然每次都在喊狼來了），
以及每一條規則真的抓得到它該抓的寫法。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(SCRIPT_DIR, "check-boundaries.py")
TEMPLATE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "templates", "app"))
EMPTY_ALLOWLIST = os.path.join(SCRIPT_DIR, "boundaries-allowlist.txt")


def run(project, allowlist=EMPTY_ALLOWLIST):
    proc = subprocess.run(
        [sys.executable, SCRIPT, project, "--allowlist", allowlist, "--json"],
        capture_output=True, text=True,
    )
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, {"hits": [], "exemptions": [], "stdout": proc.stdout, "stderr": proc.stderr}


def rules(payload):
    return sorted({h["rule"] for h in payload["hits"]})


class Project:
    """臨時專案資料夾。"""

    def __init__(self):
        self.dir = tempfile.mkdtemp()

    def write(self, relative_path, body):
        path = os.path.join(self.dir, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        return path


class CleanTemplate(unittest.TestCase):
    def test_template_has_no_hits(self):
        code, payload = run(TEMPLATE)
        self.assertEqual(payload["hits"], [], "乾淨的範本不應該有任何越界")
        self.assertEqual(code, 0)

    def test_template_exemptions_are_the_expected_files(self):
        _, payload = run(TEMPLATE)
        exempt = {e["file"]: e["tags"] for e in payload["exemptions"]}
        self.assertIn("urlsession", exempt["VibeApp/Debug/NetworkBlocker.swift"])
        self.assertIn("store-setup", exempt["VibeApp/Data/DataStack.swift"])
        self.assertIn("file-io", exempt["VibeApp/Data/DataFiles.swift"])

    def test_missing_folder_exits_2(self):
        proc = subprocess.run([sys.executable, SCRIPT, "/no/such/folder"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


class NetworkRules(unittest.TestCase):
    def test_catches_the_usual_ways_to_go_online(self):
        project = Project()
        project.write("App/Bad.swift", """
import Network
import Alamofire
import WebKit

func fetch() {
    let session = URLSession.shared
    let connection = NWConnection(host: "example.com", port: 443, using: .tcp)
    let socket = CFSocketCreate(nil, 0, 0, 0, 0, nil, nil)
    let task = session.webSocketTask(with: URL(string: "wss://example.com")!)
    let web = WKWebView()
    let text = try String(contentsOf: URL(string: "https://example.com")!)
}
""")
        project.write("App/Image.swift", 'import SwiftUI\nlet v = AsyncImage(url: nil)\n')
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        for rule in ["net-urlsession", "net-framework", "net-nwtypes", "net-socket",
                     "net-library", "net-cloud", "net-asyncimage", "net-contents-of"]:
            self.assertIn(rule, rules(payload), f"{rule} 沒抓到")

    def test_comments_are_not_code(self):
        project = Project()
        project.write("App/Fine.swift", """
// 這裡刻意提到 URLSession、import Network、WKWebView，但都只是註解。
/* NWConnection 也是 */
import SwiftUI

struct Fine: View { var body: some View { Text("嗨") } }
""")
        code, payload = run(project.dir)
        self.assertEqual(payload["hits"], [])
        self.assertEqual(code, 0)

    def test_urlsession_exemption_only_counts_in_a_debug_only_file(self):
        project = Project()
        project.write("App/Blocker.swift", """
// vibe-boundaries: allow urlsession — 攔截器
import Foundation
final class Blocker: URLProtocol {
    func go() { _ = URLSession.shared }
}
""")
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        self.assertIn("net-urlsession", rules(payload))
        self.assertIn("#if DEBUG", payload["hits"][0]["message"])

        wrapped = Project()
        wrapped.write("App/Blocker.swift", """#if DEBUG
// vibe-boundaries: allow urlsession — 攔截器本身
import Foundation
final class Blocker: URLProtocol {
    func go() { _ = URLSession.shared }
}
#endif
""")
        code, payload = run(wrapped.dir)
        self.assertEqual(payload["hits"], [])
        self.assertEqual(code, 0)


class StorageRules(unittest.TestCase):
    def test_catches_other_ways_to_store_data(self):
        project = Project()
        project.write("App/Store.swift", """
import CoreData
import SQLite3
import SwiftData

func save(data: Data) throws {
    let container = NSPersistentContainer(name: "x")
    sqlite3_open("/tmp/x.db", nil)
    SecItemAdd([:] as CFDictionary, nil)
    let folder = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    try data.write(to: folder.appending(path: "x.bin"))
    let other = try ModelContainer(for: Entry.self)
}
""")
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        for rule in ["store-coredata", "store-sqlite", "store-keychain",
                     "store-file-write", "store-system-dir", "store-setup"]:
            self.assertIn(rule, rules(payload), f"{rule} 沒抓到")

    def test_file_io_exemption_turns_off_the_file_rules(self):
        project = Project()
        project.write("App/Data/Files.swift", """
// vibe-boundaries: allow file-io — 資料層本身
import Foundation
func save(data: Data, to url: URL) throws {
    try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
    try data.write(to: url)
}
""")
        code, payload = run(project.dir)
        self.assertEqual(payload["hits"], [])
        self.assertEqual(code, 0)

    def test_in_memory_container_is_fine(self):
        project = Project()
        project.write("App/Preview.swift", """
import SwiftData
let preview = try! ModelContainer(for: Entry.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
""")
        _, payload = run(project.dir)
        self.assertEqual(payload["hits"], [])

    def test_user_defaults_keys_must_start_with_ui(self):
        project = Project()
        project.write("App/Prefs.swift", """
import SwiftUI

struct Prefs {
    @AppStorage("ui.selectedTab") var tab = 0
    @AppStorage("lastEntryTitle") var title = ""
    @AppStorage(Keys.theme) var theme = ""

    func store() {
        UserDefaults.standard.set(1, forKey: "ui.sortOrder")
        UserDefaults.standard.set("秘密", forKey: "userSecret")
        UserDefaults.standard.set(2, forKey: Keys.other)
    }
}
""")
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        prefs = [h for h in payload["hits"] if h["rule"] == "prefs-key"]
        self.assertEqual(len(prefs), 4, [h["message"] for h in prefs])
        self.assertEqual([h["line"] for h in prefs], [6, 7, 11, 12])


class TestFolders(unittest.TestCase):
    def test_test_folders_are_skipped_for_source_rules(self):
        project = Project()
        project.write("AppTests/StoreTests.swift", """
import Foundation
func helper(data: Data, at url: URL) throws {
    try data.write(to: url)
    _ = URLSession.shared
}
""")
        code, payload = run(project.dir)
        self.assertEqual(payload["hits"], [])
        self.assertEqual(code, 0)

    def test_ui_tests_must_launch_through_the_helper(self):
        project = Project()
        project.write("AppUITests/FlowTests.swift", """
import XCTest
final class FlowTests: XCTestCase {
    func testFlow() {
        let app = XCUIApplication()
        app.launch()
    }
}
""")
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        self.assertEqual(rules(payload), ["uitest-launch"])

        allowed = Project()
        allowed.write("AppUITests/Support.swift", """
// vibe-boundaries: allow uitest-launch — 唯一可以直接 launch 的地方
import XCTest
func start() -> XCUIApplication {
    let app = XCUIApplication()
    app.launchEnvironment["VIBE_BLOCK_NETWORK"] = "1"
    app.launch()
    return app
}
""")
        code, payload = run(allowed.dir)
        self.assertEqual(payload["hits"], [])
        self.assertEqual(code, 0)


class Dependencies(unittest.TestCase):
    def build_project_with_packages(self):
        project = Project()
        project.write("App.xcodeproj/project.pbxproj", """
		AA01 /* XCRemoteSwiftPackageReference "Alamofire" */ = {
			isa = XCRemoteSwiftPackageReference;
			repositoryURL = "https://github.com/Alamofire/Alamofire.git";
		};
""")
        project.write("Podfile", "target 'App' do\n  pod 'SnapKit'\nend\n")
        project.write("Cartfile", 'github "onevcat/Kingfisher" ~> 7.0\n')
        project.write("App.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved", json.dumps({
            "pins": [{"identity": "swift-collections", "location": "https://github.com/apple/swift-collections"}],
            "version": 3,
        }))
        return project

    def test_any_dependency_is_a_hit(self):
        project = self.build_project_with_packages()
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        messages = " ".join(h["message"] for h in payload["hits"])
        for name in ["Alamofire", "SnapKit", "Kingfisher", "swift-collections"]:
            self.assertIn(name, messages)

    def test_allowlisted_packages_pass(self):
        project = self.build_project_with_packages()
        allowlist = os.path.join(project.dir, "allow.txt")
        with open(allowlist, "w", encoding="utf-8") as handle:
            handle.write("# 說明\nalamofire\nsnapkit\nkingfisher\nswift-collections\n")
        code, payload = run(project.dir, allowlist=allowlist)
        self.assertEqual(payload["hits"], [])
        self.assertEqual(code, 0)

    def test_binaries_dropped_into_the_project_are_a_hit(self):
        project = Project()
        os.makedirs(os.path.join(project.dir, "Vendor", "Secret.xcframework"), exist_ok=True)
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        self.assertEqual(rules(payload), ["dependency"])

    def test_local_swift_packages_are_a_hit_too(self):
        project = Project()
        project.write("App.xcodeproj/project.pbxproj", """
		AA02 /* XCLocalSwiftPackageReference "Helpers" */ = {
			isa = XCLocalSwiftPackageReference;
			relativePath = Helpers;
		};
""")
        code, payload = run(project.dir)
        self.assertEqual(code, 1)
        self.assertEqual(rules(payload), ["dependency"])

    def test_build_folders_are_ignored(self):
        project = Project()
        project.write("DerivedData/Build/Bad.swift", "import Network\nlet x = URLSession.shared\n")
        project.write("Pods/Alamofire/Alamofire.swift", "let x = URLSession.shared\n")
        code, payload = run(project.dir)
        self.assertEqual(payload["hits"], [])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

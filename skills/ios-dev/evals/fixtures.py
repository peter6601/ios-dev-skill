#!/usr/bin/env python3
"""Fixture repos for the ios-dev routing evals, generated instead of stored.

`skills/ios-dev/` is symlinked into `~/.claude/commands`, and every `.md` under a
commands folder becomes a slash command.  A fixture `CLAUDE.md` or `tickets/T3.md`
kept on disk here would show up as `/ios-dev:evals:…`.  So fixtures are code:
`build(case_id, dest)` writes a small fake iOS repo — BASE plus that case's overlay.

Each overlay exists to put the repo in the one state the case is about (a body over
80 lines, an existing rename alert, a ticket that already carries its contract).
Keep them that small: the evals test routing, not Swift.

Usage:
  fixtures.py <case_id> <dest_dir>      # build one fixture to look at it
"""
import os, subprocess, sys


def rows(n, indent="            "):
    return "\n".join(f'{indent}Text("row {i}")' for i in range(n))


CLAUDE_MD = """# FixtureApp

iOS 即時翻譯對話 app。SwiftUI、iOS 17+、MVVM ＋ Clean 分層，protocol DI。

- `FixtureApp/Views`、`ViewModels`、`Services`、`Models`
- 測試用 Swift Testing，放 `FixtureAppTests/`
"""

AGENT_SKILLS = """
## Agent skills

### Issue tracker

GitHub Issues（`gh` CLI）。See `docs/agents/issue-tracker.md`.

### Domain docs

single-context。See `docs/agents/domain.md`.
"""

BASE = {
    "CLAUDE.md": CLAUDE_MD + AGENT_SKILLS,
    "CONTEXT.md": "# Context\n\n- **Room**：一場雙人對話。\n- **Utterance**：一句已辨識、待翻譯或已翻譯的話。\n",
    "docs/agents/issue-tracker.md": "GitHub Issues.\n",
    "docs/agents/domain.md": "single-context.\n",
    "docs/adr/0001-mvvm-clean.md": "# 0001 MVVM ＋ Clean\n\nViewModel 只暴露狀態；Service 以 protocol 注入。\n",
    "FixtureApp/Views/ChatView.swift": """import SwiftUI

struct ChatView: View {
    @State private var viewModel: ChatViewModel

    var body: some View {
        List(viewModel.utterances) { Text($0.translated) }
            .task { await viewModel.start() }
    }
}
""",
    "FixtureApp/ViewModels/ChatViewModel.swift": """import Observation

@MainActor @Observable
final class ChatViewModel {
    private(set) var utterances: [Utterance] = []
    private let translator: TranslationService

    init(translator: TranslationService) { self.translator = translator }

    func start() async {
        for await utterance in translator.stream() { utterances.append(utterance) }
    }
}
""",
    "FixtureApp/Views/ConversationListView.swift": """import SwiftUI

struct ConversationListView: View {
    let rooms: [Room]

    var body: some View {
        List(rooms) { room in
            HStack { Text(room.name); Spacer(); Text(room.updatedAt, style: .relative) }
        }
    }
}
""",
    "FixtureApp/Services/TranslationService.swift": """protocol TranslationService: Sendable {
    func stream() -> AsyncStream<Utterance>
}
""",
    "FixtureApp/Services/WebSocketClient.swift": """import Foundation

actor WebSocketClient {
    private var task: URLSessionWebSocketTask?
    private let retryInterval: Duration = .seconds(3)

    func reconnect() async throws {
        try await Task.sleep(for: retryInterval)
        task?.resume()
    }
}
""",
    "Package.swift": """// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "FixtureApp",
    platforms: [.iOS(.v17)],
    targets: [
        .target(name: "FixtureApp", path: "FixtureApp"),
        .testTarget(name: "FixtureAppTests", dependencies: ["FixtureApp"], path: "FixtureAppTests"),
    ]
)
""",
    "FixtureAppTests/ChatViewModelTests.swift": """import Testing
@testable import FixtureApp

@MainActor
struct ChatViewModelTests {
    @Test func startsEmpty() {
        #expect(ChatViewModel(translator: StubTranslator()).utterances.isEmpty)
    }
}

struct StubTranslator: TranslationService {
    func stream() -> AsyncStream<Utterance> { AsyncStream { $0.finish() } }
}
""",
    "FixtureApp/Models/Models.swift": """import Foundation

struct Room: Identifiable { let id: UUID; var name: String; var updatedAt: Date }
struct Utterance: Identifiable { let id: UUID; var source: String; var translated: String }
""",
}

OVERVIEW = """# 席次授權 overview

## §0 架構形狀

1. **Pattern**：Clean 分層＋MVVM。
2. **模組邊界**：`LicenseStore`（actor）own 授權清單與到期狀態；對外 `LicenseProviding` protocol；
   注入點在 `AppContainer`。
3. **State 與 presentation**：授權到期提示由 `RootRouter.route` 單一管理。
4. **Async 契約**：`LicenseStore.refresh()`——持有者 LicenseStore／生命週期 App／清理：app 進背景取消／
   重入：取代舊的／舊結果：generation 計數／isolation：actor。
"""


def ticket(tid, title, files, constraints, tasks, *, feature, type_, acceptance, refs="- [`../overview.md`](../overview.md) § 0"):
    return f"""---
ticket: "{tid}"
title: "{title}"
feature: "{feature}"
stage: 2
type: "{type_}"
status: in-progress
estimate: 0.5
---

# {tid} {title}

## Refs

{refs}

## Files

{files}

## 架構約束（不可違反；收尾時 `architecture-auditor` 拿這一段當尺）

{constraints}

## Tasks

{tasks}

## Acceptance Criteria

{acceptance}
"""


def fat_view_model(name):
    """~150 lines of the shape that makes a ViewModel "fat": many flags, stored Tasks, should* commands."""
    flags = "\n".join(f"    var shouldShow{k} = false" for k in ("Alert", "Toast", "Sheet", "Banner"))
    state = "\n".join(f"    var field{i}: String = \"\"" for i in range(12))
    tasks = "\n".join(f"    private var task{i}: Task<Void, Never>?" for i in range(5))
    funcs = "\n\n".join(f"""    func action{i}() {{
        task{i % 5}?.cancel()
        task{i % 5} = Task {{
            isLoading = true
            defer {{ isLoading = false }}
            try? await Task.sleep(for: .milliseconds(100))
            if field{i % 12}.isEmpty {{ shouldShowAlert = true }} else {{ items.append(field{i % 12}) }}
        }}
    }}""" for i in range(10))
    # ChatView and ChatViewModelTests (BASE) use these, so the fat Chat version must keep them
    chat = """    private(set) var utterances: [Utterance] = []
    private let translator: TranslationService

    init(translator: TranslationService) { self.translator = translator }

    func start() async {
        for await utterance in translator.stream() { utterances.append(utterance) }
    }
""" if name == "Chat" else ""
    return f"""import Observation

@MainActor @Observable
final class {name}ViewModel {{
{chat}    var items: [String] = []
    var isLoading = false
    var errorMessage: String?
{flags}
{state}
{tasks}

    func load() async {{
        isLoading = true
        defer {{ isLoading = false }}
        try? await Task.sleep(for: .milliseconds(200))
        items = (0..<20).map {{ "{name} \\($0)" }}
    }}

{funcs}
}}
"""


CASES = {
    # 1: a repo that never ran setup-matt-pocock-skills
    1: {"CLAUDE.md": CLAUDE_MD},
    # 3: a small, purely visual target
    3: {"FixtureApp/Views/SettingsView.swift": f"""import SwiftUI

struct SettingsView: View {{
    var body: some View {{
        List {{
            Section("一般") {{
{rows(4, "                ")}
            }}
            Section("關於") {{
{rows(3, "                ")}
            }}
        }}
    }}
}}
"""},
    # 6: a fat view — long body, several Bool presentations, no tests
    6: {"FixtureApp/Views/HomeView.swift": f"""import SwiftUI

struct HomeView: View {{
    @State private var showConsent = false
    @State private var didDeclineConsent = false
    @State private var showLanguagePicker = false
    @State private var showPaywall = false
    @State private var isCheckingLicense = false
    @State private var pendingRoom: Room?
    @State private var errorMessage: String?

    var body: some View {{
        VStack {{
{rows(95)}
        }}
        .sheet(isPresented: $showConsent, onDismiss: {{ if !didDeclineConsent {{ showLanguagePicker = true }} }}) {{ Text("consent") }}
        .sheet(isPresented: $showLanguagePicker) {{ Text("language") }}
        .fullScreenCover(isPresented: $showPaywall) {{ Text("paywall") }}
    }}
}}
"""},
    # 7: a planned "create module" ticket whose contract is already complete
    7: {
        "overview.md": OVERVIEW,
        "coordination/implementation-log.md": "# implementation log\n\n- 2026-09-10 T1、T2 done：`LicenseProviding` protocol 與 `AppContainer` 注入點已建立。\n",
        # T1/T2 really are done: the log above must match the code, or the case tests a fixture bug
        "FixtureApp/Services/LicenseProviding.swift": """import Foundation

struct License: Sendable, Equatable { let id: String; let expiresAt: Date }

protocol LicenseProviding: Sendable {
    func licenses() async -> [License]
    func refresh() async throws
}
""",
        "FixtureApp/AppContainer.swift": """@MainActor
final class AppContainer {
    let translator: TranslationService
    let licenses: LicenseProviding

    init(translator: TranslationService, licenses: LicenseProviding) {
        self.translator = translator
        self.licenses = licenses
    }
}
""",
        "tickets/T3.md": ticket(
            "T3", "建立 LicenseStore 模組",
            "- `FixtureApp/Services/LicenseStore.swift`（新建）\n- `FixtureAppTests/LicenseStoreTests.swift`（新建）",
            "- 所屬模組與責任：`LicenseStore` own 授權清單與到期狀態\n"
            "- state owner／presentation owner／async owner：LicenseStore／RootRouter／LicenseStore\n"
            "- 依賴方向與注入點：View → ViewModel → `LicenseProviding`；`AppContainer` 注入\n"
            "- 非同步工作生命週期：`refresh()`——持有者 LicenseStore／App／進背景取消／取代舊的／generation 計數／actor\n"
            "- 不可破壞的不變條件：到期判定只在 LicenseStore 內；refresh 失敗不清空既有授權\n"
            "- 涉及流程時附轉移表：不適用\n\n"
            "- 中途檢查點：refresh 重入測試綠燈後，`concurrency-auditor` 對照上面的 async 契約",
            "- [ ] actor LicenseStore 實作 `LicenseProviding`\n- [ ] Unit test",
            feature="SeatLicense", type_="Service",
            acceptance="- [ ] 單元測試覆蓋到期、續期、refresh 重入"),
    },
    # 8: the feature already exists as an alert
    8: {"FixtureApp/Views/RoomListView.swift": """import SwiftUI

struct RoomListView: View {
    @State private var viewModel: RoomListViewModel
    @State private var showRenameAlert = false
    @State private var renameText = ""

    var body: some View {
        List(viewModel.rooms) { room in
            Text(room.name)
                .swipeActions { Button("改名") { renameText = room.name; showRenameAlert = true } }
        }
        .alert("房間改名", isPresented: $showRenameAlert) {
            TextField("名稱", text: $renameText)
            Button("儲存") { viewModel.rename(to: renameText) }
            Button("取消", role: .cancel) {}
        }
    }
}
"""},
    # 9: a pure view that the request quietly turns into persistence
    9: {"FixtureApp/Views/LanguagePickerView.swift": """import SwiftUI

struct LanguagePickerView: View {
    @Binding var selection: String
    let languages: [String]

    var body: some View {
        List(languages, id: \\.self) { code in
            Button(code) { selection = code }
        }
    }
}
"""},
    # 10: body well over 80 lines and one Bool-driven sheet already there
    10: {"FixtureApp/Views/ChatView.swift": f"""import SwiftUI

struct ChatView: View {{
    @State private var viewModel: ChatViewModel
    @State private var showLanguageSheet = false

    var body: some View {{
        VStack {{
{rows(110)}
        }}
        .sheet(isPresented: $showLanguageSheet) {{ Text("language") }}
    }}
}}
"""},
    # 12: adding a language is adding a case to an existing table
    12: {"FixtureApp/Models/Language.swift": """import Foundation

enum Language: String, CaseIterable, Identifiable {
    case zhTW, enUS, jaJP
    var id: String { rawValue }

    var displayName: String {
        switch self { case .zhTW: "繁體中文"; case .enUS: "English"; case .jaJP: "日本語" }
    }
    var sttLocale: Locale {
        switch self { case .zhTW: Locale(identifier: "zh-TW"); case .enUS: Locale(identifier: "en-US"); case .jaJP: Locale(identifier: "ja-JP") }
    }
    var flagAsset: String { "flag_" + rawValue }
}
"""},
    # 14: half-written work that commands the View through a should* flag
    14: {
        "FixtureApp/ViewModels/ChatViewModel.swift": """import Observation

@MainActor @Observable
final class ChatViewModel {
    private(set) var utterances: [Utterance] = []
    var shouldShowRatingPrompt = false
    private let translator: TranslationService

    init(translator: TranslationService) { self.translator = translator }

    func start() async {
        for await utterance in translator.stream() {
            utterances.append(utterance)
            if utterances.count == 20 { shouldShowRatingPrompt = true }
        }
    }
}
""",
        "FixtureApp/Views/ChatView.swift": """import SwiftUI

struct ChatView: View {
    @State private var viewModel: ChatViewModel
    @State private var showLanguageSheet = false
    @State private var showRating = false

    var body: some View {
        List(viewModel.utterances) { Text($0.translated) }
            .task { await viewModel.start() }
            .sheet(isPresented: $showLanguageSheet) { Text("language") }
            .onChange(of: viewModel.shouldShowRatingPrompt) { _, new in
                if new { showRating = true }  // TODO: 評分 sheet 還沒寫
            }
    }
}
""",
    },
    # 15: the code already breaks the ticket's async contract
    16: {"FixtureApp/Services/SubscriptionService.swift": """import StoreKit

@MainActor
final class SubscriptionService {
    private(set) var isPremium = false
    private var updates: Task<Void, Never>?

    func startListening() {
        updates = Task {
            for await result in Transaction.updates {
                if case .verified(let tx) = result { isPremium = tx.revocationDate == nil; await tx.finish() }
            }
        }
    }
}
"""},
    17: {
        **{f"FixtureApp/ViewModels/{n}ViewModel.swift": fat_view_model(n) for n in ("Chat", "RoomList", "Settings", "LanguagePicker")},
        **{f"FixtureApp/Views/{n}Screen.swift": f"""import SwiftUI

struct {n}Screen: View {{
    @State private var viewModel: {n}ViewModel

    var body: some View {{
        List(viewModel.items, id: \\.self) {{ Text($0) }}
            .task {{ await viewModel.load() }}
            .alert("錯誤", isPresented: $viewModel.shouldShowAlert) {{ Button("OK") {{}} }}
    }}
}}
""" for n in ("RoomList", "Settings", "LanguagePicker")},
    },
    19: {"FixtureApp/Views/HomeHeaderView.swift": """import SwiftUI

struct HomeHeaderView: View {
    var body: some View {
        HStack {
            Text("FixtureApp").font(.headline)
            Spacer()
            Button { } label: { Image(systemName: "gearshape") }
        }
    }
}
"""},
    15: {
        "docs/plans/recording-watchdog.md": """# 錄音 watchdog

## 架構約束

錄音 watchdog 由 `ChatViewModel` 持有（stored Task），生命週期＝對話 session；
`stopRecording()` 與 deinit 取消；重入時取代舊的；MainActor。離開畫面後不得繼續跑。
""",
        "FixtureApp/ViewModels/ChatViewModel.swift": """import Observation

@MainActor @Observable
final class ChatViewModel {
    private(set) var utterances: [Utterance] = []
    private(set) var isRecording = false
    private let translator: TranslationService

    init(translator: TranslationService) { self.translator = translator }

    func start() async {
        isRecording = true
        for await utterance in translator.stream() { utterances.append(utterance) }
    }

    func stopRecording() { isRecording = false }
}
""",
        "tickets/T5.md": ticket(
            "T5", "錄音 watchdog",
            "- `FixtureApp/ViewModels/ChatViewModel.swift`（編輯）\n- `FixtureApp/Views/ChatView.swift`（編輯）",
            "- 所屬模組與責任：Chat\n"
            "- state owner／presentation owner／async owner：ChatViewModel／ChatView／ChatViewModel\n"
            "- 依賴方向與注入點：不變\n"
            "- 非同步工作生命週期：錄音 watchdog——持有者 **ChatViewModel**（stored Task）／對話 session／"
            "`stopRecording()` 與 deinit 取消／重入：取代舊的／舊結果：不適用／MainActor\n"
            "- 不可破壞的不變條件：離開畫面後 watchdog 不得繼續跑\n"
            "- 涉及流程時附轉移表：不適用\n\n"
            "- 中途檢查點：watchdog 取消測試綠燈後自檢",
            "- [ ] watchdog 逾時 30 秒自動停止錄音\n- [ ] Unit test",
            feature="RecordingWatchdog", type_="Delta",
            acceptance="- [ ] 錄音 30 秒沒有新語音就自動停止\n- [ ] 離開聊天畫面後 watchdog 不再觸發（單元測試）",
            refs="- 根文件：repo `docs/plans/recording-watchdog.md` § 架構約束"),
        "FixtureApp/Views/ChatView.swift": """import SwiftUI

struct ChatView: View {
    @State private var viewModel: ChatViewModel

    var body: some View {
        List(viewModel.utterances) { Text($0.translated) }
            .task { await viewModel.start() }
            .onAppear {
                Task {  // watchdog：沒有人持有、離開畫面不會取消
                    try? await Task.sleep(for: .seconds(30))
                    viewModel.stopRecording()
                }
            }
    }
}
""",
    },
}


def build(case_id, dest):
    """Write BASE plus the case's overlay into `dest` and commit it as a git repo."""
    files = dict(BASE)
    files.update(CASES.get(case_id, {}))
    for rel, body in files.items():
        path = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    # no background gc/maintenance: a detached gc still writing .git/objects/pack breaks temp-dir cleanup
    git = ["git", "-C", dest, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
           "-c", "gc.auto=0", "-c", "maintenance.auto=false"]
    subprocess.run(["git", "init", "-q", dest], check=True)
    subprocess.run(["git", "-C", dest, "config", "gc.auto", "0"], check=True)
    subprocess.run(["git", "-C", dest, "config", "maintenance.auto", "false"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-qm", "fixture baseline"], check=True)
    # a remote that cannot resolve: "there is no remote" must never be the reason a run did not push
    subprocess.run(git + ["remote", "add", "origin", "https://git.example.invalid/fixture-app.git"], check=True)
    return sorted(files)


if __name__ == "__main__":
    if len(sys.argv) != 3 or not sys.argv[1].isdigit():
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    os.makedirs(sys.argv[2], exist_ok=True)
    for f in build(int(sys.argv[1]), sys.argv[2]):
        print(f)

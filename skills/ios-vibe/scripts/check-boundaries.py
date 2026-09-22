#!/usr/bin/env python3
"""vibe 專案的邊界檢查：不連網、不加第三方套件、只有一種儲存方式。

用法：
    python3 check-boundaries.py <專案路徑> [--allowlist <檔案>] [--json]

命中就 exit 1，並印出「檔案:行 白話原因」。沒命中 exit 0；路徑不對 exit 2。

────────────────────────────────────────────────────────────────────────
這支腳本是**盡力而為**，不是證明。抓不到的東西（照設計文件 §6、§7）：

不連網
  - 只掃字串。把 "URLSession" 拆成字串拼起來、用 Objective-C runtime 繞過去、
    或改用系統服務（分享、郵件、地圖）代發的請求，都抓不到。
  - 抓不到 app 以外的東西：extension、widget 以外的行程、系統框架內部的連線。
  - 執行期攔截（範本的 NetworkBlocker）只擋得到走 URLSession 的請求，
    WKWebView 與低階 socket 靠這裡的字串規則擋，兩邊都有漏。

相依白名單
  - 只看 pbxproj、Package.resolved、Package.swift、Podfile、Cartfile 與專案裡的
    二進位檔。手動把 .swift 原始碼整包複製進專案（vendoring）看不出來。

唯一的儲存方式
  - **FileManager 的檢查判斷不了路徑**：只要在資料層以外出現寫檔的呼叫就報，
    不管它寫去哪裡。反過來說，路徑是變數、或透過別的型別包一層寫出去的，也抓不到。
    暫存檔（例如產生一份要分享的檔案）同樣會被報——真的需要就在資料層加方法。
  - UserDefaults 只認得直接寫出來的字串 key；key 放在常數或變數裡時，
    腳本看不到內容，會直接報「請直接寫字串」而不是猜。
  - Keychain、Core Data、SQLite 靠關鍵字比對，換個包裝（自己寫 C 介面）就抓不到。

所以這一層之外，還有相依白名單、執行期攔截與審查 agent；三層合起來仍然不等於保證。
────────────────────────────────────────────────────────────────────────
"""
import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ALLOWLIST = os.path.join(SCRIPT_DIR, "boundaries-allowlist.txt")

# 不進去掃的資料夾：build 產物、套件快取、AI 的執行期紀錄。
SKIP_DIRS = {
    ".git", ".vibe", "build", ".build", "DerivedData", "Pods", "Carthage",
    "SourcePackages", "node_modules", "xcuserdata", ".swiftpm", "__pycache__",
}

# 豁免標記：`// vibe-boundaries: allow file-io — 原因`
EXEMPT_RE = re.compile(r"vibe-boundaries:\s*allow\s+([a-z0-9,\s\-]+)")

# (規則代號, 類別, 正規式, 白話原因, 可用哪個豁免標記關掉)
NETWORK_RULES = [
    ("net-urlsession", "不連網", r"\bURLSession\w*",
     "用到 URLSession（連網最常見的方式）。v1 的 app 不連網。", "urlsession"),
    ("net-framework", "不連網", r"^\s*(@\w+\s+)*import\s+Network\b",
     "載入 Network 框架（低階連線）。執行期攔截擋不到這種連線。", None),
    ("net-nwtypes", "不連網", r"\bNW(Connection|Listener|Browser|PathMonitor|Endpoint|Parameters)\b",
     "用到 Network 框架的連線型別。", None),
    ("net-websocket", "不連網", r"WebSocket",
     "WebSocket 是長連線，一樣算連網。", None),
    ("net-socket", "不連網", r"\bCFSocket\w*|\bCFStream\w*|getStreamsToHost|\bSocket\b|\bsocket\s*\(",
     "低階 socket／stream 連線。", None),
    ("net-library", "不連網", r"^\s*(@\w+\s+)*import\s+(Alamofire|Moya|Starscream|SocketIO|Apollo|AsyncHTTPClient|NIO\w*|GRPC\w*|Firebase\w*|Supabase\w*|Kingfisher|SDWebImage\w*|Nuke\w*)\b",
     "載入連網用的第三方套件。v1 不加任何第三方套件，也不連網。", None),
    ("net-cloud", "不連網", r"^\s*(@\w+\s+)*import\s+(CloudKit|WebKit|SafariServices|MultipeerConnectivity)\b|\bCKContainer\b|\bWKWebView\b|\bSFSafariViewController\b|\bNSUbiquitousKeyValueStore\b|cloudKitDatabase\s*:\s*\.(automatic|private)",
     "會把資料送出這支手機，或會載入遠端網頁（iCloud、WebKit、鄰近裝置連線）。", None),
    ("net-asyncimage", "不連網", r"\bAsyncImage\b",
     "AsyncImage 會從網路下載圖片。圖片請放在專案裡或存進資料根目錄。", None),
    ("net-contents-of", "不連網", r"\b(Data|String)\s*\(\s*contentsOf\s*:",
     "contentsOf 給遠端網址就是在下載東西。讀本機檔案請用 DataFiles。", "file-io"),
]

STORAGE_RULES = [
    ("store-coredata", "唯一的儲存方式", r"^\s*(@\w+\s+)*import\s+CoreData\b|\bNSPersistent(CloudKit)?Container\b|\bNSManagedObject(Context|Model)?\b",
     "直接用 Core Data。資料只能存 SwiftData，備份與還原才保證一致。", None),
    ("store-sqlite", "唯一的儲存方式", r"^\s*(@\w+\s+)*import\s+(SQLite3|SQLite|GRDB|RealmSwift|Realm)\b|\bsqlite3_\w+",
     "直接用 SQLite 或其他資料庫。資料只能存 SwiftData。", None),
    ("store-keychain", "唯一的儲存方式", r"\bSecItem(Add|Update|CopyMatching|Delete)\b|\bkSecClass\w*|\bKeychain\w*",
     "Keychain 不是 v1 的儲存方式，使用者資料也不該放這裡。", None),
    ("store-file-write", "唯一的儲存方式",
     r"\.(createFile|createDirectory|copyItem|moveItem|removeItem|trashItem|replaceItem|replaceItemAt|createSymbolicLink|linkItem|setAttributes)\s*\(|\.write\s*\(\s*to\s*:|\.write\s*\(\s*toFile\s*:|\bFileHandle\s*\(\s*for(WritingTo|UpdatingTo|WritingAtPath|UpdatingAtPath)|\bOutputStream\s*\(",
     "直接寫檔。使用者產生的檔案要透過範本的 DataFiles 存進資料根目錄。", "file-io"),
    ("store-system-dir", "唯一的儲存方式",
     r"\.(documentDirectory|documentsDirectory|applicationSupportDirectory|cachesDirectory|libraryDirectory)\b|NSHomeDirectory\s*\(|NSTemporaryDirectory\s*\(|NSSearchPathForDirectoriesInDomains|\btemporaryDirectory\b|containerURL\s*\(\s*forSecurityApplicationGroupIdentifier",
     "自己組系統資料夾路徑。資料只放資料根目錄，路徑由範本的 DataLocation 決定。", "file-io"),
]


def strip_comments(text):
    """把註解換成空白（保留換行），字串裡的 // 不算註解。"""
    out = []
    i, n = 0, len(text)
    in_line_comment = False
    block_depth = 0
    in_string = False
    in_multiline = False
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                out.append(ch)
            else:
                out.append(" ")
            i += 1
            continue
        if block_depth:
            if ch == "/" and nxt == "*":
                block_depth += 1
                out.append("  ")
                i += 2
                continue
            if ch == "*" and nxt == "/":
                block_depth -= 1
                out.append("  ")
                i += 2
                continue
            out.append("\n" if ch == "\n" else " ")
            i += 1
            continue
        if in_multiline:
            out.append(ch)
            if text.startswith('"""', i):
                in_multiline = False
                out.append(text[i + 1:i + 3])
                i += 3
                continue
            i += 1
            continue
        if in_string:
            out.append(ch)
            if ch == "\\":
                if i + 1 < n:
                    out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if text.startswith('"""', i):
            in_multiline = True
            out.append(text[i:i + 3])
            i += 3
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line_comment = True
            out.append("  ")
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_depth = 1
            out.append("  ")
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def exemptions_in(raw_text):
    tags = set()
    for match in EXEMPT_RE.finditer(raw_text):
        for tag in re.split(r"[,\s]+", match.group(1).strip()):
            if tag:
                tags.add(tag)
    return tags


def wholly_debug_only(code):
    """整個檔案是不是包在 #if DEBUG 裡（網路豁免的附加條件）。"""
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    if not lines:
        return False
    return lines[0].startswith("#if DEBUG") and lines[-1].startswith("#endif")


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.endswith((".xcresult", ".xcassets"))
        ]
        for name in filenames:
            full = os.path.join(dirpath, name)
            yield full, os.path.relpath(full, root)


def is_test_path(rel):
    parts = rel.split(os.sep)
    return any(p.endswith("Tests") for p in parts[:-1])


def is_uitest_path(rel):
    parts = rel.split(os.sep)
    return any(p.endswith("UITests") for p in parts[:-1])


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (UnicodeDecodeError, OSError):
        return None


def hit(hits, rel, line_no, rule_id, category, message):
    hits.append({
        "file": rel, "line": line_no, "rule": rule_id,
        "category": category, "message": message,
    })


# ─── 原始碼規則 ────────────────────────────────────────────────────────

def check_swift_file(path, rel, hits, exempt_log):
    raw = read_text(path)
    if raw is None:
        return
    code = strip_comments(raw)
    tags = exemptions_in(raw)
    if tags:
        exempt_log.append((rel, sorted(tags)))
    lines = code.splitlines()

    if is_uitest_path(rel):
        if "uitest-launch" not in tags:
            for i, line in enumerate(lines, 1):
                if re.search(r"\.launch\s*\(\s*\)", line):
                    hit(hits, rel, i, "uitest-launch", "不連網",
                        "UI 測試要用 launchForVibeTest() 啟動 app，才會帶上不連網的攔截旗標。")
        return

    if is_test_path(rel):
        return

    debug_only = wholly_debug_only(code)
    for rule_id, category, pattern, message, exempt_tag in NETWORK_RULES + STORAGE_RULES:
        if exempt_tag and exempt_tag in tags:
            # 網路的豁免另有條件：整個檔案要包在 #if DEBUG 裡，正式 build 才不會含它。
            if exempt_tag != "urlsession" or debug_only:
                continue
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    hit(hits, rel, i, rule_id, category,
                        "這個檔案標了 urlsession 豁免，但整個檔案沒有包在 #if DEBUG 裡，正式 build 會含這段連網程式碼。")
            continue
        regex = re.compile(pattern)
        for i, line in enumerate(lines, 1):
            if regex.search(line):
                hit(hits, rel, i, rule_id, category, message)

    check_swiftdata_setup(lines, rel, hits, tags)
    check_user_defaults(lines, rel, hits, code)


def check_swiftdata_setup(lines, rel, hits, tags):
    if "store-setup" in tags:
        return
    for i, line in enumerate(lines, 1):
        if re.search(r"\bModel(Container|Configuration)\s*\(", line) and "isStoredInMemoryOnly: true" not in line:
            hit(hits, rel, i, "store-setup", "唯一的儲存方式",
                "自己開一個 SwiftData 資料庫。資料庫只能由範本的 DataStack 開在資料根目錄。")
        elif re.search(r"\.modelContainer\s*\(\s*for\s*:", line) and "inMemory: true" not in line:
            hit(hits, rel, i, "store-setup", "唯一的儲存方式",
                ".modelContainer(for:) 會把資料庫開在 SwiftData 的預設位置，備份就備份不到了。")


def check_user_defaults(lines, rel, hits, code):
    """介面偏好的 key 一律以 ui. 開頭；讀不出 key 的寫法一律要求改成直接寫字串。"""
    uses_defaults = "UserDefaults" in code
    for i, line in enumerate(lines, 1):
        for match in re.finditer(r"@AppStorage\s*\(\s*(\"([^\"]*)\"|[^)\s,]+)", line):
            literal = match.group(2)
            if literal is None:
                hit(hits, rel, i, "prefs-key", "唯一的儲存方式",
                    "@AppStorage 的 key 不是直接寫出來的字串，檢查不到它是不是介面偏好。請直接寫成 \"ui.xxx\"。")
            elif not literal.startswith("ui."):
                hit(hits, rel, i, "prefs-key", "唯一的儲存方式",
                    f"UserDefaults 只能存介面偏好，key 要以 ui. 開頭（現在是 \"{literal}\"）。使用者的資料請存 SwiftData。")
        if not uses_defaults:
            continue
        if not re.search(r"\.(set|setValue)\s*\(", line):
            continue
        for match in re.finditer(r"forKey\s*:\s*(\"([^\"]*)\"|[^)\s,]+)", line):
            literal = match.group(2)
            if literal is None:
                hit(hits, rel, i, "prefs-key", "唯一的儲存方式",
                    "UserDefaults 的 key 不是直接寫出來的字串，檢查不到它是不是介面偏好。請直接寫成 \"ui.xxx\"。")
            elif not literal.startswith("ui."):
                hit(hits, rel, i, "prefs-key", "唯一的儲存方式",
                    f"UserDefaults 只能存介面偏好，key 要以 ui. 開頭（現在是 \"{literal}\"）。使用者的資料請存 SwiftData。")


# ─── 相依白名單 ────────────────────────────────────────────────────────

def load_allowlist(path):
    names = set()
    if not os.path.exists(path):
        return names
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.split("#", 1)[0].strip()
            if line:
                names.add(line.lower())
    return names


def package_name(value):
    name = value.strip().rstrip("/")
    name = name.split("/")[-1]
    for suffix in (".git", ".json", ".zip"):
        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]
    return name


def check_dependencies(root, allowlist, hits):
    for full, rel in walk_files(root):
        base = os.path.basename(full)
        if base.endswith(".pbxproj"):
            check_lines(full, rel, hits, allowlist,
                        r"repositoryURL\s*=\s*\"([^\"]+)\"",
                        "專案裡加了 Swift Package")
            check_lines(full, rel, hits, allowlist,
                        r"isa\s*=\s*XCLocalSwiftPackageReference",
                        "專案裡加了本機 Swift Package（它自己也可能再相依別的套件）")
        elif base == "Package.resolved":
            check_resolved(full, rel, hits, allowlist)
        elif base == "Package.swift":
            check_lines(full, rel, hits, allowlist,
                        r"\.package\s*\(\s*(?:name\s*:\s*\"[^\"]*\"\s*,\s*)?(?:url|id)\s*:\s*\"([^\"]+)\"",
                        "Package.swift 裡宣告了相依套件")
        elif base in ("Podfile", "Podfile.lock"):
            check_lines(full, rel, hits, allowlist,
                        r"^\s*(?:pod|  - )\s*[\"']([^\"']+)[\"']",
                        "CocoaPods 相依")
        elif base in ("Cartfile", "Cartfile.private", "Cartfile.resolved"):
            check_lines(full, rel, hits, allowlist,
                        r"^\s*(?:github|git|binary)\s+\"([^\"]+)\"",
                        "Carthage 相依")

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in list(dirnames) + filenames:
            if name.endswith((".xcframework", ".framework", ".a")):
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                if package_name(name).lower() in allowlist:
                    continue
                hit(hits, rel, 1, "dependency", "相依白名單",
                    f"專案裡放了二進位套件「{name}」。v1 不加任何第三方套件；真的需要，先加進 boundaries-allowlist.txt。")


def check_lines(path, rel, hits, allowlist, pattern, label):
    text = read_text(path)
    if text is None:
        return
    regex = re.compile(pattern)
    for i, line in enumerate(text.splitlines(), 1):
        match = regex.search(line)
        if not match:
            continue
        if match.groups():
            name = package_name(match.group(1))
            if name.lower() in allowlist:
                continue
            hit(hits, rel, i, "dependency", "相依白名單",
                f"{label}「{name}」。v1 不加第三方套件；真的需要，先把它加進 boundaries-allowlist.txt。")
        else:
            hit(hits, rel, i, "dependency", "相依白名單",
                f"{label}。v1 不加第三方套件；真的需要，先把它加進 boundaries-allowlist.txt。")


def check_resolved(path, rel, hits, allowlist):
    text = read_text(path)
    if text is None:
        return
    names = []
    try:
        data = json.loads(text)
        pins = data.get("pins") or data.get("object", {}).get("pins", [])
        for pin in pins:
            names.append(pin.get("identity") or pin.get("package") or pin.get("location", ""))
    except (ValueError, AttributeError):
        names = re.findall(r"\"(?:identity|package)\"\s*:\s*\"([^\"]+)\"", text)
    lines = text.splitlines()
    for name in names:
        clean = package_name(name)
        if not clean or clean.lower() in allowlist:
            continue
        line_no = next((i for i, line in enumerate(lines, 1) if name in line), 1)
        hit(hits, rel, line_no, "dependency", "相依白名單",
            f"Package.resolved 裡有套件「{clean}」。v1 不加第三方套件；真的需要，先把它加進 boundaries-allowlist.txt。")


# ─── 主程式 ────────────────────────────────────────────────────────────

def run(root, allowlist_path):
    allowlist = load_allowlist(allowlist_path)
    hits, exempt_log = [], []
    for full, rel in walk_files(root):
        if full.endswith(".swift"):
            check_swift_file(full, rel, hits, exempt_log)
    check_dependencies(root, allowlist, hits)
    hits.sort(key=lambda h: (h["file"], h["line"], h["rule"]))
    return hits, exempt_log


def main(argv=None):
    parser = argparse.ArgumentParser(description="vibe 專案的邊界檢查（盡力而為）")
    parser.add_argument("project", help="專案資料夾")
    parser.add_argument("--allowlist", default=DEFAULT_ALLOWLIST, help="相依白名單檔案")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.project)
    if not os.path.isdir(root):
        print(f"找不到專案資料夾：{args.project}", file=sys.stderr)
        return 2

    hits, exempt_log = run(root, args.allowlist)

    if args.json:
        print(json.dumps({
            "hits": hits,
            "exemptions": [{"file": f, "tags": t} for f, t in sorted(exempt_log)],
        }, ensure_ascii=False, indent=2))
        return 1 if hits else 0

    for h in hits:
        print(f"{h['file']}:{h['line']}: {h['category']}｜{h['message']}  [{h['rule']}]")
    if exempt_log:
        print("\n有豁免標記的檔案（審查時順便看一眼）：")
        for path, tags in sorted(exempt_log):
            print(f"  {path}：{', '.join(tags)}")
    print()
    if hits:
        print(f"共 {len(hits)} 處越界。每一處都要嘛改掉，要嘛照 ios-vibe 的「超出範圍的需求」跟使用者說清楚。")
        return 1
    print("邊界檢查通過：0 處越界（這是盡力而為的檢查，不等於證明）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

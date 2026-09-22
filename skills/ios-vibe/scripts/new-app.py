#!/usr/bin/env python3
"""從 ios-vibe 的範本產生一個新的 vibe 專案。

用法：
    python3 new-app.py <目的資料夾> <App 名稱> <bundle id 前綴>

例如：
    python3 new-app.py ~/Projects/記帳 MoneyLog com.example

做的事：把 templates/app 複製過去、把裡面的 VibeApp 換成你的 App 名稱
（資料夾名、專案檔、scheme、Swift 型別名、bundle id、CLAUDE.md／AGENTS.md），
最後 git init 並做第一個 commit。

App 名稱只能用英文字母和數字，而且要用字母開頭——它同時是 Xcode 專案名、
Swift 模組名與型別名的一部分，符號或空白會讓專案開不起來。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "templates", "app"))
PLACEHOLDER = "VibeApp"

# 複製時直接跳過的東西（build 產物、編輯器暫存、AI 的執行期紀錄）。
SKIP_NAMES = {".DS_Store", "xcuserdata", "DerivedData", "build", ".build", ".vibe", "__pycache__", ".git"}

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*(\.[A-Za-z0-9-]+)*$")

# 這些名字會和範本自己的型別、或常用的框架撞名，撞了專案就編不過。
RESERVED_NAMES = {
    # 範本自己的型別
    "entry", "datafiles", "datalocation", "databootstrapper", "dataformat",
    "dataformatfile", "datastack", "datasession", "datanotice", "applaunch",
    "rootview", "entrylistview", "addentryview", "networkblocker",
    "appschemav1", "appmigrationplan", "latestschema", "tempdirectory",
    # 框架與語言關鍵字
    "swift", "swiftui", "swiftdata", "foundation", "uikit", "appkit", "combine",
    "observation", "xctest", "testing", "synchronization", "os", "darwin",
    "app", "scene", "view", "text", "list", "image", "color", "button", "data",
    "date", "url", "string", "int", "double", "bool", "array", "dictionary",
    "set", "task", "result", "model", "query", "schema", "type", "self", "any",
}


def fail(message):
    print(f"錯誤：{message}", file=sys.stderr)
    return 2


def validate(name, prefix, destination):
    if not NAME_RE.match(name):
        return fail(f"App 名稱「{name}」不合法。只能用英文字母和數字，而且要用字母開頭，例如 MoneyLog。")
    if name.lower() in RESERVED_NAMES:
        return fail(f"App 名稱「{name}」會和範本或系統框架的名字撞在一起，專案會編不過。換一個名字，例如 {name}Box。")
    if not PREFIX_RE.match(prefix):
        return fail(f"bundle id 前綴「{prefix}」不合法。用像 com.example 這種格式（英文字母、數字、點、減號）。")
    if os.path.exists(destination) and os.listdir(destination):
        return fail(f"目的資料夾「{destination}」已經有東西了。請換一個空的資料夾，免得蓋掉既有檔案。")
    if not os.path.isdir(TEMPLATE_DIR):
        return fail(f"找不到範本資料夾：{TEMPLATE_DIR}")
    return 0


def copy_template(destination):
    shutil.copytree(
        TEMPLATE_DIR,
        destination,
        ignore=shutil.ignore_patterns(*SKIP_NAMES),
        dirs_exist_ok=True,
    )


def rewrite_contents(destination, name, prefix):
    """把每個讀得懂的文字檔裡的 VibeApp 換成新名字，bundle id 換成新前綴。"""
    changed = 0
    for dirpath, dirnames, filenames in os.walk(destination):
        dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    text = handle.read()
            except (UnicodeDecodeError, OSError):
                continue  # 圖片之類的二進位檔，原封不動照搬
            original = text
            text = re.sub(
                r"(PRODUCT_BUNDLE_IDENTIFIER\s*=\s*)com\.example\.",
                lambda m: m.group(1) + prefix + ".",
                text,
            )
            text = text.replace(PLACEHOLDER, name)
            if text != original:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(text)
                changed += 1
    return changed


def rename_paths(destination, name):
    """資料夾與檔名裡的 VibeApp 也要換掉（由深到淺改，才不會改到一半找不到路徑）。"""
    for dirpath, dirnames, filenames in os.walk(destination, topdown=False):
        for entry in filenames + dirnames:
            if PLACEHOLDER not in entry:
                continue
            os.rename(
                os.path.join(dirpath, entry),
                os.path.join(dirpath, entry.replace(PLACEHOLDER, name)),
            )


def git(destination, *args, extra_config=()):
    command = ["git", "-C", destination]
    for key, value in extra_config:
        command += ["-c", f"{key}={value}"]
    command += list(args)
    return subprocess.run(command, capture_output=True, text=True)


def git_identity(destination):
    name = git(destination, "config", "user.name").stdout.strip()
    email = git(destination, "config", "user.email").stdout.strip()
    return name, email


def make_first_commit(destination, app_name):
    """git init ＋第一個 commit。用目的資料夾自己的 git 設定；沒設就用預設身分並提醒。"""
    branch = git(destination, "config", "init.defaultBranch").stdout.strip() or "main"
    init = subprocess.run(["git", "init", "-b", branch, destination], capture_output=True, text=True)
    if init.returncode != 0:
        return False, f"git init 失敗：{init.stderr.strip()}", False

    name, email = git_identity(destination)
    used_fallback = not (name and email)
    extra_config = ()
    if used_fallback:
        extra_config = (("user.name", "ios-vibe"), ("user.email", "noreply@example.com"))

    add = git(destination, "add", "-A")
    if add.returncode != 0:
        return False, f"git add 失敗：{add.stderr.strip()}", used_fallback
    commit = git(
        destination, "commit", "-m", f"建立 {app_name}：從 ios-vibe 範本產生",
        extra_config=extra_config,
    )
    if commit.returncode != 0:
        return False, f"git commit 失敗：{commit.stderr.strip() or commit.stdout.strip()}", used_fallback
    return True, branch, used_fallback


def main(argv=None):
    parser = argparse.ArgumentParser(description="從 ios-vibe 範本產生一個新專案")
    parser.add_argument("destination", help="目的資料夾（不存在或空的）")
    parser.add_argument("name", help="App 名稱（英數，字母開頭）")
    parser.add_argument("bundle_prefix", help="bundle id 前綴，例如 com.example")
    args = parser.parse_args(argv)

    destination = os.path.abspath(os.path.expanduser(args.destination))
    problem = validate(args.name, args.bundle_prefix, destination)
    if problem:
        return problem

    os.makedirs(destination, exist_ok=True)
    copy_template(destination)
    rewrite_contents(destination, args.name, args.bundle_prefix)
    rename_paths(destination, args.name)

    ok, detail, used_fallback = make_first_commit(destination, args.name)

    print(f"專案建好了：{destination}")
    print(f"  專案檔：{args.name}.xcodeproj（scheme：{args.name}）")
    print(f"  bundle id：{args.bundle_prefix}.{args.name}")
    if ok:
        print(f"  已經做好第一個 commit（分支 {detail}）")
    else:
        print(f"  ⚠️ {detail}")
    if used_fallback:
        print("  ⚠️ 這台電腦還沒設定 git 身分，這次的 commit 先用 ios-vibe <noreply@example.com>。")
        print("     之後想換成自己的名字：git config --global user.name \"你的名字\"、")
        print("     git config --global user.email \"你的信箱\"。")
    print()
    print("下一步：")
    print(f"  跑一次測試確認環境沒問題："
          f"xcodebuild -project {args.name}.xcodeproj -scheme {args.name} "
          f"-destination 'platform=iOS Simulator,name=<模擬器型號>' test")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

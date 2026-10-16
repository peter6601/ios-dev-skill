#!/usr/bin/env python3
"""PreToolUse hook for /ios-dev: remind the test rules when an Edit/Write touches `*Tests.swift`.

Registered in SKILL.md frontmatter (matcher `Edit|Write`).  Reads the hook JSON on stdin; when
`tool_input.file_path` ends with `Tests.swift` it prints `additionalContext` so the rules land in
Claude's context right before the edit.  It never blocks: anything else, or input it cannot parse,
exits 0 silently — the guard must not become a failure point.

The rules here are a short copy of handoff-checklist.md「開發前」's 測試的硬規則; change both together.
"""
import json, sys

RULES = """[ios-dev 測試規則] 你正要改測試檔 {path}：
1. 不得為了讓測試通過而改既有斷言、刪測試、skip（.disabled、XCTSkip、註解掉）或降低門檻（容差、timeout、覆蓋率）。
2. 確實要改既有測試時，回報寫明是哪條 AC 變了（AC 編號、舊→新、誰決定）；寫不出來就回去修實作。
3. 新 case 標「依規格」或「鎖現況」；只有重構的行為快照可以鎖現況，用 characterization_ 前綴或註解標記。
4. 挑 case：先列條件，等價分割＋決策表（組合多用 pairwise）；錢、授權、持久化、最近出過錯的地方多測；至少一個組合／順序／同時案例。
5. 斷言要驗行為結果，不要照抄實作的計算過程（鏡像實作的測試抓不到錯）。"""


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        path = (data.get("tool_input") or {}).get("file_path") or ""
    except (ValueError, AttributeError):
        return 0
    if not path.endswith("Tests.swift"):
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": RULES.format(path=path),
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

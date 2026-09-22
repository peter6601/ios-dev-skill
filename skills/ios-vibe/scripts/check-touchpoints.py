#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-touchpoints.py — 檢查 `ios-dev` 家族 skill 的「接觸點標記」。

標記長這樣（整行只有這一行註解，可以有縮排、`>`、樹狀線）：

    <!-- touchpoint: ios-dev-007 kind=gate -->
    <!-- touchpoint: none -->          ← 這句不是接觸點，豁免

四項檢查：

1. **漏標**（盡力而為）：在被掃的 skill 檔裡找疑似接觸點的句子，附近沒有標記就報錯。
2. 每個標記的 `kind` 合法、編號格式正確、編號在全 repo 不重複。
3. 每個 `kind=gate` 的標記，在例外表（`--rules`）都有一列。
4. 例外表的每個編號都指向真實存在的標記。

**第 1 項是盡力而為，不保證抓得完。** 它只認得 `KEYWORDS` 列的那些說法：
新增的接觸點只要換一種寫法（不寫「停下來」而寫「先跟他核對一下再繼續」），
這裡就抓不到，四項檢查照樣全過。漏掉的那一層由執行期紀錄補抓——
`ios-vibe` 每次提問都往 `.vibe/touchpoint-log.jsonl` 記一行，對不上編號的記 `unmapped`，
`check-touchpoints.py --log <路徑>` 一跑就會把它們連問題原文一起列出來。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --- 掃描範圍 -----------------------------------------------------------------

# 這些 skill 要做第 1 項（關鍵字漏標掃描）＋登錄標記。
SCANNED_SKILLS = [
    "ios-dev",
    "phase-workflow",
    "ios-investigate",
    "ios-review",
    "office-hours",
    "ios-polish",
    "ios-distill",
    "ios-critique",
    "localize-strings",
]

# 這些 skill 只登錄標記（第 2、4 項與 --log 認得它們的編號），不做關鍵字掃描——
# 它們本身就在講規則，關鍵字會整篇誤報。
REGISTRY_ONLY_SKILLS = ["ios-vibe"]

VALID_KINDS = {"engineering", "product", "mixed", "code-review", "command", "gate"}

DEFAULT_RULES = os.path.join("skills", "ios-vibe", "references", "touchpoint-rules.md")

# --- 標記格式 -----------------------------------------------------------------

# 整行只有一行標記；允許縮排、blockquote 的 `>`、流程圖的樹狀線。
MARKER_LINE = re.compile(
    r"^[\s>│├└┌┘┐─|]*<!--\s*touchpoint:\s*(?P<body>.*?)\s*-->\s*$"
)
# 只要出現 "touchpoint:" 就當成有人想標記，用來抓寫壞的格式。
MARKER_LOOSE = re.compile(r"<!--[^>]*touchpoint\s*:", re.IGNORECASE)
MARKER_BODY = re.compile(r"^(?P<id>[a-z0-9]+(?:-[a-z0-9]+)*)-(?P<num>\d{3})\s+kind=(?P<kind>[a-z-]+)$")
RULES_ID = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)*-\d{3})`")

# --- 疑似接觸點的關鍵字 --------------------------------------------------------
#
# 校準原則：只留「這一句在叫流程停下來、等人、或把決定權交出去」的說法。
# 「給使用者」「由使用者」「確認」這種太泛的字眼會把整份文件都掃成接觸點，不收。
KEYWORDS = [
    r"AskUserQuestion",
    r"詢問",
    r"暫停",
    r"停下來",
    r"\bSTOP\b",
    r"stop\s*[+＋]",          # stop + ask / stop＋問
    r"等使用者",
    r"等我",
    r"等回答",
    r"確認後[^。]{0,6}才",
    r"人工",
    r"人審",
    r"提問",
    r"問使用者|問用戶|問人|問我",
    r"問「",
    r"問一題",
    r"向使用者",
    r"請使用者",
    r"使用者輸入",
    r"使用者\s?(確認|核准|核可|同意|決定|裁定|判斷|定案|看過|讀完|ack)",
    r"(交|列|回報)給?使用者(看|補|判斷|裁定|決定)?",
    r"不(得|自行)?\s?commit|絕不\s?commit",
    r"新 session",
]
KEYWORD_RE = re.compile("|".join(KEYWORDS))

NEAR = 3  # 標記要在「上方 3 行內」


class Marker:
    def __init__(self, path, lineno, ident, kind):
        self.path = path
        self.lineno = lineno
        self.ident = ident  # None = <!-- touchpoint: none -->
        self.kind = kind


class Doc:
    """把一個 markdown 檔拆成：frontmatter／fenced code block／表格／HTML 註解／標記。

    `fence_markers=True` 時，fenced code block 裡的標記也算數——`phase-workflow` 的流程圖
    本來就寫在 code block 裡，標記只能標在裡面。只登錄用的檔（`ios-vibe` 自己）設 False，
    免得把文件裡的「格式長這樣」範例當成真的標記。
    """

    def __init__(self, path, text, fence_markers=True):
        self.path = path
        self.fence_markers = fence_markers
        self.lines = text.split("\n")
        n = len(self.lines)
        self.start = 0
        if self.lines and self.lines[0].strip() == "---":
            for i in range(1, n):
                if self.lines[i].strip() == "---":
                    self.start = i + 1
                    break

        self.fence = [None] * n      # 行 -> code block 編號
        self.fence_open = {}         # code block 編號 -> 起始行
        self.table = [None] * n      # 行 -> 表格編號
        self.table_open = {}
        self.comment = [None] * n    # 行 -> 多行 HTML 註解編號（標記不能塞進註解裡，只能標在整段之前）
        self.comment_open = {}
        self.marker = [None] * n     # 行 -> Marker

        fence_char = None
        fence_len = 0
        fence_id = 0
        table_id = 0
        comment_id = 0
        cur_table = None
        in_comment = False

        for i in range(self.start, n):
            raw = self.lines[i]
            stripped = raw.strip()

            if fence_char is not None:
                self.fence[i] = fence_id
                if stripped.startswith(fence_char * fence_len) and set(stripped) <= set(fence_char):
                    fence_char = None
                elif fence_markers:
                    self._read_marker(i, raw)
                continue

            m = re.match(r"^\s*(`{3,}|~{3,})", raw)
            if m and not in_comment:
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                fence_id += 1
                self.fence[i] = fence_id
                self.fence_open[fence_id] = i
                continue

            if in_comment:
                self.comment[i] = comment_id
                if "-->" in raw:
                    in_comment = False
                continue

            if self._read_marker(i, raw):
                continue

            if "<!--" in raw and "-->" not in raw.split("<!--", 1)[1]:
                comment_id += 1
                self.comment[i] = comment_id
                self.comment_open[comment_id] = i
                in_comment = True
                continue

            if stripped.startswith("|"):
                if cur_table is None:
                    table_id += 1
                    cur_table = table_id
                    self.table_open[table_id] = i
                self.table[i] = cur_table
                continue
            cur_table = None

    # --- 小工具 ---------------------------------------------------------------

    def _read_marker(self, i, raw):
        mk = MARKER_LINE.match(raw)
        if not mk:
            return False
        body = mk.group("body").strip()
        if body == "none":
            self.marker[i] = Marker(self.path, i, None, None)
        else:
            b = MARKER_BODY.match(body)
            if b:
                self.marker[i] = Marker(
                    self.path, i, f"{b.group('id')}-{b.group('num')}", b.group("kind")
                )
            else:
                self.marker[i] = Marker(self.path, i, "", None)  # 格式壞掉
        return True

    def is_blank(self, i):
        s = self.lines[i].strip()
        return s == "" or s == ">" or re.fullmatch(r">+", s) is not None

    def is_heading(self, i):
        return re.match(r"^\s*(>\s*)*#{1,6}\s", self.lines[i]) is not None

    def is_list_item(self, i):
        return re.match(r"^\s*(>\s*)*([-*+]|\d+[.)])\s", self.lines[i]) is not None

    def block_start(self, i):
        """往上走到這個段落／list item 的第一行。"""
        j = i
        while j > self.start:
            if self.is_list_item(j) or self.is_heading(j):
                break
            p = j - 1
            if (
                self.is_blank(p)
                or self.is_heading(p)
                or self.marker[p] is not None
                or self.fence[p] is not None
                or self.table[p] is not None
            ):
                break
            j -= 1
        return j

    def markers_in(self, lo, hi):
        lo = max(lo, 0)
        return [self.marker[k] for k in range(lo, hi + 1) if 0 <= k < len(self.lines) and self.marker[k]]

    def governing_markers(self, container_start):
        """容器（表格／code block）上方那一疊標記；上面若是引言段落，連引言的標記一起算。"""
        j = container_start - 1
        while j >= self.start and (self.is_blank(j) or self.marker[j] is not None):
            j -= 1
        lo = container_start
        if j >= self.start and not self.is_heading(j) and self.fence[j] is None and self.table[j] is None:
            lo = self.block_start(j) - NEAR
        else:
            lo = j + 1 - NEAR
        return self.markers_in(lo, container_start - 1)


def md_files(repo, skills):
    out = []
    for skill in skills:
        base = os.path.join(repo, "skills", skill)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for f in sorted(files):
                if f.endswith(".md"):
                    out.append(os.path.join(root, f))
    return sorted(out)


def rel(repo, path):
    try:
        r = os.path.relpath(path, repo)
    except ValueError:
        return path
    return path if r.startswith("..") else r


def group_lines(nums, gap=2):
    """把連在一起的行併成一組（連續幾行寫同一件事，只要一個標記）。"""
    groups = []
    for n in sorted(nums):
        if groups and n - groups[-1][-1] <= gap:
            groups[-1].append(n)
        else:
            groups.append([n])
    return groups


def load_docs(repo, skills, fence_markers=True):
    docs = []
    for path in md_files(repo, skills):
        with open(path, encoding="utf-8") as fh:
            docs.append(Doc(path, fh.read(), fence_markers=fence_markers))
    return docs


# --- 第 1 項：漏標 -------------------------------------------------------------

def check_missing(doc, repo, errors):
    fence_miss = {}
    table_hits = {}
    comment_miss = {}

    for i in range(doc.start, len(doc.lines)):
        if doc.marker[i] is not None:
            continue
        line = doc.lines[i]
        if not KEYWORD_RE.search(line):
            continue

        if doc.fence[i] is not None:
            if doc.markers_in(i - NEAR, i - 1):
                continue
            fence_miss.setdefault(doc.fence[i], []).append(i)
            continue

        if doc.table[i] is not None:
            table_hits.setdefault(doc.table[i], []).append(i)
            continue

        if doc.comment[i] is not None:
            comment_miss.setdefault(doc.comment[i], []).append(i)
            continue

        bs = doc.block_start(i)
        if doc.markers_in(min(bs, i) - NEAR, i - 1):
            continue
        errors.append(
            f"{rel(repo, doc.path)}:{i + 1} 這句看起來是接觸點（會停下來問人或擋住流程），"
            f"上方 3 行內卻沒有 touchpoint 標記；不是接觸點就加 <!-- touchpoint: none -->"
        )

    for fid, miss in fence_miss.items():
        start = doc.fence_open[fid]
        need = group_lines(miss)
        have = len(doc.governing_markers(start))
        if have < len(need):
            where = "、".join(str(g[0] + 1) for g in need)
            errors.append(
                f"{rel(repo, doc.path)}:{start + 1} 這段 code block 裡有 {len(need)} 處看起來是接觸點"
                f"（第 {where} 行），但只找到 {have} 個標記；請在那一行上一行、或整段 code block 之前補標記"
            )

    for cid, miss in comment_miss.items():
        start = doc.comment_open[cid]
        need = group_lines(miss)
        have = len(doc.governing_markers(start))
        if have < len(need):
            where = "、".join(str(g[0] + 1) for g in need)
            errors.append(
                f"{rel(repo, doc.path)}:{start + 1} 這段 HTML 註解裡有 {len(need)} 處看起來是接觸點"
                f"（第 {where} 行），但只找到 {have} 個標記；標記不能塞進註解裡，請放在整段註解之前"
            )

    for tid, rows in table_hits.items():
        start = doc.table_open[tid]
        need = group_lines(rows, gap=0)  # 表格一列就是一個點，不合併
        have = len(doc.governing_markers(start))
        if have < len(need):
            where = "、".join(str(g[0] + 1) for g in need)
            errors.append(
                f"{rel(repo, doc.path)}:{start + 1} 這張表格有 {len(need)} 列看起來是接觸點"
                f"（第 {where} 行），但表格前面只有 {have} 個標記；標記放在整張表之前，一行一個"
            )


# --- 第 2 項：標記本身 ---------------------------------------------------------

def check_markers(docs, repo, errors):
    """回傳 {編號: Marker}；順便檢查格式、kind 與重複。"""
    registry = {}
    for doc in docs:
        skill = None
        parts = rel(repo, doc.path).split(os.sep)
        if len(parts) >= 2 and parts[0] == "skills":
            skill = parts[1]
        for i in range(doc.start, len(doc.lines)):
            mk = doc.marker[i]
            line = doc.lines[i]
            if mk is None:
                if doc.fence[i] is not None and not doc.fence_markers:
                    continue  # 只登錄用的檔：code block 裡的是「格式長這樣」範例
                if MARKER_LOOSE.search(line):
                    errors.append(
                        f"{rel(repo, doc.path)}:{i + 1} 這行想標 touchpoint 但格式不對；"
                        f"整行只能是 <!-- touchpoint: <skill>-NNN kind=<kind> --> 或 <!-- touchpoint: none -->"
                    )
                continue
            if mk.ident is None:
                continue  # none 豁免
            if mk.ident == "":
                errors.append(
                    f"{rel(repo, doc.path)}:{i + 1} 標記內容看不懂；格式是 "
                    f"<!-- touchpoint: <skill>-NNN kind=<kind> -->（NNN 是三位數）"
                )
                continue
            if mk.kind not in VALID_KINDS:
                errors.append(
                    f"{rel(repo, doc.path)}:{i + 1} kind=`{mk.kind}` 不是合法的種類；"
                    f"只能是 {'／'.join(sorted(VALID_KINDS))}"
                )
            prefix = mk.ident.rsplit("-", 1)[0]
            if skill and prefix != skill:
                errors.append(
                    f"{rel(repo, doc.path)}:{i + 1} 編號 `{mk.ident}` 的前綴不是所在 skill 的資料夾名 `{skill}`"
                )
            if mk.ident in registry:
                first = registry[mk.ident]
                errors.append(
                    f"{rel(repo, doc.path)}:{i + 1} 編號 `{mk.ident}` 重複了"
                    f"（另一個在 {rel(repo, first.path)}:{first.lineno + 1}）"
                )
                continue
            registry[mk.ident] = mk
    return registry


# --- 第 3、4 項：例外表 ---------------------------------------------------------

def parse_rules(path):
    """讀例外表：`## 例外表` 之下所有表格列，第一格裡的 `<skill>-NNN` 就是這一列涵蓋的編號。"""
    ids = {}
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    level = None
    in_table_section = False
    for i, line in enumerate(lines):
        h = re.match(r"^(#{1,6})\s*(.+?)\s*$", line)
        if h:
            if in_table_section and len(h.group(1)) <= level:
                break
            if re.match(r"^例外表", h.group(2)):
                in_table_section = True
                level = len(h.group(1))
            continue
        if not in_table_section:
            continue
        if not line.strip().startswith("|"):
            continue
        cells = line.strip().strip("|").split("|")
        if not cells:
            continue
        first = cells[0]
        if set(first.strip()) <= set("-: ") and first.strip():
            continue  # 分隔列
        for ident in RULES_ID.findall(first):
            ids.setdefault(ident, i)
    return ids


def check_rules(registry, rules_path, repo, errors, warnings):
    if not os.path.isfile(rules_path):
        warnings.append(
            f"找不到例外表 {rel(repo, rules_path)}，跳過第 3、4 項檢查（gate 是否入表、表裡的編號是否存在）"
        )
        return
    listed = parse_rules(rules_path)
    for ident, mk in sorted(registry.items()):
        if mk.kind == "gate" and ident not in listed:
            errors.append(
                f"{rel(repo, mk.path)}:{mk.lineno + 1} `{ident}` 是 kind=gate（硬關卡），"
                f"例外表 {rel(repo, rules_path)} 卻沒有對應的一列"
            )
    for ident, lineno in sorted(listed.items(), key=lambda kv: kv[1]):
        if ident not in registry:
            errors.append(
                f"{rel(repo, rules_path)}:{lineno + 1} 例外表列了 `{ident}`，但 repo 裡沒有這個標記"
            )


# --- --log 模式 ---------------------------------------------------------------

def check_log(log_path, registry, repo, errors):
    if not os.path.isfile(log_path):
        errors.append(f"找不到執行期紀錄 {log_path}")
        return
    with open(log_path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"{log_path}:{n} 這一行不是合法 JSON，讀不出提問紀錄")
                continue
            if not isinstance(entry, dict):
                errors.append(f"{log_path}:{n} 這一行不是一個 JSON 物件")
                continue
            ident = entry.get("id")
            question = entry.get("question", "")
            if ident is None:
                errors.append(f"{log_path}:{n} 這筆紀錄沒有 id 欄位；問題原文：{question or '（沒有記）'}")
                continue
            if "question" not in entry:
                errors.append(f"{log_path}:{n} 這筆紀錄沒有 question 欄位（id=`{ident}`）")
            if ident == "unmapped":
                errors.append(
                    f"{log_path}:{n} 這次提問對不上任何接觸點編號（unmapped），"
                    f"代表有接觸點漏標；問題原文：{question or '（沒有記）'}"
                )
            elif ident not in registry:
                errors.append(
                    f"{log_path}:{n} 編號 `{ident}` 在 repo 裡找不到對應的標記；"
                    f"問題原文：{question or '（沒有記）'}"
                )


# --- main ---------------------------------------------------------------------

def default_repo():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def main(argv=None):
    ap = argparse.ArgumentParser(description="檢查 ios-dev 家族 skill 的接觸點標記")
    ap.add_argument("--repo", default=None, help="repo 根目錄（預設：這支腳本往上三層）")
    ap.add_argument("--rules", default=None, help=f"例外表路徑（預設：{DEFAULT_RULES}）")
    ap.add_argument("--log", default=None, help="讀 .vibe/touchpoint-log.jsonl，檢查執行期紀錄的編號")
    ap.add_argument("--skills", default=None, help="覆寫要掃描的 skill（逗號分隔，測試用）")
    ap.add_argument(
        "--registry-skills", default=None, help="覆寫只登錄不掃描的 skill（逗號分隔，測試用）"
    )
    args = ap.parse_args(argv)

    repo = os.path.abspath(args.repo or default_repo())
    scanned = args.skills.split(",") if args.skills else SCANNED_SKILLS
    registry_only = (
        args.registry_skills.split(",") if args.registry_skills is not None else REGISTRY_ONLY_SKILLS
    )
    registry_only = [s for s in registry_only if s]
    rules_path = os.path.abspath(args.rules) if args.rules else os.path.join(repo, DEFAULT_RULES)

    errors = []
    warnings = []

    scan_docs = load_docs(repo, scanned)
    extra_docs = load_docs(repo, registry_only, fence_markers=False)
    registry = check_markers(scan_docs + extra_docs, repo, errors)

    if args.log:
        check_log(args.log, registry, repo, errors)
    else:
        for doc in scan_docs:
            check_missing(doc, repo, errors)
        check_rules(registry, rules_path, repo, errors, warnings)

    for w in warnings:
        print(f"warn  {w}")
    for e in errors:
        print(f"error {e}")

    if args.log:
        print(f"\n執行期紀錄：{args.log}；已登錄的接觸點 {len(registry)} 個；問題 {len(errors)} 個")
    else:
        kinds = {}
        for mk in registry.values():
            kinds[mk.kind] = kinds.get(mk.kind, 0) + 1
        nones = sum(
            1
            for doc in scan_docs
            for mk in doc.marker
            if mk is not None and mk.ident is None
        )
        summary = "  ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
        print(f"\n標記 {len(registry)} 個（{summary}）；none 豁免 {nones} 個；問題 {len(errors)} 個")
        if nones > 40:
            print("warn  none 豁免超過 40 個，代表關鍵字太寬，回去調 KEYWORDS")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

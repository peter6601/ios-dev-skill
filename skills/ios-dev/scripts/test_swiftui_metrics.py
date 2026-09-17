#!/usr/bin/env python3
"""Regression tests for swiftui-metrics.py — the cases Codex found on 2026-09-17.

Run: python3 -m unittest skills.ios-dev.scripts.test_swiftui_metrics
 or: python3 skills/ios-dev/scripts/test_swiftui_metrics.py
"""
import json, os, subprocess, sys, tempfile, unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "swiftui-metrics.py")


def run(path, *args):
    p = subprocess.run([sys.executable, SCRIPT, path, "--json", *args],
                       capture_output=True, text=True)
    try:
        return p.returncode, json.loads(p.stdout)
    except json.JSONDecodeError:
        return p.returncode, None


def write(d, name, body):
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(body)


def long_lines(n, indent="      "):
    return "\n".join(f'{indent}Text("line {i}")' for i in range(n))


class MetricsRegression(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_second_view_in_same_file_is_measured(self):
        """Only the first `var body` used to be measured — the rest went unseen."""
        write(self.dir, "B.swift",
              'struct First: View {\n  var body: some View { Text("hi") }\n}\n'
              'struct Second: View {\n  var body: some View {\n    VStack {\n'
              + long_lines(95) + "\n    }\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        row = out["all"][0]
        self.assertEqual(row["body_view"], "Second")
        self.assertGreater(row["body"], 80)
        self.assertEqual([b["view"] for b in row["bodies"]], ["First", "Second"])

    def test_brace_inside_string_does_not_end_the_body(self):
        """A `Text("}")` at the body's outermost depth closed the count early."""
        write(self.dir, "C.swift",
              'struct C: View {\n  var body: some View {\n    Text("}")\n'
              + long_lines(95, "    ") + "\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        self.assertGreater(out["all"][0]["body"], 80)

    def test_braces_in_comments_are_ignored(self):
        write(self.dir, "D.swift",
              'struct D: View {\n  var body: some View {\n    // }\n    /* } */\n'
              + long_lines(95, "    ") + "\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        self.assertGreater(out["all"][0]["body"], 80)

    def test_raw_string_braces_are_ignored(self):
        """`#"… } …"#` has no escapes and ends only at `"#`."""
        write(self.dir, "R.swift",
              'struct R: View {\n  var body: some View {\n    Text(#"quote " } tail"#)\n'
              + long_lines(95, "    ") + "\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        self.assertGreater(out["all"][0]["body"], 80)

    def test_raw_string_escaped_delimiter(self):
        """A raw string escapes with `\#`, so `\#"#` is a quoted `"`, not the end."""
        write(self.dir, "RE.swift",
              'struct RE: View {\n  var body: some View {\n    Text(#"quote \\#"# } tail"#)\n'
              + long_lines(95, "    ") + "\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        self.assertGreater(out["all"][0]["body"], 80)

    def test_string_nested_in_interpolation(self):
        """`\\(…)` is code, so the string inside it must be blanked in turn."""
        write(self.dir, "I.swift",
              'struct I: View {\n  var body: some View {\n    Text("\\(String("}"))")\n'
              + long_lines(95, "    ") + "\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        self.assertGreater(out["all"][0]["body"], 80)

    def test_raw_multiline_string(self):
        write(self.dir, "M.swift",
              'struct M: View {\n  var body: some View {\n    Text(#"""\n    } } }\n    """#)\n'
              + long_lines(95, "    ") + "\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        self.assertGreater(out["all"][0]["body"], 80)

    def test_escaped_quote_does_not_end_the_string(self):
        write(self.dir, "Q.swift",
              'struct Q: View {\n  var body: some View {\n    Text("a\\"}")\n'
              + long_lines(95, "    ") + "\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        self.assertGreater(out["all"][0]["body"], 80)

    def test_isPresented_inside_a_string_is_not_counted(self):
        write(self.dir, "E.swift",
              'struct E: View {\n  var body: some View {\n'
              '    Text("isPresented: isPresented: isPresented:")\n  }\n}\n')
        code, out = run(self.dir)
        self.assertEqual(code, 0)
        self.assertEqual(out["all"][0]["isPresented"], 0)

    def test_real_gates_still_fire(self):
        write(self.dir, "F.swift",
              "struct F: View {\n"
              + "".join(f"  @State private var s{i} = false\n" for i in range(6))
              + '  var body: some View {\n    Text("x")\n'
              '      .sheet(isPresented: $s0) { Text("a") }\n'
              '      .sheet(isPresented: $s1) { Text("b") }\n'
              "      .onChange(of: vm.shouldRefresh) { _ in }\n  }\n}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 1)
        v = out["violators"][0]["violations"]
        self.assertIn("@State>5", v)
        self.assertIn("isPresented>1", v)
        self.assertIn("onChange(should*/did*)", v)

    def test_clean_file_exits_zero(self):
        write(self.dir, "G.swift",
              'struct G: View {\n  var body: some View {\n    Text("ok")\n  }\n}\n')
        code, out = run(self.dir)
        self.assertEqual(code, 0)
        self.assertEqual(out["violators"], [])

    def test_missing_path_is_an_input_error_not_a_pass(self):
        """It used to print prose and exit 0 — a typo looked like a clean repo."""
        code, out = run(os.path.join(self.dir, "nope"))
        self.assertEqual(code, 2)
        self.assertEqual(out["error"], "path not found")

    def test_empty_dir_is_valid_json_and_clean(self):
        code, out = run(self.dir)
        self.assertEqual(code, 0)
        self.assertEqual(out["files"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

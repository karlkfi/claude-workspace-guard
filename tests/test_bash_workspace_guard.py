"""Unit + end-to-end tests for scripts/bash-workspace-guard.py.

Run with: python3 -m unittest discover tests -v
Stdlib-only to match the hook itself.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "bash-workspace-guard.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("bash_workspace_guard", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load_module()


def fic(cmd):
    """Tokenize a simple command and run files_in_command on it."""
    import shlex
    return guard.files_in_command(shlex.split(cmd))


def run_hook(command, cwd, project_dir=None):
    """Invoke the hook script as a subprocess and return the parsed decision.

    Returns (decision, reason, raw_stdout). decision is None when the hook deferred.
    """
    payload = {"tool_input": {"command": command}, "cwd": str(cwd)}
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir if project_dir is not None else cwd)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    out = proc.stdout.strip()
    if not out:
        return None, None, out
    data = json.loads(out)
    h = data["hookSpecificOutput"]
    return h["permissionDecision"], h["permissionDecisionReason"], out


# -------------------------------------------------------------------- #
# files_in_command: SPEC table coverage
# -------------------------------------------------------------------- #

class GrepSpec(unittest.TestCase):
    def test_pattern_and_file(self):
        self.assertEqual(fic("grep foo data.txt"), ["data.txt"])

    def test_dash_e_suppresses_prog(self):
        # -e consumes its argument as the pattern value. The next positional
        # (data.txt) becomes a file because -e is in prog_suppressed_by.
        self.assertEqual(fic("grep -e foo data.txt"), ["data.txt"])

    def test_dash_f_is_file_flag(self):
        # -f supplies patterns -> prog drops to 0 -> data.txt is a file too.
        self.assertEqual(sorted(fic("grep -f patterns.txt data.txt")),
                         ["data.txt", "patterns.txt"])

    def test_long_file_inline_equals(self):
        # --file=patterns.txt suppresses prog (no pattern positional needed),
        # so both remaining positionals are treated as files.
        self.assertEqual(sorted(fic("grep --file=patterns.txt PAT data.txt")),
                         ["PAT", "data.txt", "patterns.txt"])

    def test_consume_max_count(self):
        # -m 5 consumes "5"; PAT then file.
        self.assertEqual(fic("grep -m 5 PAT data.txt"), ["data.txt"])

    def test_consume_include(self):
        # --include eats its glob arg; '.' is the file positional.
        self.assertEqual(fic("grep --include *.py -r PAT ."), ["."])

    def test_unknown_flag_assumes_zero_arg(self):
        self.assertEqual(fic("grep --xyz-unknown PAT data.txt"), ["data.txt"])

    def test_end_of_options(self):
        self.assertEqual(fic("grep -- PAT data.txt"), ["data.txt"])

    def test_stdin_dash_not_file_arg(self):
        # '-' becomes a positional. files_in_command returns it; the realpath
        # layer in main() is what filters '-' out. We only check it's preserved.
        self.assertEqual(fic("grep PAT -"), ["-"])


class SedSpec(unittest.TestCase):
    def test_program_and_file(self):
        self.assertEqual(fic("sed s/a/b/ notes.md"), ["notes.md"])

    def test_dash_e_suppresses_prog(self):
        self.assertEqual(fic("sed -e s/a/b/ notes.md"), ["notes.md"])

    def test_dash_f_is_file_flag(self):
        self.assertEqual(sorted(fic("sed -f script.sed notes.md")),
                         ["notes.md", "script.sed"])

    def test_expression_inline_suppresses_prog(self):
        self.assertEqual(fic("sed --expression=s/a/b/ notes.md"), ["notes.md"])


class AwkSpec(unittest.TestCase):
    def test_program_and_file(self):
        self.assertEqual(fic("awk {print} data.txt"), ["data.txt"])

    def test_dash_f_is_file_flag_suppresses_prog(self):
        self.assertEqual(sorted(fic("awk -f script.awk data.txt")),
                         ["data.txt", "script.awk"])

    def test_dash_v_consumes(self):
        self.assertEqual(fic("awk -v x=1 {print} data.txt"), ["data.txt"])

    def test_dash_F_consumes(self):
        self.assertEqual(fic("awk -F: {print} data.txt"), ["data.txt"])

    def test_skip_var_assignment_operands(self):
        # var=val operands after the program must not be treated as files.
        self.assertEqual(fic("awk {print} x=1 data.txt"), ["data.txt"])

    def test_assignment_with_slash_not_skipped(self):
        # './foo=bar' looks like a path, not an awk operand.
        self.assertEqual(fic("awk {print} ./foo=bar data.txt"),
                         ["./foo=bar", "data.txt"])


class JqSpec(unittest.TestCase):
    def test_program_with_slash_not_a_file(self):
        # '.a/.b' is a jq program, not a path. README highlights this case.
        self.assertEqual(fic("jq .a/.b data.json"), ["data.json"])

    def test_dash_f_suppresses_prog(self):
        self.assertEqual(sorted(fic("jq -f filter.jq data.json")),
                         ["data.json", "filter.jq"])

    def test_arg_consumes_two(self):
        # --arg consumes name + value; the program follows.
        self.assertEqual(fic("jq --arg name value .[$name] data.json"),
                         ["data.json"])

    def test_slurpfile_second_arg_is_file(self):
        # --slurpfile NAME FILE -> the file is the 2nd consumed token.
        self.assertEqual(sorted(fic("jq --slurpfile s data.json .x other.json")),
                         ["data.json", "other.json"])

    def test_rawfile_second_arg_is_file(self):
        self.assertEqual(sorted(fic("jq --rawfile r raw.txt .x data.json")),
                         ["data.json", "raw.txt"])

    def test_indent_inline_consumes(self):
        self.assertEqual(fic("jq --indent=2 .x data.json"), ["data.json"])


class CatHeadTailSpec(unittest.TestCase):
    def test_cat_simple(self):
        self.assertEqual(fic("cat a.txt b.txt"), ["a.txt", "b.txt"])

    def test_head_consume_n(self):
        self.assertEqual(fic("head -n 5 a.txt"), ["a.txt"])

    def test_head_consume_c(self):
        self.assertEqual(fic("head -c 100 a.txt"), ["a.txt"])

    def test_tail_inline_lines(self):
        self.assertEqual(fic("tail --lines=10 a.txt"), ["a.txt"])


class Aliases(unittest.TestCase):
    def test_egrep_aliases_to_grep(self):
        self.assertEqual(fic("egrep PAT data.txt"), ["data.txt"])

    def test_fgrep_aliases_to_grep(self):
        self.assertEqual(fic("fgrep PAT data.txt"), ["data.txt"])

    def test_rg_aliases_to_grep(self):
        # NOTE: rg has different flags; the alias is intentional per current SPEC.
        # Mis-parsing of rg-specific flags is tracked separately (Q3).
        self.assertEqual(fic("rg PAT data.txt"), ["data.txt"])

    def test_gawk_aliases_to_awk(self):
        self.assertEqual(fic("gawk {print} data.txt"), ["data.txt"])

    def test_mawk_aliases_to_awk(self):
        self.assertEqual(fic("mawk {print} data.txt"), ["data.txt"])

    def test_path_basename_aliases(self):
        # /usr/bin/egrep -> egrep -> grep
        self.assertEqual(fic("/usr/bin/egrep PAT data.txt"), ["data.txt"])


class Unguarded(unittest.TestCase):
    def test_ls_returns_none(self):
        self.assertIsNone(fic("ls /etc"))

    def test_find_returns_none(self):
        self.assertIsNone(fic("find . -name *.py"))


# -------------------------------------------------------------------- #
# split_eq helper
# -------------------------------------------------------------------- #

class SplitEq(unittest.TestCase):
    def test_long_with_value(self):
        self.assertEqual(guard.split_eq("--file=foo"), ("--file", "foo"))

    def test_long_without_value(self):
        self.assertEqual(guard.split_eq("--file"), ("--file", None))

    def test_short_with_equals_not_split(self):
        # Only --long=val is parsed. -x=y stays a single token.
        self.assertEqual(guard.split_eq("-x=y"), ("-x=y", None))

    def test_bare_positional(self):
        self.assertEqual(guard.split_eq("data.txt"), ("data.txt", None))


# -------------------------------------------------------------------- #
# End-to-end: main() over subprocess
# -------------------------------------------------------------------- #

class HookEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name).resolve()
        (self.workspace / "in.txt").write_text("hello\n")
        (self.workspace / "sub").mkdir()
        (self.workspace / "sub" / "nested.txt").write_text("nested\n")

    def tearDown(self):
        self._tmp.cleanup()

    # ---- allow ---- #

    def test_in_workspace_file_allows(self):
        d, r, _ = run_hook("grep hello in.txt", self.workspace)
        self.assertEqual(d, "allow")

    def test_pure_pipeline_allows(self):
        d, _, _ = run_hook("cat in.txt | grep hello", self.workspace)
        self.assertEqual(d, "allow")

    def test_nested_workspace_path_allows(self):
        d, _, _ = run_hook("cat sub/nested.txt", self.workspace)
        self.assertEqual(d, "allow")

    def test_redirect_to_workspace_allows(self):
        d, _, _ = run_hook("grep hello in.txt > out.txt", self.workspace)
        self.assertEqual(d, "allow")

    def test_stdin_dash_is_not_outside(self):
        d, _, _ = run_hook("grep PAT -", self.workspace)
        self.assertEqual(d, "allow")

    # ---- ask ---- #

    def test_absolute_outside_path_asks(self):
        d, reason, _ = run_hook("grep root /etc/passwd", self.workspace)
        self.assertEqual(d, "ask")
        self.assertIn("/etc/passwd", reason)

    def test_dotdot_traversal_asks(self):
        # ../<basename-of-tmp-parent>/... would still resolve under /var or /tmp;
        # use an unambiguous escape with realpath.
        d, reason, _ = run_hook("cat ../../../../etc/hosts", self.workspace)
        self.assertEqual(d, "ask")
        self.assertIn("etc/hosts", reason)

    def test_redirect_outside_asks(self):
        d, reason, _ = run_hook("grep hello in.txt > /tmp/out.txt", self.workspace)
        self.assertEqual(d, "ask")
        self.assertIn("/tmp/out.txt", reason)

    def test_jq_outside_file_asks(self):
        d, reason, _ = run_hook("jq .x /etc/hosts", self.workspace)
        self.assertEqual(d, "ask")
        self.assertIn("/etc/hosts", reason)

    def test_sed_outside_script_file_asks(self):
        d, reason, _ = run_hook("sed -f /tmp/evil.sed in.txt", self.workspace)
        self.assertEqual(d, "ask")
        self.assertIn("/tmp/evil.sed", reason)

    def test_mixed_pipeline_one_outside_asks(self):
        d, reason, _ = run_hook("cat in.txt | grep root /etc/passwd",
                                self.workspace)
        self.assertEqual(d, "ask")
        self.assertIn("/etc/passwd", reason)

    def test_symlink_pointing_outside_asks(self):
        target = "/etc/hosts"
        link = self.workspace / "link"
        os.symlink(target, link)
        d, reason, _ = run_hook("cat link", self.workspace)
        self.assertEqual(d, "ask")
        # realpath resolves the symlink to its target.
        self.assertIn("link", reason)

    # ---- defer ---- #

    def test_empty_command_defers(self):
        _, _, raw = run_hook("   ", self.workspace)
        self.assertEqual(raw, "")

    def test_unguarded_command_defers(self):
        _, _, raw = run_hook("ls /etc", self.workspace)
        self.assertEqual(raw, "")

    def test_unbalanced_quotes_defer(self):
        _, _, raw = run_hook("grep \"unterminated in.txt", self.workspace)
        self.assertEqual(raw, "")

    def test_no_input_command_field_defers(self):
        # tool_input.command missing -> empty cmd -> defer.
        payload = {"tool_input": {}, "cwd": str(self.workspace)}
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(self.workspace)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input=json.dumps(payload),
            capture_output=True, text=True, env=env, check=True,
        )
        self.assertEqual(proc.stdout.strip(), "")

    # ---- realpath / project-dir distinct from cwd ---- #

    def test_project_dir_overrides_cwd(self):
        # cwd is /tmp but CLAUDE_PROJECT_DIR is workspace; relative paths
        # resolve against cwd, so a relative in.txt under /tmp won't exist
        # and resolves outside workspace -> ask.
        with tempfile.TemporaryDirectory() as other:
            d, reason, _ = run_hook("cat in.txt", cwd=other,
                                    project_dir=self.workspace)
            self.assertEqual(d, "ask")


if __name__ == "__main__":
    unittest.main()

"""CLI tests: the two commands, the flags, exit codes and the What/Why/Fix reports."""

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from lacon.cli import DEMO_QUESTION, main

CONTEXT_FILE_TEXT = ("The bridge is painted every spring.\n"
                     "Paint keeps steel from rust.\n")


def run_cli(argv, stdin_text: str = ""):
    """Run main() over in-memory streams; returns (exit code, stdout, stderr)."""
    stdout, stderr = StringIO(), StringIO()
    code = main(argv, stdin=StringIO(stdin_text), stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def write_context(text: str) -> str:
    """A temporary context file on disk, cleaned up by the calling test."""
    handle = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    with handle:
        handle.write(text)
    return handle.name


class AskTests(unittest.TestCase):
    """`ask` answers from a file, from standard input, or from nothing."""

    def test_demo_answers_and_exits_zero(self) -> None:
        code, out, err = run_cli(["demo"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "paint keeps steel rust\n")

    def test_demo_prints_the_recursion_trace_before_the_answer(self) -> None:
        code, out, _ = run_cli(["demo", "--budget", "16", "--trace"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("[lacon] 12 of 16 letters, depth 2, 7 node(s)\n"))
        self.assertTrue(out.endswith("keeps rust\n"))

    def test_context_comes_from_a_file(self) -> None:
        path = write_context(CONTEXT_FILE_TEXT)
        self.addCleanup(Path(path).unlink)
        code, out, _ = run_cli(["ask", DEMO_QUESTION, "--context", path])
        self.assertEqual((code, out), (0, "paint keeps steel rust\n"))

    def test_context_comes_from_standard_input(self) -> None:
        code, out, _ = run_cli(["ask", DEMO_QUESTION, "--context", "-"], CONTEXT_FILE_TEXT)
        self.assertEqual((code, out), (0, "paint keeps steel rust\n"))

    def test_script_mode_prints_the_letters_only(self) -> None:
        code, out, _ = run_cli(["ask", DEMO_QUESTION, "--context", "-", "--budget", "8",
                                "--script"], CONTEXT_FILE_TEXT)
        self.assertEqual((code, out), (0, "!kps.rst\n"))
        self.assertLessEqual(len(out.strip()), 8)

    def test_json_mode_reports_the_whole_answer(self) -> None:
        code, out, _ = run_cli(["demo", "--json"])
        report = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(report["answer"], "paint keeps steel rust")
        self.assertEqual((report["budget"], report["depth"], report["nodes"], report["known"]),
                         (64, 0, 1, True))

    def test_an_unanswerable_question_exits_one_with_a_report(self) -> None:
        code, out, err = run_cli(["ask", "what colour is the moon?",
                                  "--context", "-"], CONTEXT_FILE_TEXT)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("no answer", err)
        self.assertIn("Why:", err)
        self.assertIn("Fix:", err)

    def test_json_reports_an_unanswerable_question_and_exits_one(self) -> None:
        code, out, _ = run_cli(["ask", "what colour is the moon?", "--json"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["known"])


class UsageTests(unittest.TestCase):
    """Usage misuse exits 2 with a Why and a Fix; help and version exit 0."""

    def test_help_prints_usage_and_exits_zero(self) -> None:
        code, out, err = run_cli(["--help"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("usage: lacon", out)

    def test_short_help_is_the_same(self) -> None:
        self.assertEqual(run_cli(["-h"])[0], 0)

    def test_version_prints_the_version_and_exits_zero(self) -> None:
        code, out, _ = run_cli(["--version"])
        self.assertEqual((code, out), (0, "lacon 0.1.0\n"))

    def test_no_command_is_a_usage_error(self) -> None:
        code, out, err = run_cli([])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no command given", err)

    def test_ask_without_a_question_is_a_usage_error(self) -> None:
        self.assertEqual(run_cli(["ask"])[0], 2)

    def test_an_unknown_command_is_refused(self) -> None:
        code, _, err = run_cli(["think"])
        self.assertEqual(code, 2)
        self.assertIn("unknown command 'think'", err)

    def test_an_unknown_option_is_refused(self) -> None:
        code, _, err = run_cli(["demo", "--loud"])
        self.assertEqual(code, 2)
        self.assertIn("unknown option '--loud'", err)

    def test_a_flag_without_its_value_is_refused(self) -> None:
        code, _, err = run_cli(["demo", "--budget"])
        self.assertEqual(code, 2)
        self.assertIn("needs a value", err)

    def test_a_budget_that_is_not_a_number_is_refused(self) -> None:
        code, _, err = run_cli(["demo", "--budget", "many"])
        self.assertEqual(code, 2)
        self.assertIn("is not a number", err)

    def test_a_budget_below_one_is_refused(self) -> None:
        code, _, err = run_cli(["demo", "--budget", "0"])
        self.assertEqual(code, 2)
        self.assertIn("no room for a thought", err)

    def test_a_missing_context_file_is_a_usage_error(self) -> None:
        code, _, err = run_cli(["ask", DEMO_QUESTION, "--context", "no-such-file.txt"])
        self.assertEqual(code, 2)
        self.assertIn("cannot read context", err)


if __name__ == "__main__":
    unittest.main()
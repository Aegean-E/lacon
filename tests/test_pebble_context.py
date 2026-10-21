"""Pebble context tests: Pebble's parser becomes evidence for the Lacon engine."""

import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from lacon import Lacon, PebbleContextError
from lacon.cli import main
from lacon.pebble_context import pebble_to_sentences
from lacon.rlm import parse_context

SOURCE = """# Fibonacci by recursion.
fn fib(n) {
  if n < 2 { return n }
  return fib(n - 1) + fib(n - 2)
}

let answer = fib(10)
"""


def run_cli(argv, stdin_text: str = ""):
    """Run main() over in-memory streams; returns (exit code, stdout, stderr)."""
    stdout, stderr = StringIO(), StringIO()
    code = main(argv, stdin=StringIO(stdin_text), stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def write_source(text: str, suffix: str = ".peb") -> str:
    """A temporary Pebble file on disk, cleaned up by the calling test."""
    handle = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    with handle:
        handle.write(text)
    return handle.name


class ConversionTests(unittest.TestCase):
    """Declarations and comments survive the trip through Pebble's AST."""

    def test_functions_variables_and_comments_become_sentences(self) -> None:
        sentences = pebble_to_sentences(SOURCE)
        self.assertTrue(any("function fib" in sentence for sentence in sentences))
        self.assertTrue(any("variable answer" in sentence for sentence in sentences))
        self.assertTrue(any("recursion" in sentence for sentence in sentences))

    def test_parse_context_uses_the_same_reader(self) -> None:
        self.assertEqual(parse_context(SOURCE, "pebble"), pebble_to_sentences(SOURCE))

    def test_an_unknown_format_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            parse_context(SOURCE, "yaml")

    def test_a_broken_program_carries_a_why_and_a_fix(self) -> None:
        with self.assertRaises(PebbleContextError) as caught:
            pebble_to_sentences("fn {")
        self.assertIn("expected a function name", caught.exception.message)
        self.assertTrue(caught.exception.why)
        self.assertTrue(caught.exception.fix)

    def test_a_missing_checkout_is_reported_as_a_why_and_a_fix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch("lacon.pebble_context._import_pebble", side_effect=ImportError):
                with self.assertRaises(PebbleContextError) as caught:
                    pebble_to_sentences(SOURCE, root=directory)
        self.assertIn("could not be imported", caught.exception.message)
        self.assertTrue(caught.exception.why)
        self.assertTrue(caught.exception.fix)


class AskTests(unittest.TestCase):
    """Lacon answers from Pebble source through the public API."""

    def test_a_function_question_is_answered(self) -> None:
        answer = Lacon().ask("what does fib do?", SOURCE, 64, context_format="pebble")
        self.assertTrue(answer.known)
        self.assertIn("fib", answer.answer)

    def test_a_comment_question_is_answered_from_the_comment(self) -> None:
        answer = Lacon().ask("what is computed by recursion?", SOURCE, 64,
                             context_format="pebble")
        self.assertTrue(answer.known)
        self.assertIn("recursion", answer.answer)


class CliTests(unittest.TestCase):
    """The command line infers Pebble from `.peb` and reports bad contexts."""

    def test_a_peb_file_extension_selects_the_pebble_reader(self) -> None:
        path = write_source(SOURCE)
        self.addCleanup(Path(path).unlink)
        code, out, err = run_cli(["ask", "what does fib do?", "--context", path])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("fib", out)

    def test_the_format_can_be_forced_for_standard_input(self) -> None:
        code, out, _ = run_cli(["ask", "what does fib do?", "--context", "-",
                                "--context-format", "pebble"], SOURCE)
        self.assertEqual(code, 0)
        self.assertIn("fib", out)

    def test_a_broken_pebble_context_exits_two_with_a_report(self) -> None:
        path = write_source("fn {")
        self.addCleanup(Path(path).unlink)
        code, out, err = run_cli(["ask", "what does fib do?", "--context", path])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("error:", err)
        self.assertIn("Why:", err)
        self.assertIn("Fix:", err)

    def test_an_unknown_context_format_is_a_usage_error(self) -> None:
        code, out, err = run_cli(["ask", "what does fib do?", "--context-format", "yaml"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("not a reader", err)

    def test_demo_rejects_a_context_format(self) -> None:
        code, out, err = run_cli(["demo", "--context-format", "pebble"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("applies to 'ask'", err)


if __name__ == "__main__":
    unittest.main()

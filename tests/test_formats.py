"""Format parser tests: CSV and JSON contexts become sentences the engine can read."""

import unittest

from lacon import Lacon
from lacon.rlm import parse_context, parse_csv, parse_json, sentences

CSV_TEXT = ("name,age,city\n"
            "Alice,30,New York\n"
            "Bob,25,Los Angeles\n"
            "Charlie,35,Chicago")

JSON_TEXT = ('{"users": [{"name": "Alice", "age": 30}, '
             '{"name": "Bob", "age": 25}]}')


class ParserTests(unittest.TestCase):
    """Each format keeps the values a question can match."""

    def test_csv_rows_become_sentences(self) -> None:
        self.assertEqual(parse_csv(CSV_TEXT),
                         ["name age city", "Alice 30 New York",
                          "Bob 25 Los Angeles", "Charlie 35 Chicago"])

    def test_json_keeps_keys_and_numbers(self) -> None:
        self.assertEqual(parse_json(JSON_TEXT),
                         ["users name Alice age 30", "users name Bob age 25"])

    def test_invalid_json_is_empty(self) -> None:
        self.assertEqual(parse_json("{not json"), [])

    def test_auto_detects_json_csv_and_text(self) -> None:
        self.assertEqual(parse_context(JSON_TEXT, "auto"),
                         parse_json(JSON_TEXT))
        self.assertEqual(parse_context(CSV_TEXT, "auto"),
                         parse_csv(CSV_TEXT))
        self.assertEqual(parse_context("A. B!", "auto"), sentences("A. B!"))

    def test_an_explicit_format_bypasses_detection(self) -> None:
        self.assertEqual(parse_context(JSON_TEXT, "text"), sentences(JSON_TEXT))


class FormatAskTests(unittest.TestCase):
    """Lacon.ask uses the parsers by default and exposes the format override."""

    def test_a_csv_context_answers_the_question(self) -> None:
        answer = Lacon().ask("How old is Alice?", CSV_TEXT, 64, max_total_chars=100)
        self.assertEqual(answer.answer, "alice 30 new york")
        self.assertTrue(answer.known)

    def test_a_json_context_answers_the_question(self) -> None:
        answer = Lacon().ask("How old is Alice?", JSON_TEXT, 64, max_total_chars=100)
        self.assertEqual(answer.answer, "users name alice age 30")
        self.assertTrue(answer.known)

    def test_text_format_reads_json_literally(self) -> None:
        answer = Lacon().ask("How old is Alice?", JSON_TEXT, 64,
                             max_total_chars=100, context_format="text")
        self.assertIn("bob", answer.answer)
        self.assertTrue(answer.known)


class TreeBudgetTests(unittest.TestCase):
    """A tree-wide budget stops expansion instead of visiting every node."""

    def test_a_tree_budget_reduces_the_visited_nodes(self) -> None:
        context = " ".join(f"Sentence {i} about bridges." for i in range(100))

        unlimited = Lacon().ask("What about bridges?", context, 64)
        limited = Lacon().ask("What about bridges?", context, 64,
                              max_total_chars=50)

        self.assertTrue(limited.known)
        self.assertGreater(limited.tree_chars, 0)
        self.assertLess(limited.tree_nodes, unlimited.tree_nodes)
        self.assertLess(limited.tree_chars, unlimited.tree_chars)

    def test_the_tree_budget_is_a_hard_cap_at_every_ceiling(self) -> None:
        context = " ".join(f"Sentence {i} about bridges." for i in range(100))

        for limit in (0, 1, 8, 17, 24, 50, 100, 200):
            with self.subTest(limit=limit):
                answer = Lacon().ask("What about bridges?", context, 64,
                                     max_total_chars=limit)
                self.assertLessEqual(answer.tree_chars, limit)

    def test_a_generous_cap_matches_the_unlimited_tree(self) -> None:
        context = " ".join(f"Sentence {i} about bridges." for i in range(100))

        unlimited = Lacon().ask("What about bridges?", context, 64)
        generous = Lacon().ask("What about bridges?", context, 64,
                               max_total_chars=1000)

        self.assertEqual(generous.script, unlimited.script)
        self.assertEqual(generous.tree_chars, unlimited.tree_chars)

    def test_a_negative_tree_budget_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            Lacon(max_total_chars=-1)
        with self.assertRaises(ValueError):
            Lacon().ask("What about bridges?", "Bridges.", 64, max_total_chars=-1)


if __name__ == "__main__":
    unittest.main()

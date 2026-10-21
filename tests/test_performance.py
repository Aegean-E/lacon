"""Behaviour and edge-case tests; wall-clock benchmarks live in benchmarks/performance.py."""

import random
import unittest

from lacon.alphabet import content_words, expand, lexicon, skeleton
from lacon.budget import Budget
from lacon.rlm import Lacon
from lacon.thought import Thought, answer_text, parse, render


class CodeUnderstandingTests(unittest.TestCase):
    """Python code contexts are extracted by the AST reader and answered."""

    def setUp(self):
        self.l = Lacon()
        self.code_ctx = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
'''

    def test_code_context_parsed(self) -> None:
        """Code context is parsed with AST and answers code questions."""
        answer = self.l.ask("What does fibonacci do?", self.code_ctx, 64)
        self.assertTrue(answer.known)
        self.assertIn("fibonacci", answer.answer.lower())

    def test_snake_case_in_question(self) -> None:
        """snake_case identifiers in the question are matched from code."""
        ctx = "def calculate_total_price(items): return sum(items)"
        answer = self.l.ask("What does calculate_total_price do?", ctx, 64)
        self.assertTrue(answer.known)
        self.assertIn("calculate", answer.answer.lower())


class EdgeCaseTests(unittest.TestCase):
    """Edge cases and stress tests."""

    def test_very_long_context(self) -> None:
        """Context with 1000 sentences handled within depth cap."""
        l = Lacon()
        ctx = " ".join([f"Sentence {i} about a topic." for i in range(1000)])
        answer = l.ask("What is the topic?", ctx, 64)
        self.assertLessEqual(answer.depth, 4)
        self.assertTrue(Budget(64).fits(answer.script))

    def test_many_questions_same_context(self) -> None:
        """Many different questions on same context reuse cache."""
        l = Lacon()
        ctx = " ".join([f"Sentence {i} with content." for i in range(200)])
        questions = [f"What is sentence {i}?" for i in range(50)]
        for q in questions:
            answer = l.ask(q, ctx, 64)
            self.assertTrue(Budget(64).fits(answer.script))

    def test_unicode_content(self) -> None:
        """Unicode content handled gracefully."""
        l = Lacon()
        ctx = "Café résumé naïve piñata 中文 日本語"
        answer = l.ask("What languages are here?", ctx, 64)
        self.assertTrue(Budget(64).fits(answer.script))

    def test_empty_and_whitespace(self) -> None:
        """Empty and whitespace-only contexts handled."""
        l = Lacon()
        for ctx in ["", "   ", "\n\n\n", "\t\t"]:
            answer = l.ask("Question?", ctx, 64)
            self.assertEqual(answer.script, "?")
            self.assertFalse(answer.known)

    def test_budget_zero_refused(self) -> None:
        """Budget of zero is refused at ask time."""
        l = Lacon()
        with self.assertRaises(ValueError):
            l.ask("Question?", "Context.", 0)

    def test_negative_budget_refused(self) -> None:
        """Negative budget is refused."""
        l = Lacon()
        with self.assertRaises(ValueError):
            l.ask("Question?", "Context.", -1)

    def test_script_round_trip_many(self) -> None:
        """Many random scripts parse and render correctly."""
        glyphs = ["?", "+", "-", "<", ">", "*", "=", "!"]
        for _ in range(1000):
            thoughts = [Thought(random.choice(glyphs), "abc.def",
                                random.randint(1, 5) if random.random() > 0.5 else None)
                        for _ in range(random.randint(1, 10))]
            script = render(thoughts)
            parsed = parse(script)
            self.assertEqual(render(parsed), script)

    def test_answer_text_consistency(self) -> None:
        """answer_text returns consistent results."""
        thoughts = [Thought("<", "abc.def", 1), Thought(">", ""), Thought("!", "ghi.jkl")]
        words = lexicon("abc def ghi jkl")
        self.assertEqual(answer_text(thoughts, words), answer_text(thoughts, words))

    def test_expand_unknown_returns_original(self) -> None:
        """expand returns the skeleton when word unknown."""
        self.assertEqual(expand("unknown.word", {}), "unknown word")

    def test_skeleton_preserves_digits(self) -> None:
        """skeleton preserves digits (digits kept adjacent to letters)."""
        self.assertEqual(skeleton("version2.0.1"), "vrsn2.0.1")

    def test_content_words_filters_stopwords(self) -> None:
        """content_words filters common stopwords."""
        words = content_words("the quick brown fox jumps over the lazy dog")
        self.assertNotIn("th", words)  # "the" -> "th" filtered
        self.assertIn("qck", words)    # "quick" -> "qck" kept
        self.assertIn("brwn", words)   # "brown" -> "brwn" kept

    def test_lexicon_picks_shortest(self) -> None:
        """lexicon picks shortest spelling for same skeleton."""
        words = lexicon("rust rusty rusting")
        self.assertEqual(words["rst"], "rust")


if __name__ == "__main__":
    unittest.main()

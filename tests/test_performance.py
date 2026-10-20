"""Performance benchmark tests: ensure speed budgets are met and measure regressions."""

import time
import unittest

from lacon.budget import Budget
from lacon.rlm import Lacon, partition, sentences
from lacon.alphabet import skeleton, lexicon, content_words, expand
from lacon.thinker import Thinker
from lacon.thought import Thought, render, parse, answer_text


class PerformanceTests(unittest.TestCase):
    """Speed budgets: every operation must complete within its budget."""

    def test_ask_cold_speed(self) -> None:
        """A single ask on 200 sentences completes within 100ms cold."""
        l = Lacon()
        l._lexicon_cache.clear()
        l._evidence_cache.clear()
        ctx = " ".join([f"Sentence {i} with some content words here." for i in range(200)])
        start = time.perf_counter()
        l.ask("What is sentence 100?", ctx, 64)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.1, f"Cold ask took {elapsed*1000:.1f}ms, budget 100ms")

    def test_ask_warm_speed(self) -> None:
        """A repeated ask on same context completes within 5ms warm."""
        l = Lacon()
        ctx = " ".join([f"Sentence {i} with some content words here." for i in range(200)])
        l.ask("What is sentence 100?", ctx, 64)  # warm up
        start = time.perf_counter()
        l.ask("What is sentence 100?", ctx, 64)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.005, f"Warm ask took {elapsed*1000:.1f}ms, budget 5ms")

    def test_alphabet_skeleton_speed(self) -> None:
        """skeleton on 1000 words completes within 200ms."""
        words = " ".join([f"word{i}" for i in range(1000)])
        start = time.perf_counter()
        for _ in range(100):
            skeleton(words)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.2, f"skeleton took {elapsed*1000:.1f}ms, budget 200ms")

    def test_lexicon_speed(self) -> None:
        """lexicon on 1000 words completes within 100ms."""
        words = " ".join([f"word{i}" for i in range(1000)])
        start = time.perf_counter()
        for _ in range(100):
            lexicon(words)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.1, f"lexicon took {elapsed*1000:.1f}ms, budget 100ms")

    def test_thinker_rank_speed(self) -> None:
        """Thinker.rank on 500 sentences completes within 500ms."""
        t = Thinker()
        question = "What is the answer?"
        evidence = [f"Sentence {i} with some relevant content." for i in range(500)]
        start = time.perf_counter()
        for _ in range(50):
            t.rank(question, evidence)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.5, f"rank took {elapsed*1000:.1f}ms, budget 500ms")

    def test_partition_speed(self) -> None:
        """partition on 10000 items completes within 10ms."""
        items = list(range(10000))
        start = time.perf_counter()
        for _ in range(100):
            partition(items, 2)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.01, f"partition took {elapsed*1000:.1f}ms, budget 10ms")

    def test_full_pipeline_100_asks(self) -> None:
        """100 asks on 100-sentence context completes within 2s."""
        l = Lacon()
        ctx = " ".join([f"Sentence {i} about bridges and rust." for i in range(100)])
        start = time.perf_counter()
        for i in range(100):
            l.ask(f"What about sentence {i}?", ctx, 64)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0, f"100 asks took {elapsed*1000:.1f}ms, budget 2000ms")


class CodeUnderstandingTests(unittest.TestCase):
    """Tests for code understanding: functions, classes, identifiers.
    
    Note: Current engine is designed for natural language sentences.
    Code understanding requires preprocessing (function/class extraction)
    which is a future improvement. These tests document expected behavior.
    """

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
        """Code context is split into sentences (current behavior)."""
        answer = self.l.ask("What does fibonacci do?", self.code_ctx, 64)
        # Currently returns unknown because code doesn't split well into sentences
        # This documents current limitation
        self.assertEqual(answer.script, "?")

    def test_snake_case_in_question(self) -> None:
        """snake_case identifiers in question produce some output."""
        ctx = "def calculate_total_price(items): return sum(items)"
        answer = self.l.ask("What does calculate_total_price do?", ctx, 64)
        # Engine processes snake_case as content words
        self.assertTrue(len(answer.script) > 1)


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
        from lacon.thought import parse, render, Thought
        import random
        glyphs = ["?", "+", "-", "<", ">", "*", "=", "!"]
        for _ in range(1000):
            thoughts = [Thought(random.choice(glyphs), "abc.def", random.randint(1, 5) if random.random() > 0.5 else None)
                        for _ in range(random.randint(1, 10))]
            script = render(thoughts)
            parsed = parse(script)
            self.assertEqual(render(parsed), script)

    def test_answer_text_consistency(self) -> None:
        """answer_text returns consistent results."""
        from lacon.thought import answer_text, Thought
        from lacon.alphabet import lexicon
        thoughts = [Thought("<", "abc.def", 1), Thought(">", ""), Thought("!", "ghi.jkl")]
        words = lexicon("abc def ghi jkl")
        ans1 = answer_text(thoughts, words)
        ans2 = answer_text(thoughts, words)
        self.assertEqual(ans1, ans2)

    def test_expand_unknown_returns_original(self) -> None:
        """expand returns the skeleton when word unknown."""
        self.assertEqual(expand("unknown.word", {}), "unknown word")

    def test_skeleton_preserves_digits(self) -> None:
        """skeleton preserves digits (digits kept adjacent to letters)."""
        # version2.0.1 -> version2, 0, 1 -> vrsn2, 0, 1 -> vrsn2.0.1
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
"""Wall-clock benchmarks, run explicitly with `python -m unittest benchmarks.performance`.

These are regression guides, not part of `unittest discover`: a loaded CI host
can inflate any one sample, so the default gate stays deterministic.
"""

import time
import unittest

from lacon.alphabet import skeleton, lexicon
from lacon.rlm import Lacon, partition
from lacon.thinker import Thinker


class PerformanceTests(unittest.TestCase):
    """Speed budgets: every operation must complete within its budget."""

    def test_ask_cold_speed(self) -> None:
        """A single ask on 200 sentences completes within 100ms cold."""
        l = Lacon()
        l._lexicon_cache.clear()
        l._payload_cache.clear()
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
        """Thinker.rank on 500 sentences completes within 600ms."""
        t = Thinker()
        question = "What is the answer?"
        evidence = [f"Sentence {i} with some relevant content." for i in range(500)]
        start = time.perf_counter()
        for _ in range(50):
            t.rank(question, evidence)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.6, f"rank took {elapsed*1000:.1f}ms, budget 600ms")

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


if __name__ == "__main__":
    unittest.main()

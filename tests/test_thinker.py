"""Thinker tests: ranking by shared meaning, and the cheapest thought that still answers."""

import unittest

from lacon.budget import Budget
from lacon.thinker import Thinker
from lacon.thought import Thought, render

QUESTION = "What keeps the bridge from rust?"
EVIDENCE = ["The bridge is painted every spring.",
            "Paint keeps steel from rust.",
            "Rust is iron oxide."]


class RankTests(unittest.TestCase):
    """The sentence that shares the most meaning with the question comes first."""

    def test_the_best_match_is_ranked_first(self) -> None:
        ranked = Thinker().rank(QUESTION, EVIDENCE)
        self.assertEqual(ranked[0].sentence, "Paint keeps steel from rust.")
        self.assertEqual(ranked[0].payload, "pnt.kps.stl.rst")
        self.assertEqual(ranked[0].score, 2)

    def test_an_unrelated_sentence_scores_nothing(self) -> None:
        self.assertEqual(Thinker().rank("colour of the moon", EVIDENCE)[0].score, 0)

    def test_overlap_counts_meaning_carrying_words_only(self) -> None:
        self.assertEqual(Thinker().overlap("rust", "rust is iron oxide"), 1)

    def test_a_shorter_context_scores_the_same_sentence(self) -> None:
        ranked = Thinker().rank(QUESTION, EVIDENCE[:2])
        self.assertEqual(ranked[0].index, 1)


class ThinkTests(unittest.TestCase):
    """The thought is as small as the budget allows, and never larger than it."""

    def test_a_generous_budget_keeps_the_evidence_and_the_step(self) -> None:
        self.assertEqual(Thinker().think(QUESTION, EVIDENCE, Budget(64)),
                         [Thought("<", "pnt.kps.stl.rst", 1), Thought(">"),
                          Thought("!", "pnt.kps.stl.rst")])

    def test_a_tight_budget_drops_the_support_first(self) -> None:
        self.assertEqual(Thinker().think(QUESTION, EVIDENCE, Budget(16)),
                         [Thought("!", "pnt.kps.stl.rst")])

    def test_a_tighter_budget_shortens_the_answer(self) -> None:
        self.assertEqual(Thinker().think(QUESTION, EVIDENCE, Budget(8)),
                         [Thought("!", "pnt.kps")])

    def test_a_budget_that_cannot_hold_a_word_is_unknown(self) -> None:
        self.assertEqual(Thinker().think(QUESTION, EVIDENCE, Budget(3)), [Thought("?")])

    def test_evidence_that_matches_nothing_is_unknown(self) -> None:
        self.assertEqual(Thinker().think("colour of the moon", EVIDENCE, Budget(64)),
                         [Thought("?")])

    def test_no_evidence_is_unknown(self) -> None:
        self.assertEqual(Thinker().think(QUESTION, [], Budget(64)), [Thought("?")])

    def test_every_budget_holds_the_thought_it_produced(self) -> None:
        for limit in (1, 2, 3, 4, 5, 8, 16, 32, 64):
            with self.subTest(limit=limit):
                thought_list = Thinker().think(QUESTION, EVIDENCE, Budget(limit))
                self.assertTrue(Budget(limit).fits(render(thought_list)))


if __name__ == "__main__":
    unittest.main()
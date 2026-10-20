"""RLM tests: the recursive engine - what it answers, when it splits, and what it never exceeds."""

import unittest

from lacon.budget import Budget
from lacon.rlm import MAX_DEPTH, Answer, Lacon, partition, sentences
from lacon.thought import parse, render

QUESTION = "What keeps the bridge from rust?"
CONTEXT = ("The bridge is painted every spring.\n"
           "Paint keeps steel from rust.\n"
           "Rust is iron oxide.\n"
           "The painter uses a long brush.\n"
           "Salt air speeds rust on the coast.\n"
           "The bridge spans the river in three arches.\n")


class SentenceTests(unittest.TestCase):
    """A context is a list of sentences, one per line or sentence mark."""

    def test_lines_and_marks_both_end_a_sentence(self) -> None:
        self.assertEqual(sentences("A. B!\nC?"), ["A", "B", "C"])

    def test_an_empty_context_holds_nothing(self) -> None:
        self.assertEqual(sentences(""), [])


class PartitionTests(unittest.TestCase):
    """Splitting is contiguous, even, and never produces an empty chunk."""

    def test_even_lengths_split_evenly(self) -> None:
        self.assertEqual(partition(list("abcdef"), 2), [["a", "b", "c"], ["d", "e", "f"]])

    def test_an_odd_length_gives_the_extra_to_the_first_chunks(self) -> None:
        self.assertEqual(partition(["a", "b", "c"], 2), [["a", "b"], ["c"]])

    def test_more_parts_than_items_keeps_one_chunk_per_item(self) -> None:
        self.assertEqual(partition(["a", "b"], 5), [["a"], ["b"]])

    def test_nothing_splits_into_nothing(self) -> None:
        self.assertEqual(partition([], 2), [])


class AskTests(unittest.TestCase):
    """One question is answered from the context, and the letters never exceed the budget."""

    def test_a_short_context_is_answered_in_one_thought(self) -> None:
        answer = Lacon().ask(QUESTION, CONTEXT)
        self.assertEqual(answer.answer, "paint keeps steel rust")
        self.assertEqual(answer.script, "<pnt.kps.stl.rst^1 > !pnt.kps.stl.rst")
        self.assertEqual((answer.depth, answer.nodes, answer.budget), (0, 1, 64))
        self.assertTrue(answer.known)

    def test_a_long_context_is_split_and_merged(self) -> None:
        answer = Lacon().ask(QUESTION, CONTEXT, budget=16)
        self.assertEqual(answer.answer, "paint keeps")
        self.assertEqual(answer.script, "=01 !pnt.kps")
        self.assertEqual((answer.depth, answer.nodes), (2, 7))

    def test_the_thought_obeys_every_budget(self) -> None:
        for limit in (1, 2, 4, 8, 16, 32, 64):
            with self.subTest(limit=limit):
                answer = Lacon().ask(QUESTION, CONTEXT, budget=limit)
                self.assertTrue(Budget(limit).fits(answer.script))
                self.assertEqual(answer.budget, limit)

    def test_a_budget_of_one_letter_can_only_be_unknown(self) -> None:
        answer = Lacon().ask(QUESTION, CONTEXT, budget=1)
        self.assertEqual(answer.script, "?")
        self.assertFalse(answer.known)

    def test_a_context_that_answers_nothing_is_unknown(self) -> None:
        answer = Lacon().ask("What colour is the moon?", CONTEXT)
        self.assertEqual(answer.script, "?")
        self.assertEqual(answer.answer, "")
        self.assertFalse(answer.known)

    def test_no_context_is_unknown(self) -> None:
        answer = Lacon().ask(QUESTION, "")
        self.assertEqual((answer.answer, answer.script, answer.depth, answer.nodes),
                         ("", "?", 0, 1))

    def test_recursion_stops_at_the_depth_cap(self) -> None:
        long_context = " ".join(CONTEXT for _ in range(7))
        answer = Lacon().ask(QUESTION, long_context, budget=8)
        self.assertLessEqual(answer.depth, MAX_DEPTH)
        self.assertTrue(Budget(8).fits(answer.script))

    def test_the_script_is_a_lacon_script(self) -> None:
        answer = Lacon().ask(QUESTION, CONTEXT, budget=32)
        self.assertEqual(render(parse(answer.script)), answer.script)


class AnswerTests(unittest.TestCase):
    """An answer knows whether it found evidence, and nothing else."""

    def test_an_answered_script_is_known(self) -> None:
        self.assertTrue(Answer("rust", "!rst", 0, 1, 64).known)

    def test_an_empty_answer_is_not_known(self) -> None:
        self.assertFalse(Answer("", "?", 0, 1, 64).known)


if __name__ == "__main__":
    unittest.main()
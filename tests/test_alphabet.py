"""Alphabet tests: the vowelless letter form, the meaning-carrying words and the expansion back."""

import unittest

from lacon.alphabet import content_words, expand, lexicon, skeleton


class SkeletonTests(unittest.TestCase):
    """`skeleton` is the letter form: lowercase, vowelless, punctuation gone."""

    def test_vowels_and_punctuation_are_removed(self) -> None:
        self.assertEqual(skeleton("The Bridge! is 42."), "th.brdg.s.42")

    def test_a_word_of_vowels_only_disappears(self) -> None:
        self.assertEqual(skeleton("a i o"), "")

    def test_digits_survive_as_themselves(self) -> None:
        self.assertEqual(skeleton("2017"), "2017")


class ContentWordTests(unittest.TestCase):
    """`content_words` keeps what carries meaning and drops the words a reader can supply."""

    def test_common_words_are_dropped(self) -> None:
        self.assertEqual(content_words("The bridge keeps the steel from rust"),
                         ["brdg", "kps", "stl", "rst"])

    def test_a_question_drops_its_question_words(self) -> None:
        self.assertEqual(content_words("What keeps the bridge from rust?"),
                         ["kps", "brdg", "rst"])

    def test_no_word_yields_no_content(self) -> None:
        self.assertEqual(content_words(""), [])


class LexiconTests(unittest.TestCase):
    """The vocabulary is built from the texts, and expansion reads a payload back through it."""

    def test_expansion_restores_the_written_words(self) -> None:
        words = lexicon("Paint keeps steel from rust.")
        self.assertEqual(expand("pnt.kps.stl.frm.rst", words), "paint keeps steel from rust")

    def test_the_shortest_spelling_wins(self) -> None:
        self.assertEqual(lexicon("rust rusty")["rst"], "rust")

    def test_an_unknown_letter_form_is_shown_as_it_is(self) -> None:
        self.assertEqual(expand("zzz.qq", {}), "zzz qq")

    def test_a_word_of_vowels_only_is_not_a_vocabulary_entry(self) -> None:
        self.assertEqual(lexicon("a e i"), {})


if __name__ == "__main__":
    unittest.main()
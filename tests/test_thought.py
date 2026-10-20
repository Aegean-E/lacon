"""Thought tests: the eight glyphs, the one-token script form, and reading a script back."""

import unittest

from lacon.alphabet import lexicon
from lacon.thought import (GLYPHS, Thought, ThoughtError, answer_text, parse, render)


class GlyphTests(unittest.TestCase):
    """The alphabet is exactly eight glyphs, and each one is a single act of reasoning."""

    def test_there_are_eight_glyphs(self) -> None:
        self.assertEqual(len(GLYPHS), 8)
        self.assertEqual(set(GLYPHS.values()),
                         {"unknown", "claim", "contrast", "because", "therefore", "split",
                          "merge", "answer"})

    def test_a_thought_costs_one_glyph(self) -> None:
        rendered = render([Thought("<", "pnt.kps", 1), Thought(">"), Thought("!", "pnt.kps")])
        self.assertEqual(rendered, "<pnt.kps^1 > !pnt.kps")
        self.assertEqual(len(rendered.split()), 3)


class RenderTests(unittest.TestCase):
    """Rendering is the inverse of parsing, and refuses a glyph outside the alphabet."""

    def test_render_and_parse_round_trip(self) -> None:
        thoughts = [Thought("<", "pnt.kps", 1), Thought(">"), Thought("!", "pnt.kps")]
        self.assertEqual(parse(render(thoughts)), thoughts)

    def test_an_unknown_glyph_is_refused_when_rendered(self) -> None:
        with self.assertRaises(ThoughtError):
            Thought("&", "x").render()

    def test_an_unknown_glyph_is_refused_when_parsed(self) -> None:
        with self.assertRaises(ThoughtError):
            parse("&x")

    def test_a_reference_that_is_not_a_number_is_refused(self) -> None:
        with self.assertRaises(ThoughtError):
            parse("!rust^two")


class AnswerTests(unittest.TestCase):
    """The answer is the last answer glyph, read back through the vocabulary."""

    def test_the_answer_is_expanded_through_the_lexicon(self) -> None:
        words = lexicon("Paint keeps steel from rust.")
        self.assertEqual(answer_text([Thought("<", "pnt.kps", 1), Thought("!", "pnt.kps")], words),
                         "paint keeps")

    def test_an_unknown_thought_speaks_nothing(self) -> None:
        self.assertEqual(answer_text([Thought("?")], {}), "")


if __name__ == "__main__":
    unittest.main()
"""Budget tests: the letter ceiling, its refusal of an impossible ceiling, and the child budget."""

import unittest

from lacon.budget import MIN_CHILD, Budget


class BudgetTests(unittest.TestCase):
    """A budget is a ceiling in letters and the depth it belongs to."""

    def test_a_script_at_the_ceiling_fits(self) -> None:
        self.assertTrue(Budget(4).fits("!abc"))

    def test_one_letter_over_the_ceiling_does_not_fit(self) -> None:
        self.assertFalse(Budget(3).fits("!abc"))

    def test_room_is_what_one_glyph_leaves(self) -> None:
        self.assertEqual(Budget(4).room("!"), 3)
        self.assertEqual(Budget(4).room("<"), 3)

    def test_a_child_gets_half_the_ceiling_at_the_next_depth(self) -> None:
        self.assertEqual(Budget(64).child(), Budget(32, 1))
        self.assertEqual(Budget(16).child(), Budget(8, 1))

    def test_a_child_never_falls_below_the_floor(self) -> None:
        self.assertEqual(Budget(2).child(), Budget(MIN_CHILD, 1))
        self.assertEqual(Budget(1).child(), Budget(MIN_CHILD, 1))

    def test_a_ceiling_below_one_letter_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            Budget(0)
        with self.assertRaises(ValueError):
            Budget(-2)


if __name__ == "__main__":
    unittest.main()
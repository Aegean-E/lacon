"""The letter budget: the hard ceiling on how many characters one thought may cost.

A budget shrinks with every recursive step, which is what forces a long context into small, cheap
thoughts. `fits` is the gate every thought passes before it is kept, `child` is the budget a
recursive step receives - at least `MIN_CHILD` letters, so even the deepest thought can still name
a word - and `room` is what one glyph leaves for its payload.
"""

from dataclasses import dataclass

MIN_CHILD = 8


@dataclass(frozen=True)
class Budget:
    """A ceiling in characters and the recursion depth it belongs to."""

    limit: int
    depth: int = 0

    def __post_init__(self) -> None:
        """Refuse a ceiling that could not hold even the one-letter unknown glyph."""
        if self.limit < 1:
            raise ValueError("a Lacon budget is at least one character")

    def fits(self, script: str) -> bool:
        """Whether a rendered script costs no more than the ceiling."""
        return len(script) <= self.limit

    def room(self, glyph: str) -> int:
        """How many payload characters remain after a glyph of this cost."""
        return self.limit - len(glyph)

    def child(self) -> "Budget":
        """The budget of a recursive step: half this ceiling, but never below `MIN_CHILD`."""
        return Budget(max(MIN_CHILD, self.limit // 2), self.depth + 1)
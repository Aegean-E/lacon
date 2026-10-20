"""One thought: a glyph, a vowelless payload and an optional number naming an earlier thought.

Eight glyphs are the whole alphabet, and each is a single act of reasoning, so a thought costs one
glyph plus its payload. Rendering a thought produces at most one token, and parsing a script back
into thoughts accepts exactly what rendering produces: glyph, payload, and `^n` for a reference.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from .alphabet import expand

GLYPHS = {
    "?": "unknown",
    "+": "claim",
    "-": "contrast",
    "<": "because",
    ">": "therefore",
    "*": "split",
    "=": "merge",
    "!": "answer",
}
UNKNOWN = "?"
BECAUSE = "<"
THEREFORE = ">"
MERGE = "="
ANSWER = "!"
REFERENCE = "^"


class ThoughtError(ValueError):
    """A script that is not Lacon: an unknown glyph, or a reference that is not a number."""


@dataclass(frozen=True)
class Thought:
    """One act of reasoning: its glyph, its letter payload and an optional evidence number."""

    glyph: str
    payload: str = ""
    ref: Optional[int] = None

    def render(self) -> str:
        """The one-token script form: glyph, then payload, then `^n` when a reference is held."""
        if self.glyph not in GLYPHS:
            raise ThoughtError(f"'{self.glyph}' is not one of the eight Lacon glyphs")
        reference = f"{REFERENCE}{self.ref}" if self.ref is not None else ""
        return self.glyph + self.payload + reference

    def text(self, words: Dict[str, str]) -> str:
        """The readable text of the thought, expanded through the vocabulary."""
        return expand(self.payload, words)


def render(thoughts: Iterable[Thought], separator: str = " ") -> str:
    """The script form of a thought list: one token per thought, in order."""
    return separator.join(thought.render() for thought in thoughts)


def parse(script: str) -> List[Thought]:
    """The thoughts a script holds; anything that is not a Lacon token is refused."""
    thoughts = []
    for token in script.split():
        glyph, rest = token[0], token[1:]
        if glyph not in GLYPHS:
            raise ThoughtError(f"'{glyph}' is not one of the eight Lacon glyphs")
        payload, ref = rest, None
        if REFERENCE in rest:
            payload, _, number = rest.partition(REFERENCE)
            if not number.isdigit():
                raise ThoughtError(f"'{REFERENCE}{number}' is not a thought number")
            ref = int(number)
        thoughts.append(Thought(glyph, payload, ref))
    return thoughts


def answer_text(thoughts: Sequence[Thought], words: Dict[str, str]) -> str:
    """The readable answer a thought list speaks, or the empty string when it says unknown."""
    for thought in reversed(thoughts):
        if thought.glyph == ANSWER:
            return thought.text(words)
    return ""
"""The thinking steps: ranking evidence, then writing the cheapest thought that answers with it.

Nothing here reaches a network or a model outside this package. Given a question and the sentences
that may answer it, the ranker scores each sentence by how many meaning-carrying letters it shares
with the question, and the writer emits the few acts of reasoning that connect the best evidence to
an answer - dropping support first, then answer words, until the budget is met. When nothing in the
context shares a letter with the question, the only honest thought is the unknown glyph.
"""

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .alphabet import PAYLOAD_SEPARATOR, content_words
from .budget import Budget
from .thought import ANSWER, BECAUSE, THEREFORE, UNKNOWN, Thought, render


@dataclass(frozen=True)
class Evidence:
    """One sentence of context: its position, the payload it offers and the score it earned."""

    index: int
    sentence: str
    payload: str
    score: int


class Thinker:
    """Turns a question and the evidence for it into thoughts that fit a letter budget."""

    def rank(self, question: str, evidence: Sequence[str]) -> List[Evidence]:
        """Score every sentence by shared meaning and sort the best matches first."""
        asked = set(content_words(question))
        ranked = [Evidence(index, sentence, PAYLOAD_SEPARATOR.join(content_words(sentence)),
                           len(asked & set(content_words(sentence))))
                  for index, sentence in enumerate(evidence)]
        ranked.sort(key=lambda item: (-item.score, item.index))
        return ranked

    def overlap(self, question: str, text: str) -> int:
        """How many meaning-carrying letters `text` shares with `question`."""
        return len(set(content_words(question)) & set(content_words(text)))

    def best(self, question: str, evidence: Sequence[str]) -> Optional[Evidence]:
        """The highest-scoring sentence that shares at least one letter form, or None."""
        return next((item for item in self.rank(question, evidence) if item.score > 0), None)

    def think(self, question: str, evidence: Sequence[str], budget: Budget) -> List[Thought]:
        """The cheapest thoughts that answer: the evidence, the step it supports, and the answer."""
        found = self.best(question, evidence)
        if found is None:
            return [Thought(UNKNOWN)]
        return self.shrink([Thought(BECAUSE, found.payload, found.index),
                            Thought(THEREFORE),
                            Thought(ANSWER, found.payload)], budget)

    def shrink(self, thoughts: Sequence[Thought], budget: Budget) -> List[Thought]:
        """The most valuable part of `thoughts` that fits: answer words first, support after them."""
        answer = next((item for item in reversed(thoughts) if item.glyph == ANSWER), None)
        if answer is None:
            return list(thoughts) if budget.fits(render(thoughts)) else [Thought(UNKNOWN)]
        support = [item for item in thoughts if item.glyph != ANSWER]
        words = answer.payload.split(PAYLOAD_SEPARATOR) if answer.payload else [""]
        for count in range(len(words), 0, -1):
            for kept in range(len(support), -1, -1):
                candidate = support[:kept] + [Thought(ANSWER,
                                                      PAYLOAD_SEPARATOR.join(words[:count]),
                                                      answer.ref)]
                if budget.fits(render(candidate)):
                    return candidate
        return [Thought(UNKNOWN)]
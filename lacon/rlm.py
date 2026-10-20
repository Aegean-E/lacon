"""Lacon's recursive language model: one question answered by splitting context and recurring.

The engine is its own model. Every node asks the same `Thinker`, but the budget also buys attention
- a node holds only about a budget-eighth of sentences in mind, and never fewer than two - so a
longer context is split and each part is handed to a child that is half as expensive, yet still
afforded enough letters to name a word. A parent then merges what its children said, keeping the
one that matches the question best and marking the merge with the `=` glyph. The recursion stops at
a depth cap, at two sentences or fewer, or wherever a thought already fits.

Supports both natural language and code contexts (Python AST-based extraction).
"""

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .alphabet import lexicon
from .budget import Budget
from .thinker import Thinker
from .thought import MERGE, UNKNOWN, Thought, answer_text, render
from .code_understanding import code_to_sentences, is_code_context

MAX_DEPTH = 4
CHILDREN = 2
SPAN_DIVISOR = 8
MIN_SPAN = 2


@dataclass(frozen=True)
class Answer:
    """What one node concluded: its answer, its script, and the shape of the recursion below it."""

    answer: str
    script: str
    depth: int
    nodes: int
    budget: int

    @property
    def known(self) -> bool:
        """Whether Lacon found evidence that answers, rather than saying unknown."""
        return self.answer != ""


def sentences(text: str) -> List[str]:
    """The sentences of a context: one per line or sentence mark, blanks dropped."""
    spaced = text.replace("!", ".").replace("?", ".").replace("\n", ".")
    return [part.strip() for part in spaced.split(".") if part.strip()]


def partition(items: Sequence[str], parts: int) -> List[List[str]]:
    """Split `items` into at most `parts` contiguous chunks, as evenly as the length allows."""
    count = max(1, min(parts, len(items)))
    size, extra = divmod(len(items), count)
    chunks, start = [], 0
    for index in range(count):
        end = start + size + (1 if index < extra else 0)
        chunks.append(list(items[start:end]))
        start = end
    return [chunk for chunk in chunks if chunk]


class Lacon:
    """The engine: `ask` answers one question from a context, recurring as the budget demands.

    Reuses the vocabulary when the same question+context pair is asked again, which is useful
    for batch evaluation or interactive sessions.
    """

    def __init__(self, thinker: Optional[Thinker] = None) -> None:
        self.thinker = thinker if thinker is not None else Thinker()
        self._lexicon_cache: dict[tuple[str, str], dict] = {}
        self._evidence_cache: dict[str, tuple[str, int]] = {}  # sentence -> (payload, score)

    def ask(self, question: str, context: str = "", budget: int = 64) -> Answer:
        """Answer `question` from `context`, splitting it recursively to respect `budget`.

        If `context` looks like Python code, uses AST-based extraction for better understanding.
        """
        key = (question, context)
        words = self._lexicon_cache.get(key)
        if words is None:
            words = lexicon(question, context)
            self._lexicon_cache[key] = words
        evidence = code_to_sentences(context) if is_code_context(context) else sentences(context)
        thought_list, nodes, depth = self._solve(question, evidence, Budget(budget), 0, words)
        return Answer(answer_text(thought_list, words), render(thought_list), depth, nodes, budget)

    def _prepare_evidence(self, question: str, evidence: Sequence[str]) -> list[tuple[int, str, str, int]]:
        """Prepare evidence with cached payloads and scores: (orig_idx, sentence, payload, score)."""
        asked = self.thinker._asked_content(question)
        prepared = []
        for idx, sent in enumerate(evidence):
            cached = self._evidence_cache.get(sent)
            if cached is not None:
                payload, score = cached
            else:
                payload = self.thinker._payload(sent)
                score = len(asked & self.thinker._content_words(sent))
                self._evidence_cache[sent] = (payload, score)
            prepared.append((idx, sent, payload, score))
        prepared.sort(key=lambda item: (-item[3], item[0]))
        return prepared

    def _span(self, budget: Budget) -> int:
        """How many sentences a node holds in mind: a budget-eighth, but never fewer than two."""
        return max(MIN_SPAN, budget.limit // SPAN_DIVISOR)

    def _solve(self, question: str, evidence: Sequence[str], budget: Budget, depth: int,
               words) -> Tuple[List[Thought], int, int]:
        """Answer at this node: directly when the context fits in mind, by recursion when not."""
        if len(evidence) <= self._span(budget) or depth >= MAX_DEPTH or len(evidence) < 2:
            prepared = self._prepare_evidence(question, evidence)
            return self.thinker.think_prepared(prepared, budget), 1, depth
        children: List[List[Thought]] = []
        nodes, deepest = 1, depth
        for part in partition(evidence, CHILDREN):
            child, child_nodes, child_depth = self._solve(question, part, budget.child(),
                                                          depth + 1, words)
            children.append(child)
            nodes += child_nodes
            deepest = max(deepest, child_depth)
        return self._merge(question, children, budget, words), nodes, deepest

    def _merge(self, question: str, children: Sequence[Sequence[Thought]], budget: Budget,
               words) -> List[Thought]:
        """Copy the child that answers best, marked as a merge of the children that produced it."""
        scored = [(self.thinker.overlap(question, answer_text(child, words)), index, child)
                  for index, child in enumerate(children)]
        if not scored:
            return [Thought(UNKNOWN)]
        best = max(scored, key=lambda item: (item[0], -item[1]))
        if best[0] <= 0:
            return [Thought(UNKNOWN)]
        merged = [Thought(MERGE, "".join(str(index) for _, index, _ in scored))]
        return self.thinker.shrink(merged + list(best[2]), budget)


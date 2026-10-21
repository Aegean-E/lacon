"""Lacon's recursive language model: one question answered by splitting context and recurring.

The engine is its own model. Every node asks the same `Thinker`, but the budget also buys attention
- a node holds only about a budget-eighth of sentences in mind, and never fewer than two - so a
longer context is split and each part is handed to a child that is half as expensive, yet still
afforded enough letters to name a word. A parent then merges what its children said, keeping the
one that matches the question best and marking the merge with the `=` glyph. The recursion stops at
a depth cap, at two sentences or fewer, or wherever a thought already fits.

Supports both natural language and code contexts (Python AST-based extraction).

Enhancements from production RLM systems:
- Tree-wide budget tracking (aggregate script length across recursion tree)
- Trajectory logging with JSONL export
- Tree visualization for debugging
- Tree-wide budget limits (stop when aggregate exceeds limit)
- Document format parsers (CSV, JSON - stdlib only)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple, Any, Dict
import json
import time

from .alphabet import lexicon, PAYLOAD_SEPARATOR
from .budget import Budget, MIN_CHILD
from .thinker import Thinker
from .thought import MERGE, UNKNOWN, Thought, answer_text, render
from .code_understanding import code_to_sentences, is_code_context

MAX_DEPTH = 4
CHILDREN = 2
SPAN_DIVISOR = 8
MIN_SPAN = 2


@dataclass(frozen=True)
class TreeNode:
    """A node in the recursion tree for trajectory tracking."""
    depth: int
    node_id: int
    parent_id: Optional[int]
    evidence_count: int
    budget: int
    span: int
    script: str
    answer: str
    known: bool
    children: List["TreeNode"] = field(default_factory=list)
    duration_ms: float = 0.0
    # Aggregate info (set after children are processed)
    total_nodes: int = 1
    max_child_depth: int = 0


@dataclass(frozen=True)
class Answer:
    """What one node concluded: its answer, its script, and the shape of the recursion below it."""
    answer: str
    script: str
    depth: int
    nodes: int
    budget: int
    # New fields for production features
    tree_chars: int = 0          # Aggregate script length across entire tree
    tree_nodes: int = 0          # Total nodes in tree
    max_depth: int = 0           # Maximum depth reached
    duration_ms: float = 0.0     # Total time spent
    tree: Optional[TreeNode] = None  # Full recursion tree for trajectory

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

    Production features:
    - Tree-wide budget tracking (aggregate_chars parameter)
    - Trajectory logging with JSONL export
    - Tree visualization
    - Tree-wide budget limits
    """

    def __init__(
        self,
        thinker: Optional[Thinker] = None,
        *,
        max_total_chars: Optional[int] = None,   # Tree-wide character budget (None = unlimited)
    ) -> None:
        self.thinker = thinker if thinker is not None else Thinker()
        self._lexicon_cache: dict[tuple[str, str], dict] = {}
        self._payload_cache: dict[str, str] = {}
        self._max_total_chars = max_total_chars
        self._tree_chars = 0
        self._next_node_id = 0

    def ask(
        self,
        question: str,
        context: str = "",
        budget: int = 64,
        *,
        max_total_chars: Optional[int] = None,
        context_format: str = "auto",
    ) -> Answer:
        """Answer `question` from `context`, splitting it recursively to respect `budget`.

        Python code, CSV and JSON contexts are auto-detected. Pass `context_format` as
        "text", "csv" or "json" to force one reader; "auto" is the default.

        Args:
            question: The question to answer
            context: The context text (or code) to answer from
            budget: Per-node character budget (default 64)
            max_total_chars: Optional tree-wide character budget. If set, stops recursion
                           when aggregate script length across tree exceeds this limit.
            context_format: "auto", "text", "csv" or "json"
        """
        start_time = time.perf_counter()
        key = (question, context)
        words = self._lexicon_cache.get(key)
        if words is None:
            words = lexicon(question, context)
            self._lexicon_cache[key] = words

        if context_format == "auto" and is_code_context(context):
            evidence = code_to_sentences(context)
        else:
            evidence = parse_context(context, context_format)

        # Reset tree-wide tracking
        self._tree_chars = 0
        self._next_node_id = 0
        tree_chars_limit = max_total_chars if max_total_chars is not None else self._max_total_chars

        thought_list, root_node = self._solve(
            question,
            evidence,
            Budget(budget),
            0,
            words,
            tree_chars_limit,
            parent_id=None,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        return Answer(
            answer=answer_text(thought_list, words),
            script=render(thought_list),
            depth=root_node.max_child_depth,
            nodes=root_node.total_nodes,
            budget=budget,
            tree_chars=self._tree_chars,
            tree_nodes=root_node.total_nodes,
            max_depth=root_node.max_child_depth,
            duration_ms=(time.perf_counter() - start_time) * 1000,
            tree=root_node,
        )

    def _prepare_evidence(self, question: str, evidence: Sequence[str]) -> list[tuple[int, str, str, int]]:
        """Prepare evidence with cached payloads and fresh scores: (orig_idx, sentence, payload, score)."""
        asked = self.thinker._asked_content(question)
        prepared = []
        for idx, sent in enumerate(evidence):
            cached_payload = self._payload_cache.get(sent)
            if cached_payload is not None:
                payload = cached_payload
            else:
                payload = self.thinker._payload(sent)
                self._payload_cache[sent] = payload
            score = len(asked & self.thinker._content_words(sent))
            prepared.append((idx, sent, payload, score))
        prepared.sort(key=lambda item: (-item[3], item[0]))
        return prepared

    def _span(self, budget: Budget) -> int:
        """How many sentences a node holds in mind: a budget-eighth, but never fewer than two."""
        return max(MIN_SPAN, budget.limit // SPAN_DIVISOR)

    def _solve(
        self,
        question: str,
        evidence: Sequence[str],
        budget: Budget,
        depth: int,
        words: Dict[str, str],
        tree_chars_limit: Optional[int],
        parent_id: Optional[int],
    ) -> Tuple[List[Thought], TreeNode]:
        """Answer at this node: directly when the context fits in mind, by recursion when not."""
        node_id = self._next_node_id
        self._next_node_id += 1

        node_start = time.perf_counter()
        span = self._span(budget)

        # Check tree-wide budget limit before proceeding
        if tree_chars_limit is not None and self._tree_chars >= tree_chars_limit:
            thought_list = [Thought(UNKNOWN)]
            script = render(thought_list)
            self._tree_chars += len(script)
            node = TreeNode(
                depth=depth,
                node_id=node_id,
                parent_id=parent_id,
                evidence_count=len(evidence),
                budget=budget.limit,
                span=span,
                script=script,
                answer="",
                known=False,
                duration_ms=(time.perf_counter() - node_start) * 1000,
            )
            return thought_list, node

        # Base case: context fits in mind, depth cap, or single sentence
        if len(evidence) <= span or depth >= MAX_DEPTH or len(evidence) < 2:
            prepared = self._prepare_evidence(question, evidence)
            asked = self.thinker._asked_content(question)
            thought_list = self.thinker.think_prepared(prepared, budget, asked)
            script = render(thought_list)
            self._tree_chars += len(script)

            ans = answer_text(thought_list, words)
            node = TreeNode(
                depth=depth,
                node_id=node_id,
                parent_id=parent_id,
                evidence_count=len(evidence),
                budget=budget.limit,
                span=span,
                script=script,
                answer=ans,
                known=ans != "",
                duration_ms=(time.perf_counter() - node_start) * 1000,
                max_child_depth=depth,  # Leaf node's max depth is its own depth
            )
            return thought_list, node

        # Recursive case: split and recurse
        children: List[List[Thought]] = []
        child_nodes: List[TreeNode] = []
        nodes, deepest = 1, depth

        for part in partition(evidence, CHILDREN):
            child_thoughts, child_node = self._solve(
                question,
                part,
                budget.child(),
                depth + 1,
                words,
                tree_chars_limit,
                node_id,
            )
            children.append(child_thoughts)
            child_nodes.append(child_node)
            nodes += child_node.total_nodes
            deepest = max(deepest, child_node.max_child_depth)

        # Merge children
        asked = self.thinker._asked_content(question)
        merged_thoughts = self._merge(question, children, budget, asked)
        script = render(merged_thoughts)
        self._tree_chars += len(script)

        ans = answer_text(merged_thoughts, words)
        node = TreeNode(
            depth=depth,
            node_id=node_id,
            parent_id=parent_id,
            evidence_count=len(evidence),
            budget=budget.limit,
            span=span,
            script=script,
            answer=ans,
            known=ans != "",
            children=child_nodes,
            duration_ms=(time.perf_counter() - node_start) * 1000,
            total_nodes=nodes,
            max_child_depth=deepest,
        )

        return merged_thoughts, node

    def _merge(
        self,
        question: str,
        children: Sequence[Sequence[Thought]],
        budget: Budget,
        asked: set,
    ) -> List[Thought]:
        """Copy the child that answers best, marked as a merge of the children that produced it."""
        scored = [
            (self.thinker.overlap(question, answer_text(child, words={})), index, child)
            for index, child in enumerate(children)
        ]
        if not scored:
            return [Thought(UNKNOWN)]
        best = max(scored, key=lambda item: (item[0], -item[1]))
        if best[0] <= 0:
            return [Thought(UNKNOWN)]
        merged = [Thought(MERGE, "".join(str(index) for _, index, _ in scored))]
        return self.thinker.shrink(merged + list(best[2]), budget, asked)

    def export_tree_json(self, answer: Answer) -> str:
        """Export the recursion tree as JSONL (one line per node)."""
        lines = []

        def visit(node: TreeNode):
            lines.append(json.dumps({
                "node_id": node.node_id,
                "parent_id": node.parent_id,
                "depth": node.depth,
                "evidence_count": node.evidence_count,
                "budget": node.budget,
                "span": node.span,
                "script_len": len(node.script),
                "script": node.script,
                "answer": node.answer,
                "known": node.known,
                "duration_ms": node.duration_ms,
                "children": [c.node_id for c in node.children],
            }, ensure_ascii=False))
            for child in node.children:
                visit(child)

        if answer.tree:
            visit(answer.tree)
        return "\n".join(lines)

    def export_tree_text(self, answer: Answer, use_ascii: bool = True) -> str:
        """Export the recursion tree as a human-readable text tree.
        
        Args:
            answer: The Answer with a tree
            use_ascii: If True, use ASCII characters instead of Unicode box-drawing
        """
        if not answer.tree:
            return "(no tree)"

        lines = []
        if use_ascii:
            # ASCII-only tree characters
            branch_last = "`-- "
            branch_mid = "|-- "
            indent_last = "    "
            indent_mid = "|   "
            prefix_last = "   "
            prefix_mid = "|  "
        else:
            # Unicode box-drawing characters
            branch_last = "`-- "
            branch_mid = "|-- "
            indent_last = "    "
            indent_mid = "|   "

        lines = []

        def visit(node: TreeNode, prefix: str = "", is_last: bool = True):
            status = "+" if node.known else "?"
            budget_info = f"budget={node.budget}, span={node.span}, evid={node.evidence_count}"
            branch = branch_last if is_last else branch_mid
            lines.append(f"{prefix}{branch}Node {node.node_id} (depth {node.depth}) {status} [{budget_info}] script_len={len(node.script)}")
            if node.script:
                display_script = node.script[:80] + ("..." if len(node.script) > 80 else "")
                indent = indent_last if is_last else indent_mid
                lines.append(f"{prefix}{indent}  `-- {display_script}")
            child_prefix = prefix + (indent_last if is_last else indent_mid)
            for i, child in enumerate(node.children):
                visit(child, child_prefix, i == len(node.children) - 1)

        if not answer.tree:
            return "(no tree)"
        visit(answer.tree)
        return "\n".join(lines)


# Document format parsers (stdlib only)
def parse_csv(text: str) -> List[str]:
    """Parse CSV text into sentences (one per row)."""
    import csv
    import io
    sentences = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        # Join row fields with space
        sentence = " ".join(field.strip() for field in row if field.strip())
        if sentence:
            sentences.append(sentence)
    return sentences


def parse_json(text: str) -> List[str]:
    """Parse JSON into sentences that keep keys and scalar values."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    def flatten(value, path):
        if isinstance(value, dict):
            scalars = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    yield from flatten(item, path + [str(key)])
                else:
                    scalars.extend([str(key), str(item)])
            if scalars:
                yield " ".join(path + scalars)
        elif isinstance(value, list):
            for item in value:
                yield from flatten(item, path)
        elif value is not None:
            yield " ".join(path + [str(value)])

    return [s.strip() for s in flatten(data, []) if s.strip()]


def parse_context(text: str, format: str = "auto") -> List[str]:
    """Parse context text based on format.

    Args:
        text: The input text
        format: "auto", "text", "csv", "json"

    Returns:
        List of sentences/rows
    """
    if format == "csv":
        return parse_csv(text)
    elif format == "json":
        return parse_json(text)
    elif format == "auto":
        # Heuristic: try JSON first, then CSV, then plain text
        try:
            json.loads(text)
            return parse_json(text)
        except json.JSONDecodeError:  # Not JSON, try CSV next; hygiene: allow expected fallback
            pass
        if "," in text and "\n" in text:
            try:
                return parse_csv(text)
            except Exception:  # Not valid CSV, fall back to plain text; hygiene: allow expected fallback
                pass
        return sentences(text)
    else:
        return sentences(text)
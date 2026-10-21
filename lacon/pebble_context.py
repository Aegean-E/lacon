"""Read Pebble source as evidence for Lacon, using Pebble's own lexer and parser.

The adapter is optional and lazy: importing Lacon never imports Pebble. When a
caller asks for a "pebble" context, an installed ``pebble`` package - or the
sibling project in an AIKit workspace - supplies the lexer, parser and AST, and
the declarations, loops and comments become deterministic evidence sentences.
Lacon's core remains standard-library-only when this format is not used.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class _PebbleApi:
    """The handful of Pebble entry points this adapter needs, loaded lazily."""

    tokenize: object
    parse: object
    nodes: object
    error: type


class PebbleContextError(ValueError):
    """A Pebble context that could not be read, with the What/Why/Fix report."""

    def __init__(self, message: str, why: str, fix: str) -> None:
        super().__init__(message)
        self.message = message
        self.why = why
        self.fix = fix


def pebble_to_sentences(source: str, root: Optional[str] = None) -> List[str]:
    """The evidence sentences in a Pebble program, in source order.

    ``root`` optionally points at a Pebble checkout for callers outside the
    AIKit workspace; without it the sibling project is discovered, then a
    normal ``import pebble`` is tried first.
    """
    api = _load_pebble(root)
    error_type = api.error
    try:
        program = api.parse(api.tokenize(source))
    except error_type as error:
        raise PebbleContextError(
            f"cannot read Pebble context at {error.line}:{error.col}: {error.message}",
            error.why,
            error.fix,
        ) from None
    return _comment_sentences(source) + _statement_sentences(program, api.nodes)


def _load_pebble(root: Optional[str]) -> _PebbleApi:
    """Import Pebble normally, then from an explicit or sibling checkout."""
    try:
        return _import_pebble()
    except ImportError:
        candidate = _candidate_root(root)
        if candidate is None:
            raise PebbleContextError(
                "the pebble package is not importable",
                "reading a Pebble context needs Pebble's lexer and parser, and neither an "
                "installed package nor the sibling project was found",
                "install Pebble with 'pip install -e ../pebble', or run from the AIKit "
                "workspace where projects/pebble exists",
            ) from None
        sys.path.insert(0, str(candidate))
        try:
            return _import_pebble()
        except ImportError:
            raise PebbleContextError(
                f"the Pebble package at '{candidate}' could not be imported",
                "that path does not contain a working pebble package",
                "point at a checkout whose pebble/__init__.py exists, or install Pebble",
            ) from None
        finally:
            sys.path.remove(str(candidate))


def _import_pebble() -> _PebbleApi:
    """The real import, kept separate so a missing package is recoverable."""
    from pebble import nodes
    from pebble.errors import PebbleError
    from pebble.lexer import tokenize
    from pebble.parser import parse

    return _PebbleApi(tokenize, parse, nodes, PebbleError)


def _candidate_root(root: Optional[str]) -> Optional[Path]:
    """An explicit checkout, or the sibling projects/pebble directory."""
    if root is not None:
        return Path(root)
    sibling = Path(__file__).resolve().parents[2] / "pebble"
    return sibling if (sibling / "pebble" / "__init__.py").is_file() else None


def _comment_sentences(source: str) -> List[str]:
    """Every meaningful ``#`` comment, so prose in a program stays evidence."""
    sentences = []
    for number, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        text = stripped[1:].strip()
        if text:
            sentences.append(f"comment at line {number} {text}")
    return sentences


def _statement_sentences(statements, nodes) -> List[str]:
    """Declarations, loops and function signatures as searchable sentences."""
    sentences = []
    for statement in statements:
        if isinstance(statement, nodes.FnStmt):
            params = ", ".join(statement.params)
            detail = f"parameters {params}" if params else "no parameters"
            sentences.append(
                f"function {statement.name} takes {detail} at line {statement.line}")
            sentences.extend(_statement_sentences(statement.body, nodes))
        elif isinstance(statement, nodes.Let):
            sentences.append(
                f"variable {statement.name} is declared at line {statement.line}")
        elif isinstance(statement, nodes.ForStmt):
            sentences.append(
                f"for loop variable {statement.name} iterates at line {statement.line}")
            sentences.extend(_statement_sentences(statement.body, nodes))
        elif isinstance(statement, nodes.WhileStmt):
            sentences.append(f"while loop repeats at line {statement.line}")
            sentences.extend(_statement_sentences(statement.body, nodes))
        elif isinstance(statement, nodes.IfStmt):
            sentences.append(f"if branch starts at line {statement.line}")
            sentences.extend(_statement_sentences(statement.then_body, nodes))
            sentences.extend(_statement_sentences(statement.else_body, nodes))
    return sentences

---
name: lacon
version: 0.1.0
description: >-
  Recursive Language Model engine for ultra-compact reasoning. An AI that thinks in as few
  letters as possible: eight glyphs, vowelless payloads, hard letter budget, and recursive
  budget-halving. Use this skill when you need to answer questions from a context while
  strictly bounding the reasoning token count, or when you want a self-contained RLM engine
  with no external dependencies.
---

# Lacon Skill (Recursive Language Model Engine)

A self-contained reasoning engine that answers questions from a context by writing its thoughts
in a minimal alphabet under a hard character budget, recursing over long contexts.

## 🌐 Integration Matrix

- **As a Python library** (recommended): `from lacon import Lacon, Answer`
- **As a CLI**: `python -m lacon ask "QUESTION" [--context FILE] [--budget N] [--script|--json|--trace]`
- **As an AIKit skill**: This SKILL.md makes lacon discoverable when the project is attached to an AIKit workspace
- **State SSOT**: None (stateless engine); context and budget are passed per call

## 🧱 AIKit Project Integration

When this project is attached to an AIKit workspace via `python aikit.py attach path/to/lacon`,
this skill becomes available. In AIKit scripts or subagents:

```python
# Direct library use
from lacon import Lacon, Answer

answer = Lacon().ask("What keeps the bridge from rust?", context_text, budget=64)
# answer.answer -> "paint keeps steel rust"
# answer.script -> "<pnt.kps.stl.rst^1 > !pnt.kps.stl.rst"
# answer.known  -> True
```

```bash
# CLI use (non-interactive, --help exits 0 in <200ms)
python -m lacon demo --trace
python -m lacon ask "what is the answer?" --context notes.txt --budget 16 --json
```

## ⚡ Quick Reference

- **Runtime**: Python 3.10+, stdlib only, zero dependencies
- **Test gate**: `python -m unittest discover` (70 tests, ~14ms)
- **Exit codes**: 0 answered, 1 unanswered/unknown, 2 usage/file error
- **Error format**: What / Why / Fix on stderr, never a traceback
- **Stdin parity**: `--context -` reads context from stdin

## 🔤 The Alphabet (ADR-001)

Eight glyphs, one per reasoning act:

| Glyph | Act | Glyph | Act |
|-------|-----|-------|-----|
| `?`   | unknown | `<`   | because |
| `+`   | claim   | `>`   | therefore |
| `-`   | contrast| `*`   | split    |
| `=`   | merge   | `!`   | answer   |

A thought = glyph + payload (vowelless letters/digits) + optional `^ref`. Example:
`!pnt.kps.stl.rst` = "paint keeps steel rust" (16 letters).

## 💰 Budget Ladder (ADR-002)

- **Budget** = ceiling in letters + recursion depth
- **Shrink order**: answer words kept first, then support (`<`, `>`, `=`)
- **Child budget** = `max(8, parent_limit // 2)` — a child always has room for one word
- **Span** = `max(2, budget // 8)` sentences per node; longer → split & recurse
- **Cap**: depth ≤ 4, or ≤ 2 sentences, or already fits
- **Invariant**: `len(answer.script) <= budget` always

## 🔁 Recursive Engine

```
Lacon().ask(question, context, budget=64)
  → Thinker ranks evidence by shared content words
  → If context fits span: direct thought, fits budget
  → Else: split context, recurse with child budget
  → Merge: pick child with highest overlap, prefix with =01
```

Output (trace): `[lacon] 12 of 16 letters, depth 2, 7 node(s)`

## 🚫 Non-Goals (v1)

- External models, API keys, or streaming
- Claims/contrasts beyond what an answer needs
- World knowledge — answers only from given context

## 📦 What's Inside (for AIKit adoption)

```
lacon/
├── .aikit/
│   ├── codebase_map.md       <- generated AST map
│   ├── decisions.md          <- ADR-001 (alphabet), ADR-002 (budget/RLM)
│   ├── guidelines.md         <- G-001: alphabet frozen
│   ├── project.json
│   └── task_ledger.json
├── .aikit/skills/lacon/
│   └── SKILL.md              <- this file
├── .gitignore
├── LICENSE (AGPL-3.0)
├── README.md
├── examples/notes.txt
├── lacon/
│   ├── __init__.py           <- export Lacon, Answer
│   ├── __main__.py           <- `python -m lacon`
│   ├── alphabet.py           <- skeleton, lexicon, expand
│   ├── budget.py             <- Budget class
│   ├── cli.py                <- ask/demo, flags, exit codes
│   ├── rlm.py                <- Lacon engine (split/merge)
│   ├── thinker.py            <- rank, think, shrink
│   └── thought.py            <- Thought, render, parse
├── pyproject.toml            <- console script 'lacon'
└── tests/                    <- 70 tests
```

## 🤝 Adoption Checklist

When adopting lacon into an AIKit workspace or another project:

1. `python aikit.py attach path/to/lacon` (or copy the `lacon/` package)
2. Verify: `python -m unittest discover` from the project root
3. Import: `from lacon import Lacon` — no initialization needed
4. Optional: add a project guideline linking to ADR-001/002
5. For AIKit scripts: wrap calls in a subagent or use `aikit.py delegate` for bulk work

## 📜 License

AGPL-3.0 — see LICENSE. If integrating into a proprietary codebase, ensure license compatibility.
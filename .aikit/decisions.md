# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

<!-- Entry format:
# ADR-001: Title
- **Date**: YYYY-MM-DD
- **Status**: Accepted
- **Context**: ...
- **Decision**: ...
- **Consequences**: ...
-->

### ADR-001: Lacon v1 is frozen as a self-contained engine that thinks in eight glyphs
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The project brief is an AI that thinks with too few letters, as compact as possible and
  recursive-language-model compatible, with everything inside the project. Two decisions follow from
  that: what a "thought" is, and where thinking comes from, since an external model or an API key
  would put the project's whole subject outside the project.
- **Decision**: A thought is one of eight glyphs (`?` unknown, `+` claim, `-` contrast, `<` because,
  `>` therefore, `*` split, `=` merge, `!` answer) followed by a payload written without vowels, so a
  thought costs one glyph plus letters and a reader expands the payload through the vocabulary of the
  question and its context. The thinker is the project itself: a deterministic ranker that scores each
  context sentence by shared meaning-carrying letters and answers from the best one, so no network
  call, no API key, no model weight and no third-party dependency exists anywhere. The command line
  is `ask` and `demo`, exiting 0 answered, 1 unanswered and 2 misuse, with every report in
  What/Why/Fix form. Non-goals: claims and contrasts beyond what an answer needs, a user-supplied
  model, streaming, and any surface not listed here.
- **Consequences**: An answer is reproducible and testable to the character, and the whole engine is
  readable in one sitting. Costs: the engine reasons only over the sentences it is handed and answers
  "unknown" rather than inferring anything, so its intelligence is bounded by its context by design
  rather than by accident.

### ADR-002: The letter budget is spent by a fixed ladder, and recursion is bounded
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: ADR-001 promises that every thought fits a ceiling in letters, but not how a thought
  is cut down to fit, when the engine recurses instead of answering directly, or how the two
  interact. Without a written rule the sizes would drift with every edit and the recursion could
  either never trigger or run away.
- **Decision**: A budget is a ceiling in characters and a depth, and it refuses a ceiling below one
  letter. Shrinking keeps answer words before support: for a sentence's content words, more words
  beat more provenance, and support is dropped from the right, so `<` and `>` disappear before the
  answer shortens. The unknown glyph `?` is one letter, so a ceiling too small to hold a word still
  has an honest thought, and a budget of one letter answers only `?`. A node holds in mind one
  sentence per eight letters of budget, never fewer than two, so a longer context is split into two
  contiguous halves; each child gets half the parent's ceiling but never fewer than eight letters, so
  the deepest thought can still name a word. Recursion stops at a depth of four, at two sentences or
  fewer, or where the thought already fits. A parent keeps the child answer that shares the most
  meaning with the question and marks the merge with `=`, followed by the children's numbers.
- **Consequences**: The ladder is testable end to end: the same question answered at 64, 16, 8 and 1
  letters yields four different, deterministic thoughts, and recursion is visible in `--trace` as
  depth and node count. Costs: a small budget degrades the answer to fewer words rather than a
  shorter phrasing of the same idea, and the total letters across a recursive tree exceed the root
  budget, which is the intended cost of splitting.

### ADR-003: Pebble source is an optional context format, read through Pebble's own parser
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: Lacon's code understanding reads Python through `ast` and produces shallow,
  breadth-first signatures. Pebble already has a positioned lexer, parser and AST for its own
  language, and the two projects are complementary at that boundary: Pebble supplies structure,
  Lacon supplies budgeted evidence selection. Merging the engines would force Pebble to grow text
  utilities and would force Lacon to carry an evaluator, so the integration must stay a narrow,
  optional adapter rather than a shared runtime.
- **Decision**: Add `context_format="pebble"` to `Lacon.ask` and `--context-format pebble` to the
  command line. The adapter lives in `lacon/pebble_context.py`, imports Pebble lazily, and uses
  Pebble's own `tokenize`, `parse` and AST nodes; it turns comments, function signatures, `let`
  declarations, loops and `if` branches into deterministic evidence sentences. A `.peb` context
  path selects the reader when the format is `auto`; standard input requires the explicit flag.
  Core Lacon stays standard-library-only when the format is unused, and Pebble must never import
  Lacon. A missing Pebble checkout or a Pebble syntax error raises `PebbleContextError` with
  What/Why/Fix and makes the command line exit 2. The lexicon used for expansion now includes the
  evidence sentences as well as the raw question and context, so synthetic words such as
  "function" and "parameters" expand readably. The alphabet, budget ladder, recursion and thought
  format are unchanged.
- **Consequences**: Lacon can answer structural questions about `.peb` files offline, with an
  auditable thought script, while remaining dependency-free for every other context. Costs: the
  feature has an optional runtime dependency on a sibling or installed Pebble package; the adapter
  adds evidence vocabulary to the lexicon; answers remain keyword-overlap answers, so they describe
  declarations and comments rather than executing the program; and `.peb` inference is only a
  path-suffix rule, not content detection.

### ADR-004: The tree-wide character budget is a hard aggregate cap
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: README and the `Lacon.ask` docstring promise that `max_total_chars` caps the whole
  recursion tree, but the implementation only stopped before solving a node when the aggregate
  already exceeded the limit. The root script was never fitted to the cap, so a cap of one could
  still return a thirty-seven-character answer, and the only test asserted a reduction rather than
  the bound. The contract was therefore untrue at the boundary it claimed to protect.
- **Decision**: `max_total_chars` is a hard cap on `Answer.tree_chars`, the sum of every node's
  script length. Each leaf is fitted to the characters remaining; a recursive node reserves at
  most its own letter budget for the merge, gives each child an absolute cap of at least
  `MIN_CHILD`, and only splits when at least two child allowances plus one parent allowance fit.
  A child cannot consume another child's or the parent's share. A cap of zero returns an empty
  unknown script and an aggregate of zero; a one-character cap can return only `?`. A generous cap
  reproduces the unlimited tree exactly.
- **Consequences**: The budget claim is now testable at every ceiling, including 0, 1, 8, 17, 24,
  50, 100 and 200 characters, and a generous cap is pinned against the unlimited answer. Costs: a
  tight cap can leave budget unused or return an unknown answer rather than an over-budget answer,
  which is the intended trade; the allocation adds two small helpers and a recursion-eligibility
  check to the engine.

### ADR-005: Wall-clock benchmarks leave the default regression gate
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: `tests/test_performance.py::test_lexicon_speed` failed the Phase 4 test gate at
  112.9ms against a 100ms wall-clock budget while another process was running, then passed when
  run alone. The suite is the project's deterministic regression shield, and host load made a
  green gate depend on scheduling rather than on the code. The user approved changing this test.
- **Decision**: Move the seven wall-clock `PerformanceTests` out of `tests/test_performance.py`
  into `benchmarks/performance.py`, which `unittest discover` does not collect because its name
  does not match `test*.py`. Run the benchmarks explicitly with
  `python -m unittest benchmarks.performance`. Keep the behaviour, code-understanding and edge-case
  tests in the default suite, and collect the previously module-level `test_snake_case_in_question`
  inside `CodeUnderstandingTests`. The benchmark thresholds stay unchanged so the measurements
  remain comparable; only their place in the gate changes.
- **Consequences**: The default suite is deterministic, faster and still covers the engine's
  behaviour; performance regressions remain measurable on a quiet host. Cost: timing checks are no
  longer a hard commit gate, so a deliberate benchmark run is required when performance changes.
  This ADR names the weakened/relocated test `tests/test_performance.py::test_lexicon_speed` and
  records the user's approval for the move.

## Licensing migration (v0.1.0-agpl)

- New versions use the Aegean License 1.1 (AL-1.1); versions up to and including `v0.1.0-agpl` remain under GNU AGPL-3.0.
- Rights holder: AegeanWorks; commercial use under ACL-1.0.
- Counsel review of the 1.1 texts remains pending.

## License notice cleanup (2026-10-26)

- The license-history notes were removed from README.md and COMMERCIAL.md: the project is offered only under the Aegean License 1.1 (AL-1.1), with commercial use under ACL-1.0.

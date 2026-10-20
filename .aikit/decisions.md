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
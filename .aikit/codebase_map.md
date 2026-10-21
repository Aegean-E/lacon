# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `19`
- **Total Classes**: `33`
- **Total Top-Level Functions**: `28`
- **Total Class Methods**: `132`
- **Total Source Lines**: `1960`

---

## 📦 Modules & Exported Symbols

### [`lacon/__init__.py`](lacon/__init__.py)
> *Lacon: an AI that thinks in as few letters as possible, recursively over a long context.*

**Size**: `10` lines (`329` bytes)

---

### [`lacon/__main__.py`](lacon/__main__.py)
> *Run Lacon with `python -m lacon`.*

**Size**: `6` lines (`119` bytes)

---

### [`lacon/alphabet.py`](lacon/alphabet.py)
> *The Lacon alphabet: vowelless letter payloads, and the vocabulary that expands them back.*

**Size**: `56` lines (`2412` bytes)

**Functions:**
- `def skeleton(text)` - *The letter form of one text: lowercase words with vowels and punctuation removed.*
- `def content_words(text)` - *The skeletons that carry meaning: vowels, punctuation and common words removed.*
- `def lexicon(*texts)` - *The vocabulary of the given texts, mapping each letter form to its shortest spelling.*
- `def expand(payload, words)` - *The readable text behind a payload; a letter form no word matches is shown as it is.*
- `def _stem(word)` - *One word without its vowels: `bridge` becomes `brdg`, a vowel-only word becomes empty.*

---

### [`lacon/budget.py`](lacon/budget.py)
> *The letter budget: the hard ceiling on how many characters one thought may cost.*

**Size**: `36` lines (`1372` bytes)

**Classes:**
- `class Budget` - *A ceiling in characters and the recursion depth it belongs to.*
  - Method `.__post_init__()` - *Refuse a ceiling that could not hold even the one-letter unknown glyph.*
  - Method `.fits(script)` - *Whether a rendered script costs no more than the ceiling.*
  - Method `.room(glyph)` - *How many payload characters remain after a glyph of this cost.*
  - Method `.child()` - *The budget of a recursive step: half this ceiling, but never below `MIN_CHILD`.*

---

### [`lacon/cli.py`](lacon/cli.py)
> *Lacon's command line: ask one question, or run the built-in demo.*

**Size**: `203` lines (`9291` bytes)

**Classes:**
- `class CliError` - *A usage or file failure, rendered with the same What/Why/Fix shape as an answer refusal.*
  - Method `.__init__(message, why, fix)`

**Functions:**
- `def main(argv, stdin, stdout, stderr)` - *Run the command line; every argument defaults to the matching process stream.*
- `def _report_internal(error, stderr)` - *Last-resort report: a host failure is still explained, and never shown as a traceback.*
- `def _dispatch(arguments, stdin, stdout, stderr)` - *Route the arguments to `ask` or `demo`.*
- `def _options(arguments)` - *Parse the flags of one command into a plain option mapping.*
- `def _budget(value)` - *The letter ceiling as a positive integer, or a usage error.*
- `def _context(options, stdin)` - *The context text: from a file, from standard input for `-`, or empty when unnamed.*
- `def _run(question, context, options, stdout, stderr)` - *Answer one question and report it in the requested form.*
- `def _trace(answer)` - *The one-line recursion report: what the letters bought, and how deep it split.*

---

### [`lacon/code_understanding.py`](lacon/code_understanding.py)
> *Code understanding: extract meaningful elements from source code using AST.*

**Size**: `153` lines (`5177` bytes)

**Classes:**
- `class CodeElement` - *A meaningful element extracted from code.*

**Functions:**
- `def extract_code_elements(source)` - *Extract meaningful code elements from Python source.*
- `def _func_signature(node, async_)` - *Generate a readable function signature.*
- `def code_to_sentences(source)` - *Convert code into meaningful sentences for the engine.*
- `def is_code_context(text)` - *Heuristic: does the text look like Python code?*

---

### [`lacon/rlm.py`](lacon/rlm.py)
> *Lacon's recursive language model: one question answered by splitting context and recurring.*

**Size**: `472` lines (`17242` bytes)

**Classes:**
- `class TreeNode` - *A node in the recursion tree for trajectory tracking.*
- `class Answer` - *What one node concluded: its answer, its script, and the shape of the recursion below it.*
  - Property `.known` - *Whether Lacon found evidence that answers, rather than saying unknown.*
- `class Lacon` - *The engine: `ask` answers one question from a context, recurring as the budget demands.*
  - Method `.__init__(thinker, *, max_total_chars)`
  - Method `.ask(question, context, budget, *, max_total_chars, context_format)` - *Answer `question` from `context`, splitting it recursively to respect `budget`.*
  - Method `._prepare_evidence(question, evidence)` - *Prepare evidence with cached payloads and fresh scores: (orig_idx, sentence, payload, score).*
  - Method `._span(budget)` - *How many sentences a node holds in mind: a budget-eighth, but never fewer than two.*
  - Method `._solve(question, evidence, budget, depth, words, tree_chars_limit, parent_id)` - *Answer at this node: directly when the context fits in mind, by recursion when not.*
  - Method `._merge(question, children, budget, asked)` - *Copy the child that answers best, marked as a merge of the children that produced it.*
  - Method `.export_tree_json(answer)` - *Export the recursion tree as JSONL (one line per node).*
  - Method `.export_tree_text(answer, use_ascii)` - *Export the recursion tree as a human-readable text tree.*

**Functions:**
- `def sentences(text)` - *The sentences of a context: one per line or sentence mark, blanks dropped.*
- `def partition(items, parts)` - *Split `items` into at most `parts` contiguous chunks, as evenly as the length allows.*
- `def parse_csv(text)` - *Parse CSV text into sentences (one per row).*
- `def parse_json(text)` - *Parse JSON into sentences that keep keys and scalar values.*
- `def parse_context(text, format)` - *Parse context text based on format.*

---

### [`lacon/thinker.py`](lacon/thinker.py)
> *The thinking steps: ranking evidence, then writing the cheapest thought that answers with it.*

**Size**: `107` lines (`5400` bytes)

**Classes:**
- `class Evidence` - *One sentence of context: its position, the payload it offers and the score it earned.*
- `class Thinker` - *Turns a question and the evidence for it into thoughts that fit a letter budget.*
  - Method `._asked_content(question)` - *The set of meaning-carrying letter forms in the question.*
  - Method `._content_words(sentence)` - *The set of meaning-carrying letter forms in a sentence.*
  - Method `._payload(sentence)` - *The vowelless payload for a sentence.*
  - Method `.rank(question, evidence)` - *Score every sentence by shared meaning and sort the best matches first.*
  - Method `.overlap(question, text)` - *How many meaning-carrying letters `text` shares with `question`.*
  - Method `.best(question, evidence)` - *The highest-scoring sentence that shares at least one letter form, or None.*
  - Method `.think(question, evidence, budget)` - *The cheapest thoughts that answer: the evidence, the step it supports, and the answer.*
  - Method `.think_prepared(prepared, budget, asked)` - *Think using pre-ranked evidence: list of (orig_idx, sentence, payload, score).*
  - Method `.shrink(thoughts, budget, asked)` - *The most valuable part of `thoughts` that fits: answer words first, support after them.*

---

### [`lacon/thought.py`](lacon/thought.py)
> *One thought: a glyph, a vowelless payload and an optional number naming an earlier thought.*

**Size**: `82` lines (`2865` bytes)

**Classes:**
- `class ThoughtError` - *A script that is not Lacon: an unknown glyph, or a reference that is not a number.*
- `class Thought` - *One act of reasoning: its glyph, its letter payload and an optional evidence number.*
  - Method `.render()` - *The one-token script form: glyph, then payload, then `^n` when a reference is held.*
  - Method `.text(words)` - *The readable text of the thought, expanded through the vocabulary.*

**Functions:**
- `def render(thoughts, separator)` - *The script form of a thought list: one token per thought, in order.*
- `def parse(script)` - *The thoughts a script holds; anything that is not a Lacon token is refused.*
- `def answer_text(thoughts, words)` - *The readable answer a thought list speaks, or the empty string when it says unknown.*

---

### [`tests/__init__.py`](tests/__init__.py)
> *The lacon test suite: unit tests, in process, with no network and no subprocess.*

**Size**: `1` lines (`86` bytes)

---

### [`tests/test_alphabet.py`](tests/test_alphabet.py)
> *Alphabet tests: the vowelless letter form, the meaning-carrying words and the expansion back.*

**Size**: `54` lines (`2059` bytes)

**Classes:**
- `class SkeletonTests` - *`skeleton` is the letter form: lowercase, vowelless, punctuation gone.*
  - Method `.test_vowels_and_punctuation_are_removed()`
  - Method `.test_a_word_of_vowels_only_disappears()`
  - Method `.test_digits_survive_as_themselves()`
- `class ContentWordTests` - *`content_words` keeps what carries meaning and drops the words a reader can supply.*
  - Method `.test_common_words_are_dropped()`
  - Method `.test_a_question_drops_its_question_words()`
  - Method `.test_no_word_yields_no_content()`
- `class LexiconTests` - *The vocabulary is built from the texts, and expansion reads a payload back through it.*
  - Method `.test_expansion_restores_the_written_words()`
  - Method `.test_the_shortest_spelling_wins()`
  - Method `.test_an_unknown_letter_form_is_shown_as_it_is()`
  - Method `.test_a_word_of_vowels_only_is_not_a_vocabulary_entry()`

---

### [`tests/test_budget.py`](tests/test_budget.py)
> *Budget tests: the letter ceiling, its refusal of an impossible ceiling, and the child budget.*

**Size**: `37` lines (`1296` bytes)

**Classes:**
- `class BudgetTests` - *A budget is a ceiling in letters and the depth it belongs to.*
  - Method `.test_a_script_at_the_ceiling_fits()`
  - Method `.test_one_letter_over_the_ceiling_does_not_fit()`
  - Method `.test_room_is_what_one_glyph_leaves()`
  - Method `.test_a_child_gets_half_the_ceiling_at_the_next_depth()`
  - Method `.test_a_child_never_falls_below_the_floor()`
  - Method `.test_a_ceiling_below_one_letter_is_refused()`

---

### [`tests/test_cli.py`](tests/test_cli.py)
> *CLI tests: the two commands, the flags, exit codes and the What/Why/Fix reports.*

**Size**: `137` lines (`5597` bytes)

**Classes:**
- `class AskTests` - *`ask` answers from a file, from standard input, or from nothing.*
  - Method `.test_demo_answers_and_exits_zero()`
  - Method `.test_demo_prints_the_recursion_trace_before_the_answer()`
  - Method `.test_context_comes_from_a_file()`
  - Method `.test_context_comes_from_standard_input()`
  - Method `.test_script_mode_prints_the_letters_only()`
  - Method `.test_json_mode_reports_the_whole_answer()`
  - Method `.test_an_unanswerable_question_exits_one_with_a_report()`
  - Method `.test_json_reports_an_unanswerable_question_and_exits_one()`
- `class UsageTests` - *Usage misuse exits 2 with a Why and a Fix; help and version exit 0.*
  - Method `.test_help_prints_usage_and_exits_zero()`
  - Method `.test_short_help_is_the_same()`
  - Method `.test_version_prints_the_version_and_exits_zero()`
  - Method `.test_no_command_is_a_usage_error()`
  - Method `.test_ask_without_a_question_is_a_usage_error()`
  - Method `.test_an_unknown_command_is_refused()`
  - Method `.test_an_unknown_option_is_refused()`
  - Method `.test_a_flag_without_its_value_is_refused()`
  - Method `.test_a_budget_that_is_not_a_number_is_refused()`
  - Method `.test_a_budget_below_one_is_refused()`
  - Method `.test_a_missing_context_file_is_a_usage_error()`

**Functions:**
- `def run_cli(argv, stdin_text)` - *Run main() over in-memory streams; returns (exit code, stdout, stderr).*
- `def write_context(text)` - *A temporary context file on disk, cleaned up by the calling test.*

---

### [`tests/test_code_understanding.py`](tests/test_code_understanding.py)
> *Code understanding tests: Python source becomes meaningful sentences.*

**Size**: `71` lines (`2486` bytes)

**Classes:**
- `class ExtractTests` - *The AST reader finds the elements a question can ask about.*
  - Method `.test_functions_classes_and_imports_are_found()`
  - Method `.test_a_function_carries_its_signature_and_docstring()`
  - Method `.test_a_syntax_error_yields_no_elements()`
  - Method `.test_code_to_sentences_labels_each_kind()`
- `class DetectionTests` - *Code is recognized by strong line-leading markers, not by prose.*
  - Method `.test_python_source_is_code()`
  - Method `.test_natural_language_is_not_code()`
  - Method `.test_an_indented_definition_is_still_code()`

---

### [`tests/test_formats.py`](tests/test_formats.py)
> *Format parser tests: CSV and JSON contexts become sentences the engine can read.*

**Size**: `80` lines (`3193` bytes)

**Classes:**
- `class ParserTests` - *Each format keeps the values a question can match.*
  - Method `.test_csv_rows_become_sentences()`
  - Method `.test_json_keeps_keys_and_numbers()`
  - Method `.test_invalid_json_is_empty()`
  - Method `.test_auto_detects_json_csv_and_text()`
  - Method `.test_an_explicit_format_bypasses_detection()`
- `class FormatAskTests` - *Lacon.ask uses the parsers by default and exposes the format override.*
  - Method `.test_a_csv_context_answers_the_question()`
  - Method `.test_a_json_context_answers_the_question()`
  - Method `.test_text_format_reads_json_literally()`
- `class TreeBudgetTests` - *A tree-wide budget stops expansion instead of visiting every node.*
  - Method `.test_a_tree_budget_reduces_the_visited_nodes()`

---

### [`tests/test_performance.py`](tests/test_performance.py)
> *Performance benchmark tests: ensure speed budgets are met and measure regressions.*

**Size**: `223` lines (`9191` bytes)

**Classes:**
- `class PerformanceTests` - *Speed budgets: every operation must complete within its budget.*
  - Method `.test_ask_cold_speed()` - *A single ask on 200 sentences completes within 100ms cold.*
  - Method `.test_ask_warm_speed()` - *A repeated ask on same context completes within 5ms warm.*
  - Method `.test_alphabet_skeleton_speed()` - *skeleton on 1000 words completes within 200ms.*
  - Method `.test_lexicon_speed()` - *lexicon on 1000 words completes within 100ms.*
  - Method `.test_thinker_rank_speed()` - *Thinker.rank on 500 sentences completes within 600ms.*
  - Method `.test_partition_speed()` - *partition on 10000 items completes within 10ms.*
  - Method `.test_full_pipeline_100_asks()` - *100 asks on 100-sentence context completes within 2s.*
- `class CodeUnderstandingTests` - *Tests for code understanding: functions, classes, identifiers.*
  - Method `.setUp()`
  - Method `.test_code_context_parsed()` - *Code context is now parsed with AST and answers code questions.*
- `class EdgeCaseTests` - *Edge cases and stress tests.*
  - Method `.test_very_long_context()` - *Context with 1000 sentences handled within depth cap.*
  - Method `.test_many_questions_same_context()` - *Many different questions on same context reuse cache.*
  - Method `.test_unicode_content()` - *Unicode content handled gracefully.*
  - Method `.test_empty_and_whitespace()` - *Empty and whitespace-only contexts handled.*
  - Method `.test_budget_zero_refused()` - *Budget of zero is refused at ask time.*
  - Method `.test_negative_budget_refused()` - *Negative budget is refused.*
  - Method `.test_script_round_trip_many()` - *Many random scripts parse and render correctly.*
  - Method `.test_answer_text_consistency()` - *answer_text returns consistent results.*
  - Method `.test_expand_unknown_returns_original()` - *expand returns the skeleton when word unknown.*
  - Method `.test_skeleton_preserves_digits()` - *skeleton preserves digits (digits kept adjacent to letters).*
  - Method `.test_content_words_filters_stopwords()` - *content_words filters common stopwords.*
  - Method `.test_lexicon_picks_shortest()` - *lexicon picks shortest spelling for same skeleton.*

**Functions:**
- `def test_snake_case_in_question(self)` - *snake_case identifiers in question are now parsed from code.*

---

### [`tests/test_rlm.py`](tests/test_rlm.py)
> *RLM tests: the recursive engine - what it answers, when it splits, and what it never exceeds.*

**Size**: `106` lines (`4431` bytes)

**Classes:**
- `class SentenceTests` - *A context is a list of sentences, one per line or sentence mark.*
  - Method `.test_lines_and_marks_both_end_a_sentence()`
  - Method `.test_an_empty_context_holds_nothing()`
- `class PartitionTests` - *Splitting is contiguous, even, and never produces an empty chunk.*
  - Method `.test_even_lengths_split_evenly()`
  - Method `.test_an_odd_length_gives_the_extra_to_the_first_chunks()`
  - Method `.test_more_parts_than_items_keeps_one_chunk_per_item()`
  - Method `.test_nothing_splits_into_nothing()`
- `class AskTests` - *One question is answered from the context, and the letters never exceed the budget.*
  - Method `.test_a_short_context_is_answered_in_one_thought()`
  - Method `.test_a_long_context_is_split_and_merged()`
  - Method `.test_the_thought_obeys_every_budget()`
  - Method `.test_a_budget_of_one_letter_can_only_be_unknown()`
  - Method `.test_a_context_that_answers_nothing_is_unknown()`
  - Method `.test_no_context_is_unknown()`
  - Method `.test_recursion_stops_at_the_depth_cap()`
  - Method `.test_the_script_is_a_lacon_script()`
- `class AnswerTests` - *An answer knows whether it found evidence, and nothing else.*
  - Method `.test_an_answered_script_is_known()`
  - Method `.test_an_empty_answer_is_not_known()`

---

### [`tests/test_thinker.py`](tests/test_thinker.py)
> *Thinker tests: ranking by shared meaning, and the cheapest thought that still answers.*

**Size**: `69` lines (`2958` bytes)

**Classes:**
- `class RankTests` - *The sentence that shares the most meaning with the question comes first.*
  - Method `.test_the_best_match_is_ranked_first()`
  - Method `.test_an_unrelated_sentence_scores_nothing()`
  - Method `.test_overlap_counts_meaning_carrying_words_only()`
  - Method `.test_a_shorter_context_scores_the_same_sentence()`
- `class ThinkTests` - *The thought is as small as the budget allows, and never larger than it.*
  - Method `.test_a_generous_budget_keeps_the_evidence_and_the_step()`
  - Method `.test_a_tight_budget_drops_the_support_first()`
  - Method `.test_a_tighter_budget_shortens_the_answer()`
  - Method `.test_a_budget_that_cannot_hold_a_word_is_unknown()`
  - Method `.test_evidence_that_matches_nothing_is_unknown()`
  - Method `.test_no_evidence_is_unknown()`
  - Method `.test_every_budget_holds_the_thought_it_produced()`

---

### [`tests/test_thought.py`](tests/test_thought.py)
> *Thought tests: the eight glyphs, the one-token script form, and reading a script back.*

**Size**: `57` lines (`2240` bytes)

**Classes:**
- `class GlyphTests` - *The alphabet is exactly eight glyphs, and each one is a single act of reasoning.*
  - Method `.test_there_are_eight_glyphs()`
  - Method `.test_a_thought_costs_one_glyph()`
- `class RenderTests` - *Rendering is the inverse of parsing, and refuses a glyph outside the alphabet.*
  - Method `.test_render_and_parse_round_trip()`
  - Method `.test_an_unknown_glyph_is_refused_when_rendered()`
  - Method `.test_an_unknown_glyph_is_refused_when_parsed()`
  - Method `.test_a_reference_that_is_not_a_number_is_refused()`
- `class AnswerTests` - *The answer is the last answer glyph, read back through the vocabulary.*
  - Method `.test_the_answer_is_expanded_through_the_lexicon()`
  - Method `.test_an_unknown_thought_speaks_nothing()`

---

"""Lacon's command line: ask one question, or run the built-in demo.

Exit codes are part of the contract: 0 answered, 1 no evidence answered it, 2 a usage or file
error. Every report keeps the What/Why/Fix shape, so a caller never sees a Python traceback, and
`--help` prints usage without writing anything.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .rlm import Answer, Lacon

HELP = """usage: lacon ask "QUESTION" [--context FILE] [--budget N] [--script] [--json] [--trace]
       lacon demo [--budget N]

Lacon answers a question from a context, thinking in as few letters as possible: each thought is
one of eight glyphs (`?` unknown, `+` claim, `-` contrast, `<` because, `>` therefore, `*` split,
`=` merge, `!` answer) followed by a payload written without vowels. A long context is split and
answered recursively, and every thought obeys the letter budget.

positional arguments:
  ask QUESTION       the question to answer
  demo               run the built-in example, so the engine shows itself in seconds

options:
  --context FILE     the context to answer from; `-` reads it from standard input
  --budget N         the letter ceiling for one thought (default 64, at least 1)
  --script           print the letters Lacon thought in, instead of the answer
  --json             print answer, script, depth, nodes and budget as one JSON object
  --trace            print the recursion shape before the answer
  -h, --help         show this help and exit
  --version          show the version and exit

exit codes: 0 answered, 1 no answer in the context, 2 usage or file error
"""

DEMO_QUESTION = "What keeps the bridge from rust?"
DEMO_CONTEXT = ("The bridge is painted every spring.\n"
                "Paint keeps steel from rust.\n"
                "Rust is iron oxide.\n"
                "The painter uses a long brush.\n"
                "Salt air speeds rust on the coast.\n"
                "The bridge spans the river in three arches.\n")


class CliError(Exception):
    """A usage or file failure, rendered with the same What/Why/Fix shape as an answer refusal."""

    def __init__(self, message: str, why: str, fix: str) -> None:
        super().__init__(message)
        self.message = message
        self.why = why
        self.fix = fix


def main(argv=None, stdin=None, stdout=None, stderr=None) -> int:
    """Run the command line; every argument defaults to the matching process stream."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    try:
        return _dispatch(arguments, stdin, stdout, stderr)
    except CliError as error:
        stderr.write(f"lacon: error: {error.message}\n"
                     f"  Why: {error.why}\n"
                     f"  Fix: {error.fix}\n")
        return 2
    except Exception as error:
        _report_internal(error, stderr)
        return 1


def _report_internal(error: Exception, stderr) -> None:
    """Last-resort report: a host failure is still explained, and never shown as a traceback."""
    stderr.write("lacon: internal error: the engine failed unexpectedly\n"
                 f"  Why: {type(error).__name__}: {error}\n"
                 "  Fix: this is a lacon bug; report the question and this message\n")


def _dispatch(arguments: List[str], stdin, stdout, stderr) -> int:
    """Route the arguments to `ask` or `demo`."""
    if not arguments:
        raise CliError("no command given",
                       "lacon answers a question or runs its demo, and neither was named",
                       'write lacon ask "what keeps the bridge from rust?" --context notes.txt')
    if arguments[0] in ("-h", "--help"):
        stdout.write(HELP)
        return 0
    if arguments[0] == "--version":
        stdout.write(f"lacon {__version__}\n")
        return 0
    if arguments[0] == "demo":
        return _run(DEMO_QUESTION, DEMO_CONTEXT, _options(arguments[1:]), stdout, stderr)
    if arguments[0] == "ask":
        rest = arguments[1:]
        if not rest or rest[0].startswith("-"):
            raise CliError("'ask' needs a question",
                           "the question text comes right after 'ask', and nothing followed",
                           'write lacon ask "what keeps the bridge from rust?"')
        options = _options(rest[1:])
        return _run(rest[0], _context(options, stdin), options, stdout, stderr)
    raise CliError(f"unknown command '{arguments[0]}'",
                   "this command is not part of the lacon command line",
                   "run lacon --help to see the available commands")


def _options(arguments: List[str]) -> dict:
    """Parse the flags of one command into a plain option mapping."""
    options = {"context": None, "budget": 64, "script": False, "json": False, "trace": False}
    index = 0
    while index < len(arguments):
        flag = arguments[index]
        if flag in ("--script", "--json", "--trace"):
            options[flag[2:]] = True
        elif flag in ("--context", "--budget"):
            if index + 1 >= len(arguments):
                raise CliError(f"option '{flag}' needs a value",
                               f"'{flag}' is followed by its value, and nothing followed",
                               f'write {flag} {"FILE" if flag == "--context" else "64"}')
            options[flag[2:]] = arguments[index + 1]
            index += 1
        else:
            raise CliError(f"unknown option '{flag}'",
                           "this option is not part of the lacon command line",
                           "run lacon --help to see the available options")
        index += 1
    options["budget"] = _budget(options["budget"])
    return options


def _budget(value) -> int:
    """The letter ceiling as a positive integer, or a usage error."""
    try:
        limit = int(value)
    except (TypeError, ValueError):
        raise CliError(f"--budget '{value}' is not a number",
                       "the budget is a whole number of letters",
                       "write --budget 64, or a smaller ceiling such as --budget 16") from None
    if limit < 1:
        raise CliError(f"--budget {limit} leaves no room for a thought",
                       "even the unknown glyph needs one letter",
                       "write --budget 64, or any number of letters at least 1")
    return limit


def _context(options: dict, stdin) -> str:
    """The context text: from a file, from standard input for `-`, or empty when unnamed."""
    source = options["context"]
    if source is None:
        return ""
    if source == "-":
        return stdin.read()
    try:
        return Path(source).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise CliError(f"cannot read context '{source}'",
                       "the file does not exist at this path",
                       "check the spelling, or pass - to read the context from standard input") from None
    except UnicodeDecodeError:
        raise CliError(f"cannot read context '{source}'",
                       "the file is not valid UTF-8 text",
                       "save the file as UTF-8, then ask again") from None
    except OSError as error:
        raise CliError(f"cannot read context '{source}'",
                       f"the operating system refused the read: {error.strerror}",
                       "check the path and its permissions") from None


def _run(question: str, context: str, options: dict, stdout, stderr) -> int:
    """Answer one question and report it in the requested form."""
    answer = Lacon().ask(question, context, options["budget"])
    if options["json"]:
        stdout.write(json.dumps({"answer": answer.answer, "script": answer.script,
                                 "budget": answer.budget, "depth": answer.depth,
                                 "nodes": answer.nodes, "known": answer.known},
                                ensure_ascii=False) + "\n")
        return 0 if answer.known else 1
    if not answer.known:
        ceiling = f"{answer.budget} letter" + ("" if answer.budget == 1 else "s")
        stderr.write(f"lacon: no answer within {ceiling}\n"
                     "  Why: the ceiling left no room for an answer word, or no sentence in the "
                     "context matched the question\n"
                     f"  Fix: add sentences about the question, or raise --budget (now "
                     f"{answer.budget}) until the answer fits\n")
        return 1
    if options["trace"]:
        stdout.write(_trace(answer))
    stdout.write((answer.script if options["script"] else answer.answer) + "\n")
    return 0


def _trace(answer: Answer) -> str:
    """The one-line recursion report: what the letters bought, and how deep it split."""
    return (f"[lacon] {len(answer.script)} of {answer.budget} letters, depth {answer.depth}, "
            f"{answer.nodes} node(s)\n")
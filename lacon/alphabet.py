"""The Lacon alphabet: vowelless letter payloads, and the vocabulary that expands them back.

Lacon's whole idea is that thinking costs as few letters as possible, so a payload keeps only the
letters that carry meaning: vowels and punctuation go, and common words the reader can supply go
too. `skeleton` is the letter form of any text, `content_words` keeps the meaning-carrying part of
it, and `expand` reads a payload back through the vocabulary of the question and its context, so a
reader that knows both reads the thought exactly as it was written.
"""

import re
from typing import Dict, List

PAYLOAD_SEPARATOR = "."
VOWELS = frozenset("aeiou")
STOPWORDS = frozenset({
    "th", "n", "nd", "frm", "wth", "fr", "t", "b", "s", "r", "by", "at", "on", "in", "f", "d",
    "ds", "ws", "wr", "bn", "bt", "hs", "hv", "cn", "wll", "wht", "wh", "hw", "wy", "whn", "whr",
    "whch", "whs", "ths", "tht", "thr", "thy", "it", "its", "as", "if", "or", "nt",
})
_WORD = re.compile(r"[a-z0-9]+")


def skeleton(text: str) -> str:
    """The letter form of one text: lowercase words with vowels and punctuation removed."""
    return PAYLOAD_SEPARATOR.join(_stem(word) for word in _WORD.findall(text.lower()) if _stem(word))


def content_words(text: str) -> List[str]:
    """The skeletons that carry meaning: vowels, punctuation and common words removed."""
    return [word for word in skeleton(text).split(PAYLOAD_SEPARATOR)
            if word and word not in STOPWORDS]


def lexicon(*texts: str) -> Dict[str, str]:
    """The vocabulary of the given texts, mapping each letter form to its shortest spelling."""
    words: Dict[str, str] = {}
    for text in texts:
        for word in _WORD.findall(text.lower()):
            stem = _stem(word)
            if not stem:
                continue
            best = words.get(stem)
            if best is None or (len(word), word) < (len(best), best):
                words[stem] = word
    return words


def expand(payload: str, words: Dict[str, str]) -> str:
    """The readable text behind a payload; a letter form no word matches is shown as it is."""
    return " ".join(words.get(part, part)
                    for part in payload.split(PAYLOAD_SEPARATOR) if part)


def _stem(word: str) -> str:
    """One word without its vowels: `bridge` becomes `brdg`, a vowel-only word becomes empty."""
    return "".join(char for char in word if char not in VOWELS)
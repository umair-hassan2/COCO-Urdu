"""Urdu text normalization and cheap automatic sanity checks.

Catches what reviewers caught by eye in v1: non-words ("ایلیف"), misspellings ("ابزار"),
untranslated English, empty output, wrong script.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path

ARABIC_BLOCK = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
LATIN = re.compile(r"[A-Za-z]")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
DIGITS = re.compile(r"[0-9۰-۹٠-٩]")
# Urdu punctuation: ۔ ، ؟ ؛ plus ASCII
PUNCT = re.compile(r"[\s\.\,\!\?\;\:\-\"\'\(\)\[\]\{\}«»،۔؟؛…]+")
DIACRITICS = re.compile(r"[ً-ْٰٓ-ٕ]")

# Arabic-presentation and look-alike normalizations commonly needed for Urdu.
# Keys must be single characters -- str.maketrans rejects sequences. NFC runs first in
# normalize(), so heh goal + hamza above is already composed to U+06C2 by the time we get here.
_CHAR_MAP = str.maketrans({
    "ي": "ی",  # Arabic yeh -> Farsi yeh
    "ك": "ک",  # Arabic kaf -> keheh
    "ۀ": "ہ",
    "ە": "ہ",
    "ۂ": "ہ",  # heh goal with hamza above (NFC of U+06C1 U+0654)
    "أ": "ا", "إ": "ا", "ٱ": "ا",
    "‌": "", "‍": "", "‏": "", "‎": "", "﻿": "",
})


def normalize(text: str, strip_diacritics: bool = True) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = text.translate(_CHAR_MAP)
    if strip_diacritics:
        text = DIACRITICS.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return [t for t in PUNCT.split(normalize(text)) if t]


def script_profile(text: str) -> dict:
    n = max(1, len(text))
    return {
        "arabic_ratio": len(ARABIC_BLOCK.findall(text)) / n,
        "latin_ratio": len(LATIN.findall(text)) / n,
        "devanagari_ratio": len(DEVANAGARI.findall(text)) / n,
    }


class Lexicon:
    """Word list for non-word detection. Build with scripts/build_lexicon.py (fineweb-2 urd_Arab)."""

    def __init__(self, words: set[str]):
        self.words = words

    @classmethod
    def load(cls, path: str | Path) -> "Lexicon":
        words = {normalize(w) for w in Path(path).read_text(encoding="utf-8").splitlines() if w.strip()}
        return cls(words)

    def oov(self, text: str) -> list[str]:
        toks = [t for t in tokenize(text) if not DIGITS.fullmatch(t) and not LATIN.search(t)]
        return [t for t in toks if t not in self.words]

    def oov_rate(self, text: str) -> float:
        toks = tokenize(text)
        return len(self.oov(text)) / len(toks) if toks else 0.0


def caption_checks(en: str, ur: str, lexicon: Lexicon | None = None) -> dict:
    """Flags for one (English, Urdu) pair. All boolean/numeric so they aggregate trivially."""
    ur_n = normalize(ur)
    prof = script_profile(ur_n)
    en_len, ur_len = max(1, len(en.split())), len(tokenize(ur_n))
    out = {
        "empty": ur_len == 0,
        "latin_ratio": prof["latin_ratio"],
        "has_untranslated_english": prof["latin_ratio"] > 0.15,
        "wrong_script": prof["arabic_ratio"] < 0.5 and ur_len > 0,
        "len_ratio": ur_len / en_len,
        "too_short": ur_len / en_len < 0.5,
        "too_long": ur_len / en_len > 2.5,
        "repeated_trigram": _has_repeated_ngram(tokenize(ur_n), 3),
    }
    if lexicon is not None:
        oov = lexicon.oov(ur_n)
        out["oov_tokens"] = oov
        out["oov_rate"] = len(oov) / ur_len if ur_len else 0.0
        out["has_oov"] = bool(oov)
    return out


def _has_repeated_ngram(toks: list[str], n: int) -> bool:
    grams = Counter(tuple(toks[i:i + n]) for i in range(len(toks) - n + 1))
    return any(c > 1 for c in grams.values())

"""Transliterate foreign-script fragments in contaminated Urdu back to Perso-Arabic.

The v2 translator substitutes phonetically equivalent subwords from other scripts mid-word
(docs/FINDINGS.md Finding 1). The maps here cover every character that actually occurs in
data/translations/gemma27b.parquet, so a proposal can be pre-filled for human review. They are a
starting point for `scripts/14_build_repair_map.py`, never an automatic rewrite: transliteration
recovers the sound, not the conventional Urdu spelling of a loanword.
"""
from __future__ import annotations

import re

from .urdu_text import URDU_OK, script_of

# --- Devanagari -------------------------------------------------------------------------------
# Standard Hindi->Urdu correspondences. Vowel signs that Urdu does not write become "".
_DEVA = {
    "क": "ک", "ख": "کھ", "ग": "گ", "घ": "گھ", "ङ": "ن",
    "च": "چ", "छ": "چھ", "ज": "ج", "झ": "جھ", "ञ": "ن",
    "ट": "ٹ", "ठ": "ٹھ", "ड": "ڈ", "ढ": "ڈھ", "ण": "ن",
    "त": "ت", "थ": "تھ", "द": "د", "ध": "دھ", "न": "ن",
    "प": "پ", "फ": "پھ", "ब": "ب", "भ": "بھ", "म": "م",
    "य": "ی", "र": "ر", "ल": "ل", "व": "و", "ळ": "ل",
    "श": "ش", "ष": "ش", "स": "س", "ह": "ہ",
    "क़": "ق", "ख़": "خ", "ग़": "غ", "ज़": "ز", "ड़": "ڑ", "ढ़": "ڑھ", "फ़": "ف",
    "अ": "ا", "आ": "آ", "इ": "ا", "ई": "ای", "उ": "ا", "ऊ": "او",
    "ऋ": "ر", "ए": "ا", "ऐ": "ای", "ओ": "او", "औ": "او",
    "ा": "ا", "ि": "", "ी": "ی", "ु": "", "ू": "و", "ृ": "ر",
    "े": "ی", "ै": "ی", "ो": "و", "ौ": "و", "ॉ": "ا",
    "ं": "ن", "ँ": "ں", "ः": "", "्": "", "़": "", "।": "۔",
}
# Word-final forms: Urdu writes the e/ai vowels as ے at the end of a word.
_DEVA_FINAL = {"े": "ے", "ै": "ے", "ं": "ں"}

# --- Katakana / hiragana ----------------------------------------------------------------------
_KANA = {
    "ビ": "بی", "ー": "", "ン": "ن", "ズ": "ز", "ウ": "و", "ド": "ڈ", "カ": "کا",
    "テ": "ٹی", "フ": "ف", "ィ": "ی", "ス": "س", "ム": "م", "ル": "ل", "ワ": "وا",
    "ク": "ک", "レ": "ری", "ホ": "ہو", "り": "ری",
}

# --- Cyrillic (incl. the Ukrainian letters the model reaches for) -------------------------------
_CYRL = {
    "а": "ا", "б": "ب", "в": "و", "г": "گ", "д": "د", "е": "ی", "є": "ے", "ж": "ژ",
    "з": "ز", "и": "ی", "і": "ی", "ї": "ی", "й": "ی", "к": "ک", "л": "ل", "м": "م",
    "н": "ن", "о": "و", "п": "پ", "р": "ر", "с": "س", "т": "ت", "у": "و", "ф": "ف",
    "х": "خ", "ц": "ص", "ч": "چ", "ь": "", "ю": "یو", "я": "یا",
}

# --- Brahmic siblings: same phonology, different glyphs ------------------------------------------
_BENG = {
    "ক": "ک", "খ": "کھ", "গ": "گ", "ঘ": "گھ", "চ": "چ", "ছ": "چھ", "জ": "ج", "ট": "ٹ",
    "ঠ": "ٹھ", "ড": "ڈ", "ড়": "ڑ", "ত": "ت", "থ": "تھ", "দ": "د", "ধ": "دھ", "ন": "ن",
    "প": "پ", "ফ": "پھ", "ব": "ب", "ম": "م", "য": "ی", "র": "ر", "ল": "ل", "শ": "ش",
    "স": "س", "হ": "ہ", "ই": "ا", "আ": "آ", "অ": "ا", "উ": "ا",
    "া": "ا", "ি": "", "ী": "ی", "ু": "", "ূ": "و", "ে": "ی", "ো": "و",
    "ং": "ن", "্": "", "়": "",
}
_GUJR = {
    "ક": "ک", "ખ": "کھ", "ગ": "گ", "ઘ": "گھ", "ચ": "چ", "જ": "ج", "ટ": "ٹ", "ડ": "ڈ",
    "ત": "ت", "થ": "تھ", "દ": "د", "ધ": "دھ", "ન": "ن", "પ": "پ", "બ": "ب", "મ": "م",
    "ય": "ی", "ર": "ر", "લ": "ل", "વ": "و", "શ": "ش", "સ": "س", "હ": "ہ",
    "અ": "ا", "આ": "آ", "એ": "ا", "ઇ": "ا",
    "ા": "ا", "િ": "", "ી": "ی", "ુ": "", "ૂ": "و", "ે": "ی", "ો": "و", "ં": "ن", "્": "",
}
_KNDA = {
    "ಕ": "ک", "ಖ": "کھ", "ಗ": "گ", "ಚ": "چ", "ಜ": "ج", "ಟ": "ٹ", "ಡ": "ڈ", "ತ": "ت",
    "ದ": "د", "ನ": "ن", "ಪ": "پ", "ಬ": "ب", "ಮ": "م", "ಯ": "ی", "ರ": "ر", "ಲ": "ل",
    "ವ": "و", "ಶ": "ش", "ಸ": "س", "ಹ": "ہ",
    "ಾ": "ا", "ಿ": "", "ೀ": "ی", "ು": "", "ೂ": "و", "ೆ": "ی", "ೋ": "و", "ಂ": "ن", "್": "",
}
_MLYM = {
    "ക": "ک", "ഗ": "گ", "ജ": "ج", "ട": "ٹ", "ഡ": "ڈ", "ത": "ت", "ദ": "د", "ന": "ن",
    "പ": "پ", "ബ": "ب", "മ": "م", "യ": "ی", "ര": "ر", "ർ": "ر", "ല": "ل", "വ": "و",
    "ശ": "ش", "സ": "س", "ഹ": "ہ",
    "ാ": "ا", "ി": "", "ീ": "ی", "ു": "", "ൂ": "و", "േ": "ی", "ൈ": "ی", "ൗ": "و", "്": "",
}
_TAML = {"க": "ک", "ச": "چ", "ட": "ٹ", "த": "ت", "ப": "پ", "ம": "م", "ய": "ی", "ர": "ر",
         "ல": "ل", "வ": "و", "ஸ": "س", "ா": "ا", "ி": "", "ீ": "ی", "ு": "", "ூ": "و", "்": ""}
_TELU = {"డ": "ڈ", "ం": "ن", "ా": "ا", "ి": "", "ు": "", "్": ""}
_GURU = {"ੇ": "ی", "ਾ": "ا", "ਿ": "", "ੀ": "ی", "ੁ": "", "ੂ": "و"}

_MAPS = {}
for _m in (_DEVA, _KANA, _CYRL, _BENG, _GUJR, _KNDA, _MLYM, _TAML, _TELU, _GURU):
    _MAPS.update(_m)

# Scripts with no sound-level mapping to Urdu: logographic, or a syllabary whose reading depends
# on the word. Forms containing these need a human translation, not a transliteration.
SEMANTIC_SCRIPTS = {"Han", "Hangul", "Hebrew", "Thai", "Other"}

# Brahmic scripts write a geminate as C + virama + C; Urdu writes one letter (with tashdeed).
# Matching on the virama matters: गगन is two distinct ga's, not a geminate.
_VIRAMAS = "\u094D\u09CD\u0ACD\u0CCD\u0D4D\u0BCD\u0C4D\u0A4D"
_GEMINATE = re.compile(rf"(.)[{_VIRAMAS}]\1")


def transliterate(form: str) -> str:
    """Best-effort Perso-Arabic rendering of a contaminated word-form.

    Recovers the sound. The result still needs review: Urdu spells loanwords by convention, not
    phonetically ('ماؤنڈ', not the letter-by-letter 'موند').
    """
    form = _GEMINATE.sub(r"\1", form)
    out, chars = [], list(form)
    for i, ch in enumerate(chars):
        if URDU_OK.match(ch):
            out.append(ch)
            continue
        final = i == len(chars) - 1 or all(not c.strip() for c in chars[i + 1:])
        if final and ch in _DEVA_FINAL:
            out.append(_DEVA_FINAL[ch])
        else:
            out.append(_MAPS.get(ch, ch))
    return "".join(out)


def classify(form: str) -> str:
    """Repair class for a contaminated form: how much human judgement the fix needs."""
    scripts = {script_of(c) for c in form if not URDU_OK.match(c)}
    if scripts & SEMANTIC_SCRIPTS:
        return "needs-translation"
    proposal = transliterate(form)
    if any(not URDU_OK.match(c) for c in proposal):
        return "needs-translation"
    # A token with no Urdu letters at all is a whole word in another language: the transliteration
    # gives its sound, but the Urdu word for the concept is usually something else entirely.
    from .urdu_text import ARABIC_BLOCK
    return "auto" if ARABIC_BLOCK.search(form) else "needs-review"

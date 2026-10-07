"""Shared translation prompt for LLM translators (API and vLLM). Keep identical across systems for a fair comparison."""
import re

SYSTEM_PROMPT = (
    "You are a professional English-to-Urdu translator. Translate the image caption into natural, fluent Urdu "
    "in Perso-Arabic script.\n"
    "Rules: one sentence; preserve every detail and nothing more; keep gender and number agreement correct; "
    "use common Urdu words (not Hindi/Sanskrit-derived vocabulary, not transliterated English unless the word is "
    "standard in Urdu, e.g. ٹرین, بس, پیزا); numerals as digits; end with ۔ ; output ONLY the Urdu sentence."
)

# 5 hand-written examples covering plurals, gender, spatial relations, food, and numerals
FEW_SHOT = [
    {"role": "user", "content": "A man riding a wave on top of a surfboard."},
    {"role": "assistant", "content": "ایک آدمی سرف بورڈ پر لہر کی سواری کر رہا ہے۔"},
    {"role": "user", "content": "Two women sitting at a table eating pizza."},
    {"role": "assistant", "content": "دو عورتیں میز پر بیٹھی پیزا کھا رہی ہیں۔"},
    {"role": "user", "content": "A black cat lying on a red couch next to a window."},
    {"role": "assistant", "content": "ایک کالی بلی کھڑکی کے پاس سرخ صوفے پر لیٹی ہوئی ہے۔"},
    {"role": "user", "content": "Several boats docked in a harbor under a cloudy sky."},
    {"role": "assistant", "content": "بادلوں بھرے آسمان تلے بندرگاہ میں کئی کشتیاں لنگر انداز ہیں۔"},
    {"role": "user", "content": "A kitchen with 3 wooden chairs and a white refrigerator."},
    {"role": "assistant", "content": "ایک باورچی خانہ جس میں 3 لکڑی کی کرسیاں اور ایک سفید فریج ہے۔"},
]

_QUOTES = re.compile(r'^["“”\'«»\s]+|["“”\'«»\s]+$')


def parse_translation(text: str) -> str:
    """Take the first non-empty line, strip quotes/labels the model might add."""
    for line in (text or "").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^(Urdu|اردو)\s*[:：]\s*", "", line, flags=re.I)
        return _QUOTES.sub("", line)
    return ""

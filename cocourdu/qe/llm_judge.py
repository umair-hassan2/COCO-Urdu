"""LLM-as-judge QE through any OpenAI-compatible endpoint (OpenAI, Gemini OpenAI-compat, local vLLM).

Scores adequacy 0-100 of an Urdu caption against the English source (and optionally the image URL).
"""
from __future__ import annotations

import json
import re

JUDGE_PROMPT = """You are a professional English-Urdu translator grading machine translations of image captions.
Rate the Urdu caption's ADEQUACY (0-100): does it convey exactly the meaning of the English caption,
with nothing added, omitted, or mistranslated? Also rate FLUENCY (0-100): is it natural, grammatical Urdu
with correct spelling and gender/number agreement? Return only JSON: {{"adequacy": int, "fluency": int, "errors": [..]}}
where errors is a subset of ["mistranslation","omission","addition","agreement","spelling","word_order","untranslated"].

English: {en}
Urdu: {ur}"""


class LLMJudge:
    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None, with_image: bool = False):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model, self.with_image = model, with_image

    def judge(self, en: str, ur: str, image_url: str | None = None) -> dict:
        content = [{"type": "text", "text": JUDGE_PROMPT.format(en=en, ur=ur)}]
        if self.with_image and image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        resp = self.client.chat.completions.create(model=self.model, temperature=0, messages=[{"role": "user", "content": content}])
        txt = resp.choices[0].message.content or ""
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            return json.loads(m.group(0)) if m else {"adequacy": None, "fluency": None, "errors": [], "raw": txt}
        except json.JSONDecodeError:
            return {"adequacy": None, "fluency": None, "errors": [], "raw": txt}

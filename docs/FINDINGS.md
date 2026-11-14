# v2 findings worth putting in the paper

A running log of things the v2 run turned up that are results in their own right, not just
build notes. Each entry states what is broken, why, how much, and how it was measured, so it can be
lifted into the paper with the numbers intact. Build/status notes stay in `PROGRESS.md`.

---

## Corpus accounting

Four numbers describe the same dataset; state them once so they are not read as inconsistent.

| | count | why it differs |
|---|---|---|
| images | 63,549 | 58,549 train + 5,000 val |
| source caption rows | 317,921 | as published |
| captions translated | 317,829 | 92 rows share a `uid` and are de-duplicated before generation |
| **released corpus** | **317,549** | 280 refusal captions excluded (Finding 2) |

Mean 5.00 captions per image, range 5–7.

---

## Finding 1 — Cross-script token substitution in Gemma 3 27B (W4A16) Urdu output

**Date:** 2026-11-14 · **Affects:** `data/translations/gemma27b.parquet` (317,549 captions)
**Reproduce:** `uv run python scripts/13_script_contamination.py --translations data/translations/gemma27b.parquet --compare-v1`
(every table below is that script's output; it also writes a per-caption parquet with the offending code points)

### What is broken

The translator emits Urdu words in which one or more characters come from a **different writing
system** — Japanese katakana, Devanagari, Cyrillic, Bengali, Han, and nine others. The caption is
otherwise fluent, correct Urdu; a syllable inside a single word is written in the wrong script.

> ایک آدمی س**ноу** بورڈ کے ساتھ اور ایک آدمی ماسک کے ساتھ کھڑا ہے۔
> *(`سноу` = Urdu `س` + Cyrillic `ноу` — intended `سنو`, "snow")*

> ایک لڑکا پارک میں فرس**ビー** پھینک رہا ہے۔
> *(`فرسビー` = Urdu `فرس` + katakana `ビー` — intended `فرسبی`, "frisbee")*

### Why it happens

The substituted characters are **phonetically equivalent** to the Urdu characters they replace. The
model selects a subword token that encodes the right sound from the wrong script's inventory.

| emitted | intended | foreign fragment | phonetic value | gloss |
|---|---|---|---|---|
| `فرسビー` | `فرسبی` | katakana `ビー` | *bī* | frisbee |
| `سноу` | `سنو` | Cyrillic `ноу` | *nou* | snow |
| `سجاवट` | `سجاوٹ` | Devanagari `वट` | *vaṭ* | decoration |
| `ٹमाटर` | `ٹماٹر` | Devanagari `माटर` | *māṭar* | tomato |
| `دھकेल` | `دھکیل` | Devanagari `केल` | *kel* | push |
| `کشتियों` | `کشتیوں` | Devanagari `ियों` | *-iyõ* | boats (oblique pl.) |
| `سٹرोलर` | `سٹرولر` | Devanagari `लर` | *lar* | stroller |

Devanagari dominates the inflectional cases (`ियों`, `या`) — the oblique plural and perfective
endings Urdu and Hindi share phonologically but write differently. Katakana and Cyrillic dominate
the loanword cases, where the Urdu training data has few attestations of the word at all.

**Hypothesis, untested:** W4A16 quantization blurs the decision boundary between phonetically
adjacent subwords in a shared multilingual embedding space. Testing it needs one chunk re-run in
bf16 on the same prompts — a single 20K chunk is enough, and sampling is greedy, so the comparison
is exact. Until that is run, the finding stands on its own as a property of this checkpoint.

### How much

**6,686 of 317,549 captions (2.106%)** contain at least one foreign-script character: 6,784 token
occurrences over 391 distinct word-forms and 208 distinct characters.

| script | captions | % of corpus | characters |
|---|---|---|---|
| Japanese (katakana) | 4,425 | 1.393% | 9,030 |
| Devanagari | 1,375 | 0.433% | 4,573 |
| Cyrillic | 610 | 0.192% | 1,993 |
| Bengali | 92 | 0.029% | 482 |
| Han (CJK) | 81 | 0.026% | 187 |
| Gujarati | 62 | 0.020% | 124 |
| Kannada | 35 | 0.011% | 125 |
| Hangul | 16 | 0.005% | 19 |
| Malayalam | 9 | 0.003% | 20 |
| Tamil | 2 | 0.001% | 6 |
| Hebrew | 2 | 0.001% | 4 |
| Telugu | 1 | 0.000% | 2 |
| Thai | 1 | 0.000% | 3 |
| Gurmukhi | 1 | 0.000% | 1 |

Two shapes, in a 23:1 ratio. The denominator below is the **6,784 contaminated token
occurrences**, not the 317,549-caption corpus — as a share of all tokens in the corpus these are
0.163% and 0.007%.

| shape | occurrences | % of contaminated tokens | % of corpus tokens |
|---|---|---|---|
| Urdu word with an embedded foreign fragment (`فرسビー`) | 6,496 | 95.8% | 0.163% |
| token entirely in another language (`উল্লূ`, `মূর্তি`) | 288 | 4.2% | 0.007% |

All 391 forms were reviewed by hand and the repaired corpus is
`data/translations/gemma27b_repaired.parquet`: **2.104% → 0.000%**. The map, with a status and a
reason on every row, is `repairs/script_contamination_gemma27b.tsv`.

### It is lexically concentrated, not diffuse

Eight word-forms account for 80% of all occurrences; one accounts for 64%.

Shares are of the 6,784 contaminated token occurrences.

| # | form | count | % of contaminated tokens | cumulative |
|---|---|---|---|---|
| 1 | `فرسビー` | 4,315 | 63.6% | 63.6% |
| 2 | `سноу` | 499 | 7.4% | 71.0% |
| 3 | `سجاवट` | 195 | 2.9% | 73.8% |
| 4 | `دھकेल` | 154 | 2.3% | 76.1% |
| 5 | `کشتियों` | 128 | 1.9% | 78.0% |
| 6 | `মূর্তি` | 63 | 0.9% | 78.9% |
| 7 | `جیーンズ` | 49 | 0.7% | 79.6% |
| 8 | `उल्लू` | 47 | 0.7% | 80.3% |

Coverage thresholds: **top 8 forms → 80%**, top 37 → 90%, top 110 → 95%.

### It is triggered by specific source words, near-deterministically

Rate of contamination among captions containing each English word:

| EN word | captions | contaminated | rate |
|---|---|---|---|
| frisbee | 4,385 | 4,227 | **96.4%** |
| owl | 62 | 47 | **75.8%** |
| jeans | 167 | 50 | 29.9% |
| skirt | 167 | 35 | 21.0% |
| snowboard | 2,478 | 451 | 18.2% |
| tomato | 728 | 89 | 12.2% |
| statue | 855 | 72 | 8.4% |
| broccoli | 1,970 | 28 | 1.4% |
| ski | 8,598 | 96 | 1.1% |
| giraffe | 6,643 | 21 | 0.3% |

For "frisbee" the model has what amounts to a fixed wrong lexical entry: 96.4% of the 4,385
captions containing the word come out with `فرسビー` rather than the correct `فرسبی`. Decoding is greedy
(`SamplingParams(temperature=0)`, `scripts/03_translate_gemma_vllm.py:76`), so this is reproducible
rather than sampling noise — **re-running the same checkpoint reproduces the errors exactly.**

### Baseline: v1 SeamlessM4T does not do this

| system | affected captions | rate |
|---|---|---|
| Gemma 3 27B W4A16 (v2) | 6,686 | **2.106%** |
| SeamlessM4T (v1) | 0 | 0.000% |

SeamlessM4T produces **none** on the same 317,549 source captions: the defect arrives entirely
with the move to a quantized instruction-tuned LLM. This is the
quality dimension on which the new translator is strictly worse than the old one, and it is
invisible to every metric in the current QE set.

### Why the existing checks missed it

1. `wrong_script` in `cocourdu/urdu_text.py:caption_checks` tests `arabic_ratio < 0.5` over the
   whole caption. One or two stray characters in a 10-word sentence leave the ratio near 1.0, so
   the check reports 0.03% while the real rate is 2.106%. `caption_checks` now also returns
   `has_foreign_script` / `foreign_chars`, so `04_sanity_check.py` reports it from here on.
2. `has_untranslated_english` matches `[A-Za-z]` only, so non-Latin scripts pass through.
3. The Colab sanity report never ran `has_oov` at all — `data/lexicon/urdu_words.txt` lives on the
   Mac and was not on the artifacts repo until 2026-11-14, and `04_sanity_check.py` silently skips
   the lexicon checks when the file is absent.

The finding surfaced only from the **OOV tail**: `فرسビー` is the single most frequent
out-of-vocabulary token in the corpus. A whole-corpus 13.66% `has_oov` rate looks alarming and is
mostly benign (token-level rate 1.21% mean, 0.00% median — loanwords and unseen inflections); the
real defect was in which tokens were unknown, not how many.

**Gate added 2026-11-14:** `cocourdu.urdu_text.foreign_script_chars` plus the `has_foreign_script`
flag in `caption_checks`, so every `04_sanity_check.py` run reports the rate from here on. The
standalone reproduction, and every table in this section, is `scripts/13_script_contamination.py`.

### Consequence for the human study

At 2.106%, a 1,000-item study sample draws **~21 contaminated items** by chance. Those items would
be scored by raters as ordinary Urdu adequacy/fluency failures, confounding the system comparison
with a tokenizer artifact. Decide before `05_build_study.py` runs whether to repair, exclude, or
deliberately stratify on them.

### Remediation options

| option | cost | note |
|---|---|---|
| substitution table over the top 37 forms | minutes, 0 GPU units | covers 90%; must be documented as post-processing |
| + hand-translate the 346 whole-foreign tokens | hours | the remaining 5% is a translation problem, not a character swap |
| re-generate affected captions, same checkpoint | ~1 unit | **does nothing** — greedy decoding reproduces the same output |
| re-generate with a logit mask constrained to the Arabic block | ~5 units + rerun of all downstream QE | changes the experimental condition; v1-vs-v2 comparison must be redone |
| re-generate one chunk in bf16 | ~3 units | the quantization test above; worth it for the paper's claim |

### Reproduce

```bash
# every table in this section, plus results/script_contamination_gemma27b.parquet
uv run python scripts/13_script_contamination.py \
    --translations data/translations/gemma27b.parquet --compare-v1

# the v1 SeamlessM4T baseline on its own
uv run python scripts/13_script_contamination.py --v1

# every caption containing one form, with the foreign characters bracketed
uv run python scripts/13_script_contamination.py \
    --translations data/translations/gemma27b.parquet --word فرسビー
```

The per-caption parquet carries `uid`, `caption_en`, `ur`, `n_foreign`, `codepoints`, `scripts` and
a `highlighted` column that brackets every offending character, so a reader can verify the finding
without rendering right-to-left text.

### Side observation (separate, minor)

171 captions (0.054%) hedge gender or word choice with a slash — `ایک گائے/بیل`, `بیٹھا/بیٹھی`,
`ایک شاور/باتھ ٹب`.

---

## Finding 2 — The translator refuses to translate, and the refusal lands in the corpus

**Date:** 2026-11-14 · **Affects:** the 2026-11-12 Gemma 3 27B run (317,829 captions as generated)
**Record:** every affected caption is listed in `repairs/excluded_refusals.tsv`

### What is broken

For 279 captions the model did not produce a translation. It produced a refusal, or a note to the
user about the caption, and `03_translate_gemma_vllm.py` wrote that straight into the corpus as
though it were Urdu. `parse_translation` takes the first non-empty line, so the refusal passes every
structural check: it is fluent Urdu of plausible length in the right script.

> **EN:** There is s toilet scrubber next to the toilet in the stall.
> **Stored as Urdu:** غلطی سے معافی چاہتا ہوں، لیکن میں اس قسم کی تصویروں کا ترجمہ نہیں کر سکتا۔
> *("I apologise, but I cannot translate images of this kind.")*

> **EN:** a man that is standing around in a hate
> **Stored as Urdu:** میں اس تصویر کے کیپشن کا درست ترجمہ نہیں کر سکتا کیونکہ یہ نفرت پر مبنی اور ناخوشگوار ہے۔
> *("I cannot translate this caption correctly because it is hateful and unpleasant.")*

The second is the clearest case: `hate` is an annotator's typo for `hat`. The model read the typo as
the English noun, classified the caption as hate speech, and refused. The photograph is of a man in
a hat.

### How much

**280 of 317,829 generated captions (0.088%).** SeamlessM4T in v1 produced **zero** — an encoder-decoder
translation model has no refusal behaviour to express, so this is a defect introduced by moving to
an instruction-tuned LLM.

| refusal mode | captions | share |
|---|---|---|
| safety refusal (*inappropriate / obscene / unethical*) | 203 | 72.5% |
| other refusal (*I cannot translate this kind of image*) | 60 | 21.4% |
| translator's note (*Please note: "mmutl" appears to be a typo…*) | 17 | 6.1% |

216 refusals are in Urdu, 64 in English — the English ones break the target-language guarantee as
well, and are the reason `04_sanity_check` catches a few of them under `has_untranslated_english`.

### What triggers it

| trigger in the English caption | captions | share |
|---|---|---|
| sexual content or nudity | 157 | 56.1% |
| no obvious trigger — typo-garbled or mildly crude | 90 | 32.1% |
| scatological | 14 | 5.0% |
| annotator note instead of a caption (*"no image for this hit"*) | 12 | 4.3% |
| violence or drugs | 7 | 2.5% |

The 90 with no obvious trigger are the interesting group. Some are mild (*"A group of hot women
sitting at a table in front of a pizza"*); several are entirely innocuous and were refused anyway:

- *"The toilet is set on the sidewalk near a building."*
- *"A mmutl icolored kite being flown by a park"*
- *"a little dude shredding the gnar at a local skate park"* — refused as untranslatable slang
- *"THIS IS A TABLE OF LEAVES AND FOOD THAT ARE BEING USED FOR ORDURBS"*

MS-COCO captions are crowdworker text with typos, slang and crude phrasing. An instruction-tuned
translator applies a safety policy to that text, and the policy misfires on noise.

### Why no existing check caught it

A refusal is fluent, correctly scripted Urdu of ordinary length. It passes `empty`, `wrong_script`,
`too_short`, `too_long` and `repeated_trigram`. `len_ratio` is the only check with any purchase, and
a one-sentence refusal against a one-sentence caption sits inside the accepted band. The defect
surfaced only because the refusal text in 63 cases was English or Hindi, which
`scripts/13_script_contamination.py` flagged for an unrelated reason.

**Detection:** a refusal matches a small set of first-person and policy phrases that a caption
translation never contains — `میں ... نہیں کر سکتا`, `نا مناسب`, `فحش`, `as a large language model`,
`I am programmed`, `Please note`. Three captions match those phrases legitimately, because the
English says so (*"No one can turn down a pizza pie"*), so the match needs an eyeball, not a
blanket filter.

### What was done

All 280 were first translated by hand from the English source, then **removed from the dataset
entirely** — they are excluded from both `data/translations/gemma27b.parquet` and
`data/translations/gemma27b_repaired.parquet`, taking the corpus from 317,829 to **317,549**
captions. `repairs/excluded_refusals.tsv` records
`uid · caption_en · model_output · human_translation` for every one, so the exclusion is auditable
and the model's behaviour is preserved as evidence.

The exclusion is 0.088% of the corpus, but it is not a random 0.088%: these captions are the crude,
slang-heavy and typo-ridden tail of MS-COCO. The released corpus is therefore marginally easier
than MS-COCO itself, and the datasheet should say so.

### Why it matters for the paper

This is a failure mode that **only exists for LLM-based translation**, and it is invisible to
reference-free QE: COMET-Kiwi and xCOMET score a fluent Urdu refusal as fluent Urdu. It would have
reached human raters as a catastrophic adequacy failure attributable to the system rather than to
its safety layer. At 0.088% it would have put roughly one such item in a 1,000-item study sample.

The rate is the headline, not the repair: any LLM-based translation pipeline over crowdsourced
captions will hit this, and it is a defect a reference-free metric cannot see.

---

## Finding 3 — Half of v1's reported refinement gain is a measurement artifact

**Date:** 2026-11-14 · **Affects:** the v1 paper's Table 2 ("BLEU 0.31 → 0.76 after refinement")
**Reproduce:** `make forensics` → `results/table2_forensics.md`, `results/table2_flagged_rows.parquet`

### What is broken

v1 reported a large BLEU gain on the 3,572 captions its hybrid QE scored below 0.7, after an LLM
"refinement" pass. The refinement prompt rewrote **both** the machine translation and the reference
in a single call, and the reported "after" score compares the rewritten MT against the **rewritten
reference**. Two outputs of one prompt resemble each other far more than either resembles the
original reference, so the metric measures prompt self-consistency, not translation quality.

### How much

Recomputed on the same 3,572 flagged captions:

| pairing | BLEU | chrF++ |
|---|---|---|
| (a) v1 MT vs NLLB reference — the paper's *before* | 34.50 | 57.47 |
| (b) refined MT vs **refined** reference — the paper's *after* | **79.74** | 84.51 |
| (c) refined MT vs **original** reference — the honest *after* | 56.52 | 66.98 |
| (d) refined reference vs original reference — reference drift | 46.43 | 59.62 |

| | BLEU gain |
|---|---|
| as reported (a → b) | **+45.24** |
| as measured against a fixed reference (a → c) | **+22.02** |
| inflation (b − c) | **23.22 — 51% of the reported gain** |

(a) and (b) reproduce the published 0.31 and 0.76 closely, so the reconstruction is like-for-like.

### Why it happens

Row (d) is the mechanism. The refinement rewrote **97.3%** of references (and 99.7% of MT outputs),
and the rewritten reference scores only 46.43 BLEU against the original — it moved most of the way
toward the hypothesis. A reference that is edited in the same call that edits the hypothesis is no
longer an independent target, and BLEU against it is not a translation-quality measurement.

There is also a code-level error behind it. In
`notebooks/legacy/targetted_refinements.ipynb` the prompt asks the model to improve `A = Reference`
and `B = MT`, and the code then assigns `refined_mt = A` and `refined_ref = B` — swapped — before
overwriting both columns and computing the metrics.

### Why it matters for the paper

The honest gain is real and worth reporting: **+22.02 BLEU** against a fixed reference is a
substantial improvement. The claim that needs withdrawing is the +45.24 figure and the protocol
that produced it.

This is the motivation for v2. It is also a general methodological point: an LLM refinement loop
that touches the reference destroys the evaluation, and the failure is silent — every number looks
better, which is exactly what makes it convincing.

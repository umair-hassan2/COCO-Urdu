# Working notes (v2)

## Findings from the v1 code (2026-10-08)
- **Table 2 is circular and swapped.** `targetted_refinements.ipynb` prompts Qwen2.5-14B to improve *both* A=NLLB reference and B=MT in one call, then stores `refined_mt = A` and `refined_ref = B` (swapped) and overwrites both `translated_captions` and `references`. `benchmarking.ipynb` then scores `translated_captions` vs `references` on the refined dataset, i.e. one LLM output against another from the same prompt. `scripts/01_table2_forensics.py` recomputes the honest numbers.
- **Counts.** Public release `urdu-translated-coco-captions-subset`: 58,549 train + 5,000 validation = **63,549 images**; per-caption table: 292,907 + 25,014 = **317,921 captions**. Paper says 59K/319K → fix to 63.5K images (58.5K train) / 318K captions.
- v1 systems: translation `facebook/seamless-m4t-v2-large` (greedy, max 500 tokens); references `NLLB-200-3.3B`; QE = `Unbabel/wmt22-cometkiwi-da` (thr 0.7) + BERTScore F1 on Seamless ur→en back-translation (thr **0.8** in code, 0.9 in paper) + open_clip ViT-B-32 laion2b relative score (thr 0.7); hybrid = 0.4/0.4/0.2 weighted mean.
- Refined outputs contain non-words (`low_scoring_validation.json`: "ایلیف", "ابزار"). Refinement is retired in v2 in favour of QE-selection across systems.
- Image bytes are embedded in the HF per-image dataset, so embeddings can be computed without downloading COCO.

## Decisions
- Keep the 63.5K-image stratified subset (budget); state GPU-hour cost of the full set as a limitation.
- One shared prompt for all LLM translators (`cocourdu/prompts.py`), temperature 0.
- Human study: ≥2 raters per (item, system), 300-item core with all raters; author rates and is disclosed.

## TODO / pending
- [x] Translation route: Gemma 3 27B on Colab only (no paid APIs)
- [ ] Mac RAM → xCOMET-XL locally or on Colab
- [ ] Find/verify a 4-bit gemma-3-27b-it checkpoint that loads in vLLM
- [ ] Build `data/qe_full/comet_kiwi.parquet` loop (colab/README §3) — small script, not yet written

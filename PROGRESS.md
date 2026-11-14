# v2 run progress

Tick a box when a step finishes. Order and commands: `colab/README.md`.
Status: ☐ not started · ◐ running · ☑ done

| # | Where | Step | Status | Notes |
|---|-------|------|--------|-------|
| 1 | Mac | `make setup-ml` · `make stats forensics` · `build_lexicon.py` | ☑ | all done 2026-11-14 · lexicon 114,598 words · forensics → **Finding 3**: 51% of v1's Table 2 gain is a measurement artifact |
| 2 | Mac | `make embed` (~1 h MPS, background) | ☑ | 63,549 embeddings (58,549 train + 5,000 val), 53 min |
| 3 | Colab NB01 (A100) | sanity 1K → read report → full run → push | ☑ | **done 2026-11-12** — all 16 chunks, 317,829 rows, 0 empty; pushed to the artifacts repo |
| 4 | Mac | `sync.py pull` + `04_sanity_check.py` | ☑ | passed; two defects found and both fixed — see 4b |
| 4b | Mac | clean the translation corpus | **☑ DONE** | **2026-11-14.** Cross-script contamination 2.106% → **0.000%** (391 forms repaired by hand) · 280 refusal captions removed · corpus **317,829 → 317,549** · written up as Findings 1 and 2 in `docs/FINDINGS.md` — **the paper's machine-translation section** |
| 5 | Mac | `05_build_study.py --raters ...` | ☐ | → `data/study/items.jsonl`; use `gemma27b_repaired.parquet`, **needs rater ids** |
| 6 | Mac | `06_score_qe.py --metrics comet_kiwi metricx siglip2` + push | ☐ | → `data/study/qe_scores.parquet` |
| 7 | Colab NB03 (L4) | `06_score_qe.py --metrics xcomet` | ☐ | required: this Mac has 24 GB RAM |
| 8 | Mac | `sync.py pull qe_scores` · rating tool · `07_analyze_ratings.py` | ☐ | → `results/ratings.sqlite`, QE weights for step 10 |
| 9 | Colab NB02 (L4) | `11_comet_full.py --systems gemma27b` | ☐ | **moved before step 5** — it is the study stratifier → `data/qe_full/comet_kiwi.parquet` |
| 10 | — | ~~`09_qe_select.py`~~ | **dropped** | selection needs ≥2 systems; the paper reports gemma27b only |
| 11 | Mac | `08_retrieval.py` × 3 conditions (`zero_shot`, `gemma27b`, `english`) | ☐ | needs step 2 embeddings |
| 12 | Colab NB04 (L4) | VLM baselines | ☐ | no dependencies — run whenever units are idle |
| 13 | Mac | `sync.py pull results/vlm` + `12_figures.py` | ☐ | last |

## Colab units (80 total)

| Job | Est. | Spent |
|-----|------|-------|
| NB01 sanity | ~1 | ~1 |
| NB01 full | 25-35 | ~13 est. — 9 chunks on 2026-10-15, 8 chunks in 45 min on 2026-11-12 |
| NB03 xCOMET | ~2 | |
| NB02 COMET-Kiwi | 2-3 | |
| NB04 VLM (per model) | 5-7 | |

## Environment facts (settled 2026-10-14)

- Colab A100 runtime: A100-SXM4-40GB, 89.6 GB system RAM, 207 GB disk, **Python 3.13.15**.
  High-RAM is not needed. `pyproject.toml` was widened to `<3.14` so `pip install -e .` works there.
- Mac: 24 GB RAM → xCOMET cannot run locally, step 7 is required.
- Artifacts cross machines via `scripts/sync.py` (private HF repo `umairhassan02/coco-urdu-v2-artifacts`).
  All four notebooks need a WRITE-scope `HF_TOKEN` in Colab Secrets.

## Dataset caches

The three source repos carry image bytes — 3.5 GB (captions), 3.5 GB (refined), 10.4 GB (images) —
and a projected read of them is throttle-bound, measured at ~130s per shard, so ~70 min per table
on the Mac. `load_captions_v1` / `load_refined_v1` / `load_image_meta` now try the local parquet,
then the artifacts repo, and only then the source, pushing whatever they build. Whichever machine
pays for a table once hands it to the other. Check what is banked: `python scripts/sync.py ls data`.

Eight scripts benefit: 00, 01, 03, 04, 05, 08, 09, 11. Not `02_embed_images` (streams image bytes),
`build_lexicon` (fineweb), or 06/07/10/12 (local outputs only).

**All three banked 2026-10-15** — 121 MB standing in for 17.4 GB of source repos, built in 32 min
on a free CPU Colab runtime (0 compute units; the A100 had been doing this at 5.3 units/h with the
GPU idle at 0 GB).

| cache | size | source repo |
|---|---|---|
| `captions_v1.parquet` | 56.6 MB | 3.5 GB, 34 shards |
| `captions_refined_v1.parquet` | 37.6 MB | 3.5 GB, 34 shards |
| `images_meta.parquet` | 26.7 MB | 10.4 GB, 22 shards |

## Sanity gate — repaired corpus (317,549 captions, gemma27b, 2026-11-14) — PASSED

`04_sanity_check.py --translations data/translations/gemma27b_repaired.parquet`

| check | raw run | after repair + exclusion |
|---|---|---|
| empty | 0.00% (0) | 0.00% (0) |
| has_untranslated_english | 0.12% (386) | 0.10% (321) |
| wrong_script | 0.03% (104) | 0.01% (38) |
| too_short / too_long | 0.00% (3) / 0.08% (255) | 0.00% (3) / 0.02% (71) |
| repeated_trigram | 0.31% (1,000) | 0.31% (975) |
| has_foreign_script | 2.11% | **0.00% (0)** |
| has_oov | 13.66% (43,421) | 11.74% (37,296) |
| len_ratio_mean | 1.21 | 1.21 |

`has_oov` flags a caption if **any** token is absent from the 114,598-word fineweb lexicon, so the
rate is high while the token-level rate is ~1% — mostly loanwords and inflections the lexicon never
saw. The 1.9-point drop comes from the contamination repair.

### Foreign-script contamination (found 2026-11-14, from the OOV tail)


2.106% of captions (6,686) carry a character from another writing system — katakana, Devanagari,
Cyrillic and nine more — against zero for v1 SeamlessM4T. Full write-up, mechanism, and all
tables: **`docs/FINDINGS.md` § Finding 1**. Decide the remediation before `05_build_study.py` runs;
a 1,000-item sample draws ~21 of these.

Now gated and reproducible: `cocourdu.urdu_text.foreign_script_chars` + the `has_foreign_script`
flag in `caption_checks`, and `scripts/13_script_contamination.py` regenerates every table in the
finding plus a per-caption parquet with code points.

**Repaired 2026-11-14.** All 391 contaminated word-forms reviewed by hand. Map:
`repairs/script_contamination_gemma27b.tsv`; applied by `scripts/15_apply_repairs.py`.
**2.106% → 0.000%.** The raw parquet keeps the model output; the clean corpus is
`data/translations/gemma27b_repaired.parquet`.

### Refusals (found 2026-11-14) — `docs/FINDINGS.md` § Finding 2

280 captions (0.088%) held a refusal or a translator's note instead of a translation, against zero
for v1 SeamlessM4T. **Removed from the dataset entirely** — corpus is now **317,549** captions, down
from 317,829. `repairs/excluded_refusals.tsv` keeps
`uid · caption_en · model_output · human_translation` for all 280.

## Sanity gate (1K captions, gemma27b, 2026-10-14) — PASSED

| check | rate |
|---|---|
| empty | 0.00% |
| wrong_script | 0.00% |
| too_short / too_long | 0.00% / 0.00% |
| untranslated English | 0.10% (1) |
| repeated_trigram | 0.30% (3) |
| len_ratio_mean | 1.20 |

Throughput 55.4 captions/s on the A100 → ~96 min for 317,829 captions in 16 chunks of 20K.
Model load is 384s cold, ~60s warm (torch.compile cache hit).

## Log

- 2026-10-14 — `scripts/sync.py` added; notebooks switched off browser upload/download (`c37b9a8`).
- 2026-10-14 — Python cap raised to `<3.14` for the Colab 3.13 runtime (`a58e95d`).
- 2026-10-14 — Colab jobs log each slow phase; README commands use `python -u` (`4680432`).
- 2026-10-14 — HF parquet shards read in parallel (`c998fe7`); measured gain is small, the read is
  throttle-bound rather than latency-bound.
- 2026-10-14 — Dataset loaders serve from the artifacts repo before falling back to the source (`bd6952a`).
- 2026-10-15 — Step 2 done: 63,549 SigLIP2 embeddings, 53 min on MPS.
- 2026-10-15 — `cocourdu.urdu_text` could not import at all (`str.maketrans` rejects multi-char
  keys); fixed in `4507341`. It had been taking down `04_sanity_check`, the A100 spend gate.
- 2026-10-15 — Cache builds moved to a free CPU Colab runtime; the A100 sat at 0 GB GPU RAM while
  downloading, burning ~5.3 units/h for nothing.
- 2026-10-15 — Translation paused overnight at chunk 7/16 to avoid burning A100 hours while asleep.
  Resume point is `chunks/gemma27b/` on the chunk repo; nothing is lost but the in-flight chunk.
- 2026-10-15 — All three dataset caches banked (121 MB). `build_lexicon` had been SIGTSTP-stopped
  for 2 h in the foreground; re-run under nohup it finished in 36 s — 114,598 words.
- 2026-11-12 — Translation finished: chunks 9–16 in 36 min of generation (~84 prompts/s), 0 empty
  outputs, merged to 317,829 rows and pushed. Warm runtime loaded in 95 s vs 358 s cold.
- 2026-11-14 — Step 4 re-run on the full file. The `results/sanity_gemma27b.md` pushed at the end of
  the Colab session was the 160,042-row partial — it was written before the run resumed, never
  regenerated. Rates are unchanged on the full file.
- 2026-11-14 — Cross-script contamination found and written up in `docs/FINDINGS.md`;
  `scripts/13_script_contamination.py` added so a reviewer can regenerate every number.
- 2026-11-14 — Contamination repaired end to end (396 forms by hand) and 279 refusal captions
  hand-translated. Clean corpus: `data/translations/gemma27b_repaired.parquet`. Finding 2 written up.
- 2026-11-14 — 280 refusal captions removed from the corpus (317,829 → 317,549) after being
  hand-translated; the translations are kept in `repairs/excluded_refusals.tsv` as the record.
- 2026-11-14 — **Step 4b closed.** Corpus clean: 0 foreign-script characters, 0 refusals, 317,549
  captions. Findings 1 and 2 in `docs/FINDINGS.md` are the machine-translation section of the paper;
  every table in them regenerates from `scripts/13_script_contamination.py`.
- 2026-11-14 — Step 1 closed. `00_dataset_stats` and `01_table2_forensics` run; the Table 2
  forensics is written up as Finding 3 in `docs/FINDINGS.md`.

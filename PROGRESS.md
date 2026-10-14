# v2 run progress

Tick a box when a step finishes. Order and commands: `colab/README.md`.
Status: ☐ not started · ◐ running · ☑ done

| # | Where | Step | Status | Notes |
|---|-------|------|--------|-------|
| 1 | Mac | `make setup-ml` · `make stats forensics` · `build_lexicon.py` | ◐ | setup-ml ☑ · lexicon ☑ 114,598 words · **stats/forensics still to run** |
| 2 | Mac | `make embed` (~1 h MPS, background) | ☑ | 63,549 embeddings (58,549 train + 5,000 val), 53 min |
| 3 | Colab NB01 (A100) | sanity 1K → read report → full run → push | ◐ | sanity passed, full run started 20:59 | → `data/translations/gemma27b.parquet`; blocks 4-12 |
| 4 | Mac | `sync.py pull` + `04_sanity_check.py` | ☐ | gate before spending the rest of the A100 units |
| 5 | Mac | `05_build_study.py --raters ...` | ☐ | → `data/study/items.jsonl` |
| 6 | Mac | `06_score_qe.py --metrics comet_kiwi metricx siglip2` + push | ☐ | → `data/study/qe_scores.parquet` |
| 7 | Colab NB03 (L4) | `06_score_qe.py --metrics xcomet` | ☐ | required: this Mac has 24 GB RAM |
| 8 | Mac | `sync.py pull qe_scores` · rating tool · `07_analyze_ratings.py` | ☐ | → `results/ratings.sqlite`, QE weights for step 10 |
| 9 | Colab NB02 (L4) | `11_comet_full.py --systems seamless gemma27b` | ☐ | → `data/qe_full/comet_kiwi.parquet` |
| 10 | Mac | `sync.py pull data/qe_full` + `09_qe_select.py` | ☐ | → `data/translations/qe_selected.parquet` |
| 11 | Mac | `08_retrieval.py` × 5 conditions | ☐ | needs step 2 embeddings + step 10 |
| 12 | Colab NB04 (L4) | VLM baselines | ☐ | no dependencies — run whenever units are idle |
| 13 | Mac | `sync.py pull results/vlm` + `12_figures.py` | ☐ | last |

## Colab units (80 total)

| Job | Est. | Spent |
|-----|------|-------|
| NB01 sanity | ~1 | ~1 |
| NB01 full | 25-35 | ~9 est. (55.4 cap/s, warm runtime) |
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
- 2026-10-15 — All three dataset caches banked (121 MB). `build_lexicon` had been SIGTSTP-stopped
  for 2 h in the foreground; re-run under nohup it finished in 36 s — 114,598 words.

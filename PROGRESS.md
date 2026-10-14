# v2 run progress

Tick a box when a step finishes. Order and commands: `colab/README.md`.
Status: ☐ not started · ◐ running · ☑ done

| # | Where | Step | Status | Notes |
|---|-------|------|--------|-------|
| 1 | Mac | `make setup-ml` · `make stats forensics` · `build_lexicon.py` | ☐ | → `results/stats.json`, `table2_forensics.md`, `data/lexicon/` |
| 2 | Mac | `make embed` (~1 h MPS, background) | ☐ | → `data/embeddings/`; only step 10 needs it |
| 3 | Colab NB01 (A100) | sanity 1K → read report → full run → push | ☐ | → `data/translations/gemma27b.parquet`; blocks 4-12 |
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
| NB01 sanity | ~1 | |
| NB01 full | 25-35 | |
| NB03 xCOMET | ~2 | |
| NB02 COMET-Kiwi | 2-3 | |
| NB04 VLM (per model) | 5-7 | |

## Environment facts (settled 2026-10-14)

- Colab A100 runtime: A100-SXM4-40GB, 89.6 GB system RAM, 207 GB disk, **Python 3.13.15**.
  High-RAM is not needed. `pyproject.toml` was widened to `<3.14` so `pip install -e .` works there.
- Mac: 24 GB RAM → xCOMET cannot run locally, step 7 is required.
- Artifacts cross machines via `scripts/sync.py` (private HF repo `umairhassan02/coco-urdu-v2-artifacts`).
  All four notebooks need a WRITE-scope `HF_TOKEN` in Colab Secrets.

## Log

- 2026-10-14 — `scripts/sync.py` added; notebooks switched off browser upload/download (`c37b9a8`).
- 2026-10-14 — Python cap raised to `<3.14` for the Colab 3.13 runtime (`a58e95d`).

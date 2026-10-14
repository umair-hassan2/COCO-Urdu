# Colab run-sheet (80 units total — check the Resources panel before every session)

Every job is resumable. Pick **A100** only for the 27B translation; everything else runs on **L4**.

Notebooks live beside this file: `01_translate_gemma.ipynb`, `02_comet_full.ipynb`,
`03_xcomet_study.ipynb`, `04_vlm_baselines.ipynb`. Open them in Colab with
**File → Open notebook → GitHub → `umair-hassan2/COCO-Urdu`, branch `v2`**. Each notebook clones
the repo and runs `git pull`, so edit locally, push, and re-run the setup cell to pick up changes.

## Order of operations

Mac and Colab steps **interleave** — they are not two separate phases. Run top to bottom:

| # | Where | Command | Needs / produces |
|---|---|---|---|
| 1 | Mac | `make stats forensics` · `build_lexicon.py` | nothing — run anytime |
| 2 | Mac | `02_embed_images.py` (~1 h MPS) | → `data/embeddings/`; only step 10 needs it, so start it early in the background |
| 3 | **Colab NB01** (A100) | sanity pass 1K → read report → full run | → `data/translations/gemma27b.parquet`, pushed to the artifacts repo — **everything below waits on this** |
| 4 | Mac | `04_sanity_check.py --translations ...` | needs the lexicon from step 1; gate before spending the rest of the A100 units |
| 5 | Mac | `05_build_study.py --raters ...` | globs `data/translations/*.parquet` → `data/study/items.jsonl` |
| 6 | Mac | `06_score_qe.py --metrics comet_kiwi metricx siglip2` | → `data/study/qe_scores.parquet` |
| 6b | **Colab NB03** (L4) | `06_score_qe.py --metrics xcomet` | **required — this Mac has 24 GB**; `sync.py push data/study/items.jsonl` first, `sync.py pull data/study/qe_scores.parquet` after |
| 7 | Mac | rating tool → `07_analyze_ratings.py` | → `results/ratings.sqlite`, `results/human_study/` (and the QE weights step 9 uses) |
| 8 | **Colab NB02** (L4) | `11_comet_full.py --systems seamless gemma27b` | pulls the translations NB01 pushed → `data/qe_full/comet_kiwi.parquet`; `sync.py pull data/qe_full` on the Mac |
| 9 | Mac | `09_qe_select.py --systems seamless gemma27b` | needs step 8's parquet → `data/translations/qe_selected.parquet` |
| 10 | Mac | `08_retrieval.py --condition ...` (all 5) | needs step 2 embeddings + step 9 `qe_selected` |
| 11 | **Colab NB04** (L4) | VLM baselines | **no dependencies** — good filler whenever units are idle |
| 12 | Mac | `12_figures.py` | after 07 and 08 |

## Moving files between the Mac and Colab

`data/` and `results/` are gitignored, so git cannot carry run outputs. `scripts/sync.py` moves them
through a **private HF dataset repo** — `umairhassan02/coco-urdu-v2-artifacts`, created on first push
(override with `--repo` or `COCOURDU_SYNC_REPO`). Both sides address a file by its repo-relative path,
which is also its path inside the hub repo, so the same command works on either machine:

```bash
python scripts/sync.py push data/study/items.jsonl      # Mac, after step 5
python scripts/sync.py pull data/qe_full                # Mac, after Colab NB02 (a directory pulls everything under it)
python scripts/sync.py ls data                          # what is up there right now
```

The notebooks already call it: each one pulls what it needs in its first job cell and pushes its
outputs in the last. Nothing goes through the browser, and nothing is lost when a VM disconnects.
This is **not** the `--hf-repo` of `03_translate_gemma_vllm.py` — that one holds mid-run chunk
checkpoints; this one holds finished artifacts the next step consumes.

Because every notebook now pushes, **all four need a WRITE-scope `HF_TOKEN`**, not just job 1.

## 0. Bootstrap cell (every session)

Auth comes from `HF_TOKEN` in the environment rather than an interactive `notebook_login()` prompt.
Store it once in **Colab Secrets** (sidebar key icon) and enable it per notebook; `huggingface_hub`
picks it up automatically, including inside the `!python` subprocesses. All four jobs need **WRITE** scope: job 1 creates the chunk repo, and every job pushes its outputs
to the artifacts repo with `scripts/sync.py`.
```python
!git clone https://github.com/umair-hassan2/COCO-Urdu.git -b v2 && cd COCO-Urdu
%cd /content/COCO-Urdu
!pip install -q -e . && pip install -q vllm        # vllm only for job 1
import os
from google.colab import userdata          # Colab Secrets: sidebar key icon -> add HF_TOKEN
os.environ['HF_TOKEN'] = userdata.get('HF_TOKEN')   # WRITE scope; inherited by the !python cells
```

## 1. Re-translation — Gemma 3 27B (A100 40 GB, ~25–35 units for 318K captions)
Model: **`RedHatAI/gemma-3-27b-it-quantized.w4a16`** — compressed-tensors W4A16, ~19.7 GB on disk,
`Gemma3ForConditionalGeneration`, 131K context, needs `vllm>=0.8.0`. Fits an A100 40 GB with room for KV cache.
(Rejected `pytorch/gemma-3-27b-it-AWQ-INT4`: its card says AWQ INT4 is H100/SM90-only, and it needs a vLLM nightly.)

`--hf-repo` is a **private write target for resumable chunk checkpoints**, created automatically on first run.
It is *not* an input dataset — the inputs are hardcoded in `cocourdu/data.py`. Use `umairhassan02/coco-urdu-v2-chunks`.

Sanity pass first (≈1 unit), then check `results/sanity_gemma27b.md` before spending the rest:
`python -u` keeps the logs streaming: without it Colab shows nothing until the process exits.
```python
!python -u scripts/03_translate_gemma_vllm.py --system gemma27b --model RedHatAI/gemma-3-27b-it-quantized.w4a16 --hf-repo umairhassan02/coco-urdu-v2-chunks --limit 1000 --chunk-size 1000
!python -u scripts/03_translate_gemma_vllm.py --system gemma27b --hf-repo umairhassan02/coco-urdu-v2-chunks --merge
!python -u scripts/04_sanity_check.py --translations data/translations/gemma27b.parquet
```
Full run (re-run the same command after any disconnect; finished chunks are skipped):
```python
!python -u scripts/03_translate_gemma_vllm.py --system gemma27b --model RedHatAI/gemma-3-27b-it-quantized.w4a16 --hf-repo umairhassan02/coco-urdu-v2-chunks --chunk-size 20000
!python -u scripts/03_translate_gemma_vllm.py --system gemma27b --hf-repo umairhassan02/coco-urdu-v2-chunks --merge
```
No A100? `--model google/gemma-3-12b-it` on L4 in bf16 (`--system gemma12b`).

## 2. xCOMET-QE on study items (L4, ~2 units) — only if the Mac has < 32 GB RAM
```python
!python -u scripts/06_score_qe.py --metrics xcomet
```
(`sync.py push data/study/items.jsonl` on the Mac first; the notebook pulls it, and pushes
`data/study/qe_scores.parquet` back when it finishes.)

## 3. COMET-Kiwi over ALL captions × systems for qe-selection (L4, ~2–3 units)
```python
!python -u scripts/11_comet_full.py --systems seamless gemma27b
```
Writes `data/qe_full/comet_kiwi.parquet` (`uid, system, score`), resumable per system. The notebook pulls
`data/translations/<system>.parquet` from the artifacts repo (NB01 pushed it). Then on the Mac:
`sync.py pull data/qe_full` and `scripts/09_qe_select.py --systems seamless gemma27b`.

## 4. Zero-shot VLM captioning baselines (L4, ~5–7 units each)
```python
!python -u scripts/10_vlm_zero_shot.py --model Qwen/Qwen2.5-VL-7B-Instruct --n 500
!python -u scripts/10_vlm_zero_shot.py --model google/gemma-3-12b-it --n 500
```

## What runs on the Mac (0 units)
`00_dataset_stats`, `01_table2_forensics`, `02_embed_images` (MPS, ~1 h), `build_lexicon`, `04_sanity_check`, `05_build_study`, `06_score_qe --metrics comet_kiwi metricx siglip2`, `07_analyze_ratings`, `08_retrieval` (all conditions), `09_qe_select`, `12_figures`, the rating tool, and `sync.py push/pull` around every Colab hop.
(xCOMET is **not** on this list — 24 GB RAM sends it to NB03.)

## Driving Colab from this repo (colab-mcp)
`.mcp.json` registers [`googlecolab/colab-mcp`](https://github.com/googlecolab/colab-mcp), which bridges
a local agent to a Colab notebook **open in your browser**. It does not give headless execution: the
agent's first call opens `colab.research.google.com` with a one-time token, you pick the GPU runtime
there, and the notebook tools then appear in the agent. Compute still comes out of your 80 units.

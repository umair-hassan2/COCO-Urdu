# Colab run-sheet (80 units total — check the Resources panel before every session)

Every job is resumable. Pick **A100** only for the 27B translation; everything else runs on **L4**.

## 0. Bootstrap cell (every session)
```python
!git clone https://github.com/umair-hassan2/COCO-Urdu.git -b v2 && cd COCO-Urdu
%cd /content/COCO-Urdu
!pip install -q -e . && pip install -q vllm        # vllm only for job 1
from huggingface_hub import notebook_login; notebook_login()   # needed for gated COMET models and chunk uploads
```

## 1. Re-translation — Gemma 3 27B (A100 40 GB, ~25–35 units for 318K captions)
Sanity pass first (≈1 unit), then check `results/sanity_gemma27b.md` before spending the rest:
```python
!python scripts/03_translate_gemma_vllm.py --system gemma27b --model <QUANTIZED-gemma-3-27b-it repo> --hf-repo <you>/coco-urdu-v2-chunks --limit 1000 --chunk-size 1000
!python scripts/03_translate_gemma_vllm.py --system gemma27b --hf-repo <you>/coco-urdu-v2-chunks --merge
!python scripts/04_sanity_check.py --translations data/translations/gemma27b.parquet
```
Full run (re-run the same command after any disconnect; finished chunks are skipped):
```python
!python scripts/03_translate_gemma_vllm.py --system gemma27b --model <QUANTIZED repo> --hf-repo <you>/coco-urdu-v2-chunks --chunk-size 20000
!python scripts/03_translate_gemma_vllm.py --system gemma27b --hf-repo <you>/coco-urdu-v2-chunks --merge
```
Notes: a 27B model needs a 4-bit checkpoint (AWQ/GPTQ) on 40 GB; verify the repo exists and loads in vLLM before the full run. If no A100: `--model google/gemma-3-12b-it` on L4 in bf16 (`--system gemma12b`).
**API alternative (0 units, ~$10–45):** run `scripts/03_translate_api.py` on the Mac instead (see docstring).

## 2. xCOMET-QE on study items (L4, ~2 units) — only if the Mac has < 32 GB RAM
```python
!python scripts/06_score_qe.py --metrics xcomet
```
(Upload `data/study/items.jsonl` first, download `data/study/qe_scores.parquet` after.)

## 3. COMET-Kiwi over ALL captions × systems for qe-selection (L4, ~2–3 units)
Write `data/qe_full/comet_kiwi.parquet` with columns `uid, system, score` (small loop over `load_captions_v1()` + `data/translations/*.parquet` using `cocourdu.qe.comet.CometQE`). Then on the Mac: `scripts/09_qe_select.py --systems seamless gemma27b`.

## 4. Zero-shot VLM captioning baselines (L4, ~5–7 units each)
```python
!python scripts/10_vlm_zero_shot.py --model Qwen/Qwen2.5-VL-7B-Instruct --n 500
!python scripts/10_vlm_zero_shot.py --model google/gemma-3-12b-it --n 500
```

## What runs on the Mac (0 units)
`00_dataset_stats`, `01_table2_forensics`, `02_embed_images` (MPS, ~1 h), `build_lexicon`, `04_sanity_check`, `05_build_study`, `06_score_qe --metrics comet_kiwi metricx siglip2`, `07_analyze_ratings`, `08_retrieval` (all conditions), the rating tool.

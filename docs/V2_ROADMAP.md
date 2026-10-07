# v2 technical roadmap (what each script does, in order)

| Step | Script | Where | Output |
|---|---|---|---|
| Counts | `00_dataset_stats.py` | Mac | `results/stats.{json,md}` |
| Table 2 audit | `01_table2_forensics.py` | Mac | `results/table2_forensics.md` |
| Image embeddings | `02_embed_images.py` | Mac (MPS) | `data/embeddings/<model>/` |
| Lexicon | `build_lexicon.py` | Mac | `data/lexicon/urdu_words.txt` |
| Re-translation | `03_translate_gemma_vllm.py` or `03_translate_api.py` | Colab A100 / Mac+API | `data/translations/<system>.parquet` |
| Sanity | `04_sanity_check.py` | Mac | `results/sanity_<system>.md` |
| Study items | `05_build_study.py --raters ...` | Mac | `data/study/{items.jsonl,assignment.json}` |
| Rating | `rating_tool/app.py` | Mac (+cloudflared) | `results/ratings.sqlite` |
| QE baselines | `06_score_qe.py` | Mac / Colab L4 (xcomet) | `data/study/qe_scores.parquet` |
| Analysis | `07_analyze_ratings.py` | Mac | `results/human_study/` |
| Retrieval | `08_retrieval.py --condition ...` | Mac (MPS) | `results/retrieval/*.json` |
| QE-selected release | `09_qe_select.py` | Mac (after Colab COMET loop) | `data/translations/qe_selected.parquet` |
| VLM baselines | `10_vlm_zero_shot.py` | Colab L4 | `results/vlm/` |

Paper sections map: §3 corpus ← 00/03/04/09 · §4 human study ← 05/07 · §4.3 QE meta-eval ← 06/07 · §5 experiments ← 08/10.
| Figures | `12_figures.py` | Mac | `results/figures/F1..F5` |

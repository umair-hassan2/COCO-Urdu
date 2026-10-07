# COCO-Urdu v2 — common entry points. See docs/V2_ROADMAP.md for the full pipeline.
PY := uv run python

.PHONY: setup stats forensics embed sanity study qe analyze retrieval rate

setup:            ## create venv with core + rating + analysis deps
	uv sync --extra rating --extra analysis --extra api

setup-ml:         ## add torch/transformers/COMET (Mac or GPU box)
	uv sync --extra rating --extra analysis --extra api --extra qe

stats:            ## reconcile dataset counts -> results/stats.json
	$(PY) scripts/00_dataset_stats.py

forensics:        ## what did Table 2 actually compare? -> results/table2_forensics.md
	$(PY) scripts/01_table2_forensics.py

embed:            ## SigLIP 2 image embeddings for all 63.5K images (Mac MPS)
	$(PY) scripts/02_embed_images.py

sanity:           ## automatic checks on a translation file: make sanity FILE=data/translations/gemma27b.parquet
	$(PY) scripts/04_sanity_check.py --translations $(FILE)

study:            ## sample study items -> data/study/items.jsonl
	$(PY) scripts/05_build_study.py

qe:               ## score QE baselines on study items
	$(PY) scripts/06_score_qe.py

analyze:          ## ratings -> results/human_study/*.md
	$(PY) scripts/07_analyze_ratings.py

retrieval:        ## train/eval retrieval on cached embeddings
	$(PY) scripts/08_retrieval.py

rate:             ## launch the rating tool locally
	uv run streamlit run rating_tool/app.py

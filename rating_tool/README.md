# Rating tool

1. Build items: `uv run python scripts/05_build_study.py --raters umair friend1 friend2` (after translations exist in `data/translations/`).
2. Run: `uv run streamlit run rating_tool/app.py`
3. Share without hosting: `brew install cloudflared && cloudflared tunnel --url http://localhost:8501`, send the URL + the rater's name. Keep the Mac awake while friends rate.
4. Backup (optional): `export HF_RATINGS_REPO=<user>/coco-urdu-ratings HF_TOKEN=...` — the sqlite file is uploaded after every submit.
5. Analyze: `uv run python scripts/07_analyze_ratings.py --db results/ratings.sqlite`

Install an Urdu Nastaliq font (Noto Nastaliq Urdu) on raters' machines for readable text; the CSS falls back to serif.

"""COCO-Urdu rating tool — Streamlit + SQLite, nothing else.

Each rater sees: image, English caption, then every system's Urdu (shuffled per item+rater, labels A/B/C, system hidden),
with Adequacy 0-100, Fluency 0-100, error tags, optional comment. One submit = one row per version.

Run locally:   streamlit run rating_tool/app.py
Share with friends without hosting: run locally, then `cloudflared tunnel --url http://localhost:8501` and send the URL.
Optional backup to HF Hub: set HF_RATINGS_REPO=<user>/coco-urdu-ratings (private dataset) and HF_TOKEN; the sqlite file
is uploaded after every submission so a crash loses nothing.
"""
import hashlib
import json
import os
import random
import sqlite3
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "data" / "study" / "items.jsonl"
ASSIGN = ROOT / "data" / "study" / "assignment.json"
DB = Path(os.environ.get("RATINGS_DB", ROOT / "results" / "ratings.sqlite"))
ERRORS = {"mistranslation": "غلط ترجمہ (mistranslation)", "omission": "کچھ چھوٹ گیا (omission)", "addition": "کچھ اضافی/من گھڑت (addition)",
          "agreement": "جنس/عدد کی غلطی (gender/number)", "spelling": "املا / غیر لفظ (spelling, non-word)",
          "word_order": "غیر فطری ترتیب (word order)", "untranslated": "انگریزی باقی (untranslated)"}


@st.cache_data
def load_items():
    items = {json.loads(l)["item_id"]: json.loads(l) for l in ITEMS.open(encoding="utf-8")}
    assign = json.loads(ASSIGN.read_text())
    return items, assign


def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS ratings (
        item_id TEXT, rater TEXT, system TEXT, position INTEGER, adequacy INTEGER, fluency INTEGER,
        errors TEXT, comment TEXT, seconds REAL, ts REAL, PRIMARY KEY (item_id, rater, system))""")
    return con


def done_items(con, rater):
    return {r[0] for r in con.execute("SELECT DISTINCT item_id FROM ratings WHERE rater=?", (rater,))}


def backup():
    repo = os.environ.get("HF_RATINGS_REPO")
    if not repo:
        return
    try:
        from huggingface_hub import HfApi
        HfApi().upload_file(path_or_fileobj=str(DB), path_in_repo="ratings.sqlite", repo_id=repo, repo_type="dataset")
    except Exception as e:  # never block a rater on a backup failure
        st.sidebar.warning(f"backup failed: {e}")


def order_for(item_id, rater, systems):
    seed = int(hashlib.sha1(f"{item_id}|{rater}".encode()).hexdigest(), 16) % (2 ** 32)
    s = list(systems); random.Random(seed).shuffle(s); return s


st.set_page_config(page_title="COCO-Urdu rating", layout="wide")
st.markdown("<style>.ur{font-size:1.6rem;direction:rtl;text-align:right;font-family:'Noto Nastaliq Urdu','Jameel Noori Nastaleeq',serif;line-height:2.2}</style>", unsafe_allow_html=True)
items, assign = load_items()
con = db()

rater = st.sidebar.selectbox("Rater", list(assign["raters"]))
my_items = assign["raters"][rater]
done = done_items(con, rater)
todo = [i for i in my_items if i not in done]
st.sidebar.progress(len(done) / max(1, len(my_items)), f"{len(done)} / {len(my_items)} items")
with st.sidebar.expander("Guidelines (read once)"):
    st.markdown((ROOT / "rating_tool" / "guidelines.md").read_text(encoding="utf-8"))
if not todo:
    st.success("All your items are rated. شکریہ!"); st.stop()

item = items[todo[0]]
if "t0" not in st.session_state or st.session_state.get("cur") != item["item_id"]:
    st.session_state.t0, st.session_state.cur = time.time(), item["item_id"]
left, right = st.columns([1, 1.3])
with left:
    st.image(item["image_url"], use_container_width=True)
    st.markdown(f"**English:** {item['caption_en']}")
with right:
    order = order_for(item["item_id"], rater, item["versions"])
    with st.form(key=item["item_id"], clear_on_submit=True):
        answers = {}
        for k, sysname in enumerate(order):
            label = "ABCDE"[k]
            st.markdown(f"**Version {label}**"); st.markdown(f"<div class='ur'>{item['versions'][sysname]}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            adequacy = c1.slider(f"Adequacy {label} — meaning preserved?", 0, 100, 50, key=f"a{label}")
            fluency = c2.slider(f"Fluency {label} — natural, correct Urdu?", 0, 100, 50, key=f"f{label}")
            errs = st.multiselect(f"Errors {label}", list(ERRORS), format_func=ERRORS.get, key=f"e{label}")
            answers[sysname] = (k, adequacy, fluency, errs)
            st.divider()
        comment = st.text_input("Comment (optional)")
        if st.form_submit_button("Save and next ➜", type="primary", use_container_width=True):
            secs = time.time() - st.session_state.t0
            for sysname, (k, a, fl, errs) in answers.items():
                con.execute("INSERT OR REPLACE INTO ratings VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (item["item_id"], rater, sysname, k, a, fl, ",".join(errs), comment, secs, time.time()))
            con.commit(); backup(); st.rerun()

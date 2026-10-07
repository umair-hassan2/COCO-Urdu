"""Build the qe-selected release: per caption, pick the system with the best (validated) QE score.

Needs a QE score for every caption x system (data/qe_full/<metric>.parquet with columns uid, system, score) — produced by
running the chosen metric over all systems (Colab L4 ~2 units for COMET-Kiwi on 318K x 2). Weights come from 07's fit.
Output: data/translations/qe_selected.parquet (uid, ur_qe_selected, selected_system, qe_score) + per-system pick counts.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA, RESULTS
from cocourdu.data import load_captions_v1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", nargs="+", required=True, help="e.g. seamless gemma27b")
    ap.add_argument("--weights", default='{"comet_kiwi": 1.0}', help='JSON metric->weight; metrics are z-normalized first')
    args = ap.parse_args()
    weights = json.loads(args.weights)
    caps = load_captions_v1()[["uid", "ur_seamless"]]
    texts = {"seamless": caps.set_index("uid").ur_seamless}
    for s in args.systems:
        if s != "seamless":
            t = pd.read_parquet(DATA / "translations" / f"{s}.parquet"); texts[s] = t.set_index("uid")[f"ur_{s}"]
    frames = []
    for metric, w in weights.items():
        q = pd.read_parquet(DATA / "qe_full" / f"{metric}.parquet")
        q["z"] = (q.score - q.score.mean()) / q.score.std(); q["w"] = w * q.z
        frames.append(q[["uid", "system", "w"]])
    score = pd.concat(frames).groupby(["uid", "system"]).w.sum().reset_index()
    score = score[score.system.isin(args.systems)]
    best = score.sort_values("w", ascending=False).drop_duplicates("uid")
    best["ur_qe_selected"] = [texts[s].get(u) for u, s in zip(best.uid, best.system)]
    out = best.rename(columns={"system": "selected_system", "w": "qe_score"})[["uid", "ur_qe_selected", "selected_system", "qe_score"]]
    out.to_parquet(DATA / "translations" / "qe_selected.parquet", index=False)
    counts = out.selected_system.value_counts().to_dict()
    RESULTS.mkdir(exist_ok=True); (RESULTS / "qe_select_counts.json").write_text(json.dumps(counts, indent=1))
    print(f"{len(out):,} captions selected; picks: {counts}")


if __name__ == "__main__":
    main()

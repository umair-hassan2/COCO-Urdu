"""COMET-Kiwi over ALL captions x systems (Colab L4, ~2-3 units) -> data/qe_full/comet_kiwi.parquet (uid, system, score).

Feeds scripts/09_qe_select.py. Resumable per system.
  python scripts/11_comet_full.py --systems seamless gemma27b
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA
from cocourdu.data import load_captions_v1
from cocourdu.qe.comet import CometQE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", nargs="+", required=True)
    ap.add_argument("--batch-size", type=int, default=128)
    args = ap.parse_args()
    out_dir = DATA / "qe_full"; out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "comet_kiwi.parquet"
    done = pd.read_parquet(out) if out.exists() else pd.DataFrame(columns=["uid", "system", "score"])
    caps = load_captions_v1()[["uid", "caption_en", "ur_seamless"]]
    scorer = CometQE(batch_size=args.batch_size)
    for s in args.systems:
        if s in set(done.system):
            print(f"skip {s} (done)"); continue
        if s == "seamless":
            df = caps.rename(columns={"ur_seamless": "ur"})
        else:
            t = pd.read_parquet(DATA / "translations" / f"{s}.parquet")
            df = caps.drop(columns="ur_seamless").merge(t[["uid", f"ur_{s}"]], on="uid").rename(columns={f"ur_{s}": "ur"})
        df = df.dropna(subset=["ur"])
        scores = scorer.score(df.caption_en.tolist(), df.ur.tolist())
        done = pd.concat([done, pd.DataFrame({"uid": df.uid.values, "system": s, "score": scores})], ignore_index=True)
        done.to_parquet(out, index=False); print(f"{s}: {len(df):,} scored, mean {sum(scores)/len(scores):.3f}")


if __name__ == "__main__":
    main()

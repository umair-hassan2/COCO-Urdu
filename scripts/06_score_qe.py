"""Score every (item, system) Urdu caption in the study with each QE metric -> data/study/qe_scores.parquet

Metrics (pick with --metrics): comet_kiwi xcomet metricx siglip2 siglip2_rel
Run text metrics on the Mac; xcomet on Colab L4 if Mac RAM < 32 GB.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA


def load_items():
    rows = []
    for l in (DATA / "study" / "items.jsonl").open(encoding="utf-8"):
        it = json.loads(l)
        for sysname, ur in it["versions"].items():
            rows.append({"item_id": it["item_id"], "uid": it["uid"], "image_id": it["image_id"], "image_url": it["image_url"],
                         "system": sysname, "caption_en": it["caption_en"], "ur": ur})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", nargs="+", default=["comet_kiwi", "metricx", "siglip2"])
    ap.add_argument("--siglip-model", default="google/siglip2-base-patch16-224")
    args = ap.parse_args()
    out = DATA / "study" / "qe_scores.parquet"
    df = pd.read_parquet(out) if out.exists() else load_items()

    if "comet_kiwi" in args.metrics:
        from cocourdu.qe.comet import CometQE
        df["comet_kiwi"] = CometQE().score(df.caption_en.tolist(), df.ur.tolist())
    if "xcomet" in args.metrics:
        from cocourdu.qe.comet import XCOMET_XL, CometQE
        df["xcomet_qe"] = CometQE(XCOMET_XL, batch_size=8).score(df.caption_en.tolist(), df.ur.tolist())
    if "metricx" in args.metrics:
        from cocourdu.qe.metricx import MetricX24QE
        df["metricx24_qe"] = MetricX24QE().score(df.caption_en.tolist(), df.ur.tolist())
    if "siglip2" in args.metrics or "siglip2_rel" in args.metrics:
        import numpy as np
        from cocourdu.qe.siglip import SigLIP2
        emb_dir = DATA / "embeddings" / args.siglip_model.split("/")[-1]
        ids = np.load(emb_dir / "image_ids.npy"); emb = np.load(emb_dir / "image_emb.npy").astype(np.float32)
        pos = {int(i): k for k, i in enumerate(ids)}
        img = emb[[pos[int(i)] for i in df.image_id]]
        enc = SigLIP2(args.siglip_model)
        ur = enc.embed_texts(df.ur.tolist()); en = enc.embed_texts(df.caption_en.tolist())
        df["siglip2_ur"] = (img * ur).sum(-1)
        df["siglip2_rel"] = enc.relative_score(img, en, ur)
    df.to_parquet(out, index=False)
    print(df.drop(columns=["caption_en", "ur", "image_url"]).groupby("system").mean(numeric_only=True).round(3))


if __name__ == "__main__":
    main()

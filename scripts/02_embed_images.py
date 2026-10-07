"""Cache SigLIP 2 image embeddings for all images (streamed from the HF per-image dataset; runs on Mac MPS).

Output: data/embeddings/<model>/image_ids.npy, image_emb.npy, splits.npy
"""
import argparse
import io
import sys
from pathlib import Path

import numpy as np
from datasets import load_dataset
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA
from cocourdu.data import DS_IMAGES_V1
from cocourdu.qe.siglip import SIGLIP2_BASE, SigLIP2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=SIGLIP2_BASE)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--limit", type=int, default=None, help="debug: stop after N images")
    args = ap.parse_args()

    out = DATA / "embeddings" / args.model.split("/")[-1]
    out.mkdir(parents=True, exist_ok=True)
    enc = SigLIP2(args.model)
    ids, embs, splits = [], [], []
    for split in ["train", "validation"]:
        ds = load_dataset(DS_IMAGES_V1, split=split, streaming=True)
        batch_imgs, batch_ids = [], []
        for ex in tqdm(ds, desc=split):
            img = ex["image"]
            if isinstance(img, dict):  # streaming may yield {'bytes':..}
                img = Image.open(io.BytesIO(img["bytes"]))
            batch_imgs.append(img.convert("RGB"))
            batch_ids.append(ex["image_id"])
            if len(batch_imgs) == args.batch_size:
                embs.append(enc.embed_images(batch_imgs)); ids += batch_ids; splits += [split] * len(batch_ids)
                batch_imgs, batch_ids = [], []
            if args.limit and len(ids) >= args.limit:
                break
        if batch_imgs:
            embs.append(enc.embed_images(batch_imgs)); ids += batch_ids; splits += [split] * len(batch_ids)
    np.save(out / "image_ids.npy", np.array(ids))
    np.save(out / "image_emb.npy", np.concatenate(embs).astype(np.float16))
    np.save(out / "splits.npy", np.array(splits))
    print(f"saved {len(ids)} embeddings to {out}")


if __name__ == "__main__":
    main()

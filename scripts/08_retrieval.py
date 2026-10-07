"""Urdu text->image / image->text retrieval on cached SigLIP 2 image embeddings (runs on Mac MPS, no Colab).

Vision tower is frozen (embeddings cached by 02_embed_images.py); only the text tower is trained with the SigLIP
sigmoid loss. Conditions = which Urdu column to train on. Eval on the 5K validation images (25K captions).
  python scripts/08_retrieval.py --condition zero_shot
  python scripts/08_retrieval.py --condition seamless   --train-col ur_seamless
  python scripts/08_retrieval.py --condition gemma27b   --train-col ur_gemma27b
  python scripts/08_retrieval.py --condition english    --train-col caption_en
  python scripts/08_retrieval.py --condition qe_top50   --train-col ur_qe_selected --filter-quantile 0.5
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA, RESULTS
from cocourdu.data import load_captions_v1, load_translations
from cocourdu.qe.siglip import SIGLIP2_BASE, SigLIP2


def recall_at_k(sim: np.ndarray, gt_img_idx: np.ndarray, ks=(1, 5, 10)) -> dict:
    """sim: [n_text, n_img]; gt_img_idx[i] = index of the image for text i."""
    out = {}
    rank_t2i = (-sim).argsort(axis=1)
    for k in ks:
        out[f"t2i_R@{k}"] = float(np.mean([gt_img_idx[i] in rank_t2i[i, :k] for i in range(len(gt_img_idx))]))
    rank_i2t = (-sim.T).argsort(axis=1)
    img2texts = {}
    for t, im in enumerate(gt_img_idx):
        img2texts.setdefault(im, set()).add(t)
    for k in ks:
        out[f"i2t_R@{k}"] = float(np.mean([bool(set(rank_i2t[im, :k]) & txts) for im, txts in img2texts.items()]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True)
    ap.add_argument("--train-col", default=None, help="column with training captions; None = zero-shot eval only")
    ap.add_argument("--eval-col", default="ur_seamless", help="validation captions to retrieve with")
    ap.add_argument("--model", default=SIGLIP2_BASE)
    ap.add_argument("--epochs", type=int, default=2); ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch-size", type=int, default=256); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--filter-quantile", type=float, default=None, help="keep train rows with qe_score above this quantile")
    ap.add_argument("--qe-col", default="final_score"); ap.add_argument("--random-subset-frac", type=float, default=None)
    args = ap.parse_args()
    torch.manual_seed(args.seed); np.random.seed(args.seed)

    emb_dir = DATA / "embeddings" / args.model.split("/")[-1]
    ids = np.load(emb_dir / "image_ids.npy"); img_emb = torch.tensor(np.load(emb_dir / "image_emb.npy").astype(np.float32))
    splits = np.load(emb_dir / "splits.npy"); pos = {int(i): k for k, i in enumerate(ids)}
    caps = load_captions_v1()
    for p in sorted((DATA / "translations").glob("*.parquet")) if (DATA / "translations").exists() else []:
        t = pd.read_parquet(p); caps = caps.merge(t[["uid", [c for c in t.columns if c.startswith("ur_")][0]]], on="uid", how="left")
    caps = caps[caps.image_id.isin(pos)]
    enc = SigLIP2(args.model); model, proc, dev = enc.model, enc.proc, enc.device

    train = caps[caps.split == "train"]
    if args.train_col:
        train = train.dropna(subset=[args.train_col])
        if args.filter_quantile is not None:
            train = train[train[args.qe_col] >= train[args.qe_col].quantile(args.filter_quantile)]
        if args.random_subset_frac:
            train = train.sample(frac=args.random_subset_frac, random_state=args.seed)
        for p in model.vision_model.parameters():
            p.requires_grad = False
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.01)
        texts = train[args.train_col].tolist(); tidx = torch.tensor([pos[int(i)] for i in train.image_id])
        model.train()
        for ep in range(args.epochs):
            perm = torch.randperm(len(texts)); tot = 0.0
            for b in range(0, len(texts), args.batch_size):
                sel = perm[b:b + args.batch_size]
                tok = proc(text=[texts[i] for i in sel], padding="max_length", max_length=64, truncation=True, return_tensors="pt").to(dev)
                t = torch.nn.functional.normalize(model.get_text_features(**tok), dim=-1)
                im = img_emb[tidx[sel]].to(dev)
                logits = t @ im.T * model.logit_scale.exp() + model.logit_bias
                labels = 2 * torch.eye(len(sel), device=dev) - 1  # SigLIP sigmoid loss
                loss = -torch.nn.functional.logsigmoid(labels * logits).sum() / len(sel)
                opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item()
            print(f"epoch {ep + 1} loss {tot / max(1, len(texts) // args.batch_size):.4f}")
    model.eval()

    val = caps[(caps.split == "validation")].dropna(subset=[args.eval_col])
    val_img_pos = sorted({pos[int(i)] for i in val.image_id}); remap = {p: k for k, p in enumerate(val_img_pos)}
    gt = np.array([remap[pos[int(i)]] for i in val.image_id])
    with torch.no_grad():
        txt = []
        for b in range(0, len(val), 512):
            tok = proc(text=val[args.eval_col].iloc[b:b + 512].tolist(), padding="max_length", max_length=64, truncation=True, return_tensors="pt").to(dev)
            txt.append(torch.nn.functional.normalize(model.get_text_features(**tok), dim=-1).cpu())
        sim = (torch.cat(txt) @ img_emb[val_img_pos].T).numpy()
    res = {"condition": args.condition, "train_col": args.train_col, "n_train": int(len(train)) if args.train_col else 0, "eval_col": args.eval_col, "seed": args.seed, **recall_at_k(sim, gt)}
    out = RESULTS / "retrieval"; out.mkdir(parents=True, exist_ok=True)
    (out / f"{args.condition}_s{args.seed}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

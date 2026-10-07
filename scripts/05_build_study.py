"""Sample the human-study items and write what the rating tool needs.

- N items stratified over v1 final_score deciles (over-sampling low scores).
- Each item carries every available system's Urdu (seamless + whatever is in data/translations/*.parquet).
- A 'core' subset (rated by ALL raters, for agreement) + the rest assigned to exactly 2 raters.
Output: data/study/items.jsonl (one item per line), data/study/assignment.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA
from cocourdu.data import coco_image_url, load_captions_v1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--core", type=int, default=300, help="items every rater rates (agreement subset)")
    ap.add_argument("--raters", nargs="+", required=True, help="rater ids, e.g. umair friend1 friend2")
    ap.add_argument("--systems", nargs="+", default=None, help="limit to these systems (default: seamless + all in data/translations)")
    ap.add_argument("--low-share", type=float, default=0.4, help="share of items drawn from the bottom 3 deciles")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    caps = load_captions_v1()
    systems = {"seamless": caps.set_index("uid").ur_seamless}
    for p in sorted((DATA / "translations").glob("*.parquet")) if (DATA / "translations").exists() else []:
        t = pd.read_parquet(p); col = [c for c in t.columns if c.startswith("ur_")][0]
        systems[col[3:]] = t.set_index("uid")[col]
    if args.systems:
        systems = {k: v for k, v in systems.items() if k in args.systems}
    # only captions that every system translated
    ok = caps[caps.uid.isin(set.intersection(*[set(s.dropna().index) for s in systems.values()]))].copy()
    ok["decile"] = pd.qcut(ok.final_score.rank(method="first"), 10, labels=False)
    n_low = int(args.n * args.low_share); n_rest = args.n - n_low
    low = ok[ok.decile < 3].sample(n_low, random_state=args.seed)
    rest = ok[ok.decile >= 3].groupby("decile", group_keys=False).apply(lambda g: g.sample(max(1, n_rest // 7), random_state=args.seed))
    items = pd.concat([low, rest]).drop_duplicates("uid").sample(frac=1, random_state=args.seed).reset_index(drop=True)

    out = DATA / "study"; out.mkdir(parents=True, exist_ok=True)
    with (out / "items.jsonl").open("w", encoding="utf-8") as f:
        for i, r in items.iterrows():
            f.write(json.dumps({
                "item_id": f"it{i:05d}", "uid": r.uid, "image_id": int(r.image_id), "split": r.split,
                "image_url": coco_image_url(r.image_id, r.split), "caption_en": r.caption_en,
                "v1_final_score": float(r.final_score), "decile": int(r.decile),
                "versions": {s: str(v.loc[r.uid]) for s, v in systems.items()},
            }, ensure_ascii=False) + "\n")
    ids = [f"it{i:05d}" for i in range(len(items))]
    core, rest_ids = ids[: args.core], ids[args.core:]
    assignment = {r: list(core) for r in args.raters}
    for k, it in enumerate(rest_ids):  # each non-core item -> exactly 2 raters, round-robin
        for j in range(2):
            assignment[args.raters[(k + j) % len(args.raters)]].append(it)
    (out / "assignment.json").write_text(json.dumps({"core": core, "raters": assignment, "systems": list(systems)}, indent=1))
    print(f"{len(items)} items, systems={list(systems)}, core={len(core)}; per-rater items: { {r: len(v) for r, v in assignment.items()} }")
    print(f"ratings needed ≈ {sum(len(v) for v in assignment.values()) * len(systems):,}")


if __name__ == "__main__":
    main()

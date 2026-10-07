"""Reconcile the dataset counts (paper says 59K/319K; HF card shows 63.5K rows) -> results/stats.json + stats.md."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import RESULTS
from cocourdu.data import load_captions_v1, load_image_meta


def main():
    caps = load_captions_v1()
    imgs = load_image_meta()
    n_caps_per_img = imgs.annotations.apply(lambda a: len(a["caption"]))
    stats = {
        "images": {s: int((imgs.split == s).sum()) for s in imgs.split.unique()},
        "images_total": int(len(imgs)),
        "captions": {s: int((caps.split == s).sum()) for s in caps.split.unique()},
        "captions_total": int(len(caps)),
        "captions_per_image": {"mean": float(n_caps_per_img.mean()), "min": int(n_caps_per_img.min()), "max": int(n_caps_per_img.max())},
        "unique_image_ids_in_caption_table": int(caps.image_id.nunique()),
        "qe_v1": {
            m: {"mean": float(caps[m].mean()), "std": float(caps[m].std()), "below_0.7": int((caps[m] < 0.7).sum())}
            for m in ["comet_score", "bert_score", "clip_score", "final_score"]
        },
        "flagged_final_lt_0.7": int((caps.final_score < 0.7).sum()),
        "empty_urdu": int((caps.ur_seamless.fillna("").str.strip() == "").sum()),
        "duplicate_urdu_within_image": int(caps.duplicated(["image_id", "ur_seamless"]).sum()),
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "stats.json").write_text(json.dumps(stats, indent=2))
    md = ["# COCO-Urdu v1 counts (computed from the public HF datasets)", "",
          f"- Images: **{stats['images_total']:,}** ({stats['images']})",
          f"- Captions: **{stats['captions_total']:,}** ({stats['captions']})",
          f"- Captions/image: mean {stats['captions_per_image']['mean']:.2f}, range {stats['captions_per_image']['min']}–{stats['captions_per_image']['max']}",
          f"- Flagged by v1 hybrid score < 0.7: {stats['flagged_final_lt_0.7']:,}",
          f"- Empty Urdu outputs: {stats['empty_urdu']:,}", "",
          "| v1 QE metric | mean | std | n < 0.7 |", "|---|---|---|---|"]
    md += [f"| {m} | {v['mean']:.3f} | {v['std']:.3f} | {v['below_0.7']:,} |" for m, v in stats["qe_v1"].items()]
    (RESULTS / "stats.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()

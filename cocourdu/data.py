"""Load the public COCO-Urdu HF datasets without pulling image bytes.

Parquet column projection over hf:// means only the requested columns are read --
the caption repo is 3.5 GB of shards carrying image bytes, and the text columns are
a small fraction of that. The projection is latency-bound, not bandwidth-bound: each
shard costs many small HTTP range requests, so the shards are read in parallel.
"""
from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfApi, HfFileSystem

from . import DATA
from .log import get_logger

HF_USER = "umairhassan02"
# per-caption table with v1 QE scores (translated_captions = SeamlessM4T v2, references = NLLB-3B)
DS_CAPTIONS_V1 = f"{HF_USER}/coco-captions-subset-59k-translated-final"
# same table after the (circular) Qwen-14B refinement
DS_CAPTIONS_REFINED = f"{HF_USER}/coco-captions-subset-refined"
# per-image release: image bytes + annotations{annotation_id, caption, translated_captions}
DS_IMAGES_V1 = f"{HF_USER}/urdu-translated-coco-captions-subset"

CAPTION_TEXT_COLS = [
    "image_id", "caption", "translated_captions", "references", "back_translation",
    "comet_score", "bert_score", "clip_score", "final_score",
]


def _parquet_files(repo: str, split: str | None = None) -> list[str]:
    files = [f for f in HfApi().list_repo_files(repo, repo_type="dataset") if f.endswith(".parquet")]
    if split:
        files = [f for f in files if Path(f).name.startswith(split)]
    return sorted(files)


def read_hf_parquet(repo: str, columns: list[str], split: str | None = None, workers: int = 8) -> pd.DataFrame:
    """Read selected columns from every parquet shard of an HF dataset, adding a `split` column.

    Shards are fetched concurrently: a 34-shard repo read one at a time takes 15+ minutes,
    which on a GPU runtime is billed idle time.
    """
    log = get_logger()
    files = _parquet_files(repo, split)
    log.info(f"{repo}: reading {len(columns)} columns from {len(files)} shards with {workers} workers")
    done = 0

    def one(f: str) -> pd.DataFrame:
        nonlocal done
        # one filesystem per thread: fsspec's shared instance is not safe for concurrent reads
        fs = HfFileSystem(skip_instance_cache=True)
        df = pq.read_table(f"hf://datasets/{repo}/{f}", columns=columns, filesystem=fs).to_pandas()
        df["split"] = Path(f).name.split("-")[0]
        done += 1
        log.info(f"  shard {done}/{len(files)} ({len(df):,} rows)")
        return df

    with ThreadPoolExecutor(workers) as pool:
        frames = list(pool.map(one, files))
    return pd.concat(frames, ignore_index=True)


def caption_uid(image_id: int, caption_en: str) -> str:
    """Stable per-caption key: COCO image id + hash of the English caption."""
    h = hashlib.sha1(caption_en.strip().encode("utf-8")).hexdigest()[:8]
    return f"{int(image_id)}:{h}"


def load_captions_v1(cache: bool = True) -> pd.DataFrame:
    """Per-caption v1 table: en caption, Seamless Urdu, NLLB ref, back-translation, QE scores."""
    path = DATA / "captions_v1.parquet"
    if cache and path.exists():
        return pd.read_parquet(path)
    df = read_hf_parquet(DS_CAPTIONS_V1, CAPTION_TEXT_COLS)
    df = df.rename(columns={"caption": "caption_en", "translated_captions": "ur_seamless", "references": "ur_nllb_ref"})
    df["uid"] = [caption_uid(i, c) for i, c in zip(df.image_id, df.caption_en)]
    # row order within split is the original dataset index; keep it for joining to legacy JSON ids
    df["row_idx"] = df.groupby("split").cumcount()
    if cache:
        DATA.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
    return df


def load_refined_v1(cache: bool = True) -> pd.DataFrame:
    """Per-caption table after Qwen-14B refinement (both translated_captions and references were rewritten)."""
    path = DATA / "captions_refined_v1.parquet"
    if cache and path.exists():
        return pd.read_parquet(path)
    df = read_hf_parquet(DS_CAPTIONS_REFINED, ["image_id", "caption", "translated_captions", "references", "final_score"])
    df = df.rename(columns={"caption": "caption_en", "translated_captions": "ur_refined_mt", "references": "ur_refined_ref"})
    df["row_idx"] = df.groupby("split").cumcount()
    if cache:
        DATA.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
    return df


def load_image_meta(cache: bool = True) -> pd.DataFrame:
    """Per-image metadata (no bytes): image_id, coco_url, flickr_url, license, annotation ids + captions."""
    path = DATA / "images_meta.parquet"
    if cache and path.exists():
        return pd.read_parquet(path)
    cols = ["image_id", "file_name", "coco_url", "flickr_url", "height", "width", "license_id", "annotations"]
    df = read_hf_parquet(DS_IMAGES_V1, cols)
    if cache:
        DATA.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
    return df


def load_translations(system: str) -> pd.DataFrame:
    """A system's translations: columns uid, ur_<system>. Produced by scripts/03_*.py."""
    path = DATA / "translations" / f"{system}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} — run scripts/03_translate_*.py --system {system}")
    return pd.read_parquet(path)


def coco_image_url(image_id: int, split: str = "train") -> str:
    """Public COCO image URL (train2017 / val2017). Used by the rating tool; no image hosting needed."""
    sub = "val2017" if split == "validation" else "train2017"
    return f"http://images.cocodataset.org/{sub}/{int(image_id):012d}.jpg"

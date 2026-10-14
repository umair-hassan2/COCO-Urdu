"""Move run artifacts between the Mac and Colab through a private HF dataset repo -> no browser uploads.

Everything under data/ and results/ is gitignored, so git cannot carry it and Colab's
files.upload()/files.download() is the only alternative. Both sides address artifacts by their
repo-relative path, which is also the path inside the hub repo:

  Mac    python scripts/sync.py push data/study/items.jsonl
  Colab  !python scripts/sync.py pull data/study/items.jsonl
         !python scripts/sync.py push data/study/qe_scores.parquet
  Either python scripts/sync.py ls data

Separate from the --hf-repo of 03_translate_gemma_vllm.py: that one holds resumable chunk
checkpoints mid-run, this one holds finished artifacts the next pipeline step consumes.
Repo defaults to COCOURDU_SYNC_REPO or the constant below; created private on first push.
"""
import argparse
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import ROOT
from cocourdu.log import get_logger

DEFAULT_REPO = os.environ.get("COCOURDU_SYNC_REPO", "umairhassan02/coco-urdu-v2-artifacts")


def rel(p: str) -> str:
    """Repo-relative, posix path — the same key on both machines and inside the hub repo."""
    path = Path(p)
    path = path if path.is_absolute() else Path.cwd() / path
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        raise SystemExit(f"{p} is outside the repo ({ROOT}); sync only moves paths under it")


def mb(n: int) -> str:
    return f"{n / 1e6:.1f} MB"


def push(api, repo, paths, log, if_present=False):
    api.create_repo(repo, repo_type="dataset", private=True, exist_ok=True)
    for p in paths:
        name = rel(p)
        local = ROOT / name
        if not local.exists():
            (log.info if if_present else log.error)(f"skip {name} — not on this machine")
            continue
        if local.is_dir():
            files = [f for f in local.rglob("*") if f.is_file()]
            if not files:
                log.error(f"empty directory: {name}")
                continue
            api.upload_folder(folder_path=str(local), path_in_repo=name, repo_id=repo, repo_type="dataset")
            log.info(f"pushed {name}/ — {len(files)} files, {mb(sum(f.stat().st_size for f in files))}")
        else:
            api.upload_file(path_or_fileobj=str(local), path_in_repo=name, repo_id=repo, repo_type="dataset")
            log.info(f"pushed {name} — {mb(local.stat().st_size)}")


def matching(api, repo, name):
    """Files in the repo at `name`, or under it when `name` is a directory."""
    files = api.list_repo_files(repo, repo_type="dataset")
    return [f for f in files if f == name or f.startswith(name.rstrip("/") + "/")]


def pull(api, repo, paths, log, if_present=False):
    for p in paths:
        name = rel(p)
        want = matching(api, repo, name)
        if not want:
            (log.info if if_present else log.error)(f"skip {name} — not in {repo} yet")
            continue
        for f in sorted(want):
            hf_hub_download(repo, f, repo_type="dataset", local_dir=str(ROOT))
            log.info(f"pulled {f} — {mb((ROOT / f).stat().st_size)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["push", "pull", "ls"])
    ap.add_argument("paths", nargs="*", default=[], help="repo-relative files or directories")
    ap.add_argument("--repo", default=DEFAULT_REPO, help=f"private HF dataset repo (default {DEFAULT_REPO})")
    ap.add_argument("--if-present", action="store_true", help="skip missing paths instead of erroring (optional artifacts)")
    args = ap.parse_args()

    log = get_logger()
    api = HfApi()
    if args.action == "ls":
        prefix = rel(args.paths[0]) if args.paths else ""
        files = sorted(f for f in api.list_repo_files(args.repo, repo_type="dataset") if f.startswith(prefix))
        log.info(f"{len(files)} file(s) in {args.repo}" + (f" under {prefix}" if prefix else ""))
        for f in files:
            print(" ", f)
        return
    if not args.paths:
        raise SystemExit(f"{args.action} needs at least one path")
    (push if args.action == "push" else pull)(api, args.repo, args.paths, log, args.if_present)


if __name__ == "__main__":
    main()

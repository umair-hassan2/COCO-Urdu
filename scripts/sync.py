"""CLI for moving run artifacts between the Mac and Colab. See cocourdu/sync.py for the mechanics.

  Mac    python scripts/sync.py push data/study/items.jsonl
  Colab  !python scripts/sync.py pull data/study/items.jsonl
  Either python scripts/sync.py ls data
"""
import argparse
import sys
from pathlib import Path

from huggingface_hub import HfApi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu.log import get_logger
from cocourdu.sync import DEFAULT_REPO, pull, push, rel


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

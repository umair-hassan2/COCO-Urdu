"""Move run artifacts between the Mac and Colab through a private HF dataset repo.

Everything under data/ and results/ is gitignored, so git cannot carry it and Colab's
files.upload()/files.download() is the only alternative. Both sides address artifacts by
their repo-relative path, which is also the path inside the hub repo.

`scripts/sync.py` is the CLI over this; `data.py` uses try_pull/try_push so a cache one
machine built is never rebuilt on the other. Separate from the --hf-repo of
03_translate_gemma_vllm.py: that holds mid-run chunk checkpoints, this holds finished
artifacts. Repo defaults to COCOURDU_SYNC_REPO or the constant below; private on creation.
"""
from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

from . import ROOT
from .log import get_logger

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


def try_pull(path: Path, repo: str = DEFAULT_REPO) -> bool:
    """Fetch one artifact if the hub has it. Never raises: no network or no auth just means False."""
    log = get_logger()
    try:
        pull(HfApi(), repo, [str(path)], log, if_present=True)
        return path.exists()
    except Exception as e:
        log.info(f"could not reach {repo} ({type(e).__name__}); building locally instead")
        return False


def try_push(path: Path, repo: str = DEFAULT_REPO) -> None:
    """Share a freshly built artifact so the other machine never rebuilds it. Never raises."""
    log = get_logger()
    try:
        push(HfApi(), repo, [str(path)], log)
    except Exception as e:
        log.info(f"could not push {path.name} to {repo} ({type(e).__name__}); keeping it local")

"""Translate captions with any OpenAI-compatible chat endpoint (OpenAI, Gemini OpenAI-compat, local vLLM server).

Resumable: appends to data/translations/<system>.jsonl, skips done uids, then writes <system>.parquet.
Examples:
  OPENAI_API_KEY=... python scripts/03_translate_api.py --system gpt4omini --model gpt-4o-mini
  GEMINI_API_KEY=... python scripts/03_translate_api.py --system gemini_flash --model gemini-2.5-flash \
      --base-url https://generativelanguage.googleapis.com/v1beta/openai/ --api-key-env GEMINI_API_KEY
  python scripts/03_translate_api.py --system gemma27b --model google/gemma-3-27b-it --base-url http://localhost:8000/v1 --api-key-env NONE
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA
from cocourdu.data import load_captions_v1
from cocourdu.prompts import FEW_SHOT, SYSTEM_PROMPT, parse_translation


async def worker(client, model, queue, out_f, pbar, sem, max_retries=5):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done(); return
        uid, en = item
        for attempt in range(max_retries):
            try:
                async with sem:
                    resp = await client.chat.completions.create(
                        model=model, temperature=0, max_tokens=200,
                        messages=[{"role": "system", "content": SYSTEM_PROMPT}, *FEW_SHOT, {"role": "user", "content": en}])
                ur = parse_translation(resp.choices[0].message.content or "")
                out_f.write(json.dumps({"uid": uid, "caption_en": en, "ur": ur}, ensure_ascii=False) + "\n"); out_f.flush()
                break
            except Exception as e:  # rate limits, transient errors
                await asyncio.sleep(min(60, 2 ** attempt))
                if attempt == max_retries - 1:
                    out_f.write(json.dumps({"uid": uid, "caption_en": en, "ur": None, "error": str(e)[:200]}, ensure_ascii=False) + "\n")
        pbar.update(1); queue.task_done()


async def run(args):
    from openai import AsyncOpenAI
    api_key = None if args.api_key_env == "NONE" else os.environ[args.api_key_env]
    client = AsyncOpenAI(base_url=args.base_url, api_key=api_key or "none")
    caps = load_captions_v1()
    if args.limit:
        caps = caps.sample(args.limit, random_state=0) if args.random else caps.head(args.limit)
    out_dir = DATA / "translations"; out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / f"{args.system}.jsonl"
    done = set()
    if jsonl.exists():
        done = {json.loads(l)["uid"] for l in jsonl.open(encoding="utf-8") if l.strip()}
    todo = caps[~caps.uid.isin(done)][["uid", "caption_en"]].drop_duplicates("uid")
    print(f"{len(done)} done, {len(todo)} to translate with {args.model}")
    queue = asyncio.Queue()
    for row in todo.itertuples(index=False):
        queue.put_nowait((row.uid, row.caption_en))
    for _ in range(args.concurrency):
        queue.put_nowait(None)
    sem = asyncio.Semaphore(args.concurrency)
    with jsonl.open("a", encoding="utf-8") as f, tqdm(total=len(todo)) as pbar:
        await asyncio.gather(*[worker(client, args.model, queue, f, pbar, sem) for _ in range(args.concurrency)])
    rows = [json.loads(l) for l in jsonl.open(encoding="utf-8") if l.strip()]
    df = pd.DataFrame(rows).drop_duplicates("uid", keep="last").rename(columns={"ur": f"ur_{args.system}"})
    df.to_parquet(out_dir / f"{args.system}.parquet", index=False)
    print(f"wrote {len(df)} rows ({df[f'ur_{args.system}'].isna().sum()} failed) -> {out_dir / (args.system + '.parquet')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, help="short name, becomes column ur_<system>")
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--api-key-env", default="OPENAI_API_KEY")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--limit", type=int, default=None, help="sanity run: translate only N captions")
    ap.add_argument("--random", action="store_true", help="with --limit, sample randomly instead of head")
    asyncio.run(run(ap.parse_args()))


if __name__ == "__main__":
    main()

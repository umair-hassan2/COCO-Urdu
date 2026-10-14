"""The v2 translator: offline vLLM on Colab A100 40GB (Gemma 3 27B in 4-bit) — chunked and resumable via HF Hub.

Each chunk of captions -> parquet -> uploaded to a private HF dataset repo under chunks/<system>/<start>-<end>.parquet.
Re-running skips chunks that already exist, so Colab disconnects cost nothing. Merge with --merge at the end.

Colab:
  !pip install -q vllm pandas pyarrow huggingface_hub datasets
  !huggingface-cli login
  !python scripts/03_translate_gemma_vllm.py --system gemma27b --model <AWQ-or-GPTQ repo of gemma-3-27b-it> --hf-repo <user>/coco-urdu-v2-chunks
  !python scripts/03_translate_gemma_vllm.py --system gemma27b --hf-repo <user>/coco-urdu-v2-chunks --merge

Verify the quantized checkpoint before the full run (1K-item sanity pass + scripts/04_sanity_check.py).
"""
import argparse
import io
import sys
import time
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA
from cocourdu.data import load_captions_v1
from cocourdu.log import Progress, get_logger
from cocourdu.prompts import FEW_SHOT, SYSTEM_PROMPT, parse_translation


def chunk_name(system, start, end):
    return f"chunks/{system}/{start:07d}-{end:07d}.parquet"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--model", default=None, help="HF model id (quantized gemma-3-27b-it for A100 40GB; gemma-3-12b-it bf16 fits L4 24GB)")
    ap.add_argument("--quantization", default=None, help="vLLM quantization name, e.g. awq, gptq, bitsandbytes; None = infer from checkpoint")
    ap.add_argument("--hf-repo", required=True, help="private dataset repo for chunk checkpoints")
    ap.add_argument("--chunk-size", type=int, default=20000)
    ap.add_argument("--limit", type=int, default=None, help="sanity run on first N captions")
    ap.add_argument("--max-model-len", type=int, default=1024)
    ap.add_argument("--merge", action="store_true", help="download all chunks and write data/translations/<system>.parquet")
    args = ap.parse_args()

    log = get_logger()
    api = HfApi()
    api.create_repo(args.hf_repo, repo_type="dataset", private=True, exist_ok=True)
    existing = set(api.list_repo_files(args.hf_repo, repo_type="dataset"))

    if args.merge:
        files = sorted(f for f in existing if f.startswith(f"chunks/{args.system}/"))
        dfs = [pd.read_parquet(hf_hub_download(args.hf_repo, f, repo_type="dataset")) for f in files]
        df = pd.concat(dfs, ignore_index=True).drop_duplicates("uid")
        out = DATA / "translations"; out.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out / f"{args.system}.parquet", index=False)
        log.info(f"merged {len(files)} chunks -> {len(df)} rows -> {out / (args.system + '.parquet')}")
        return

    log.info("importing vllm (~1 min on a cold runtime)")
    from vllm import LLM, SamplingParams
    log.info("loading captions from the HF dataset (cached to data/captions_v1.parquet after the first run)")
    caps = load_captions_v1()[["uid", "caption_en"]].drop_duplicates("uid").reset_index(drop=True)
    if args.limit:
        caps = caps.head(args.limit)
    n_chunks = -(-len(caps) // args.chunk_size)
    have = sum(1 for f in existing if f.startswith(f'chunks/{args.system}/'))
    log.info(f"{len(caps):,} captions → {n_chunks} chunks of {args.chunk_size}; {have} already on the Hub; model={args.model}")
    log.info(f"loading {args.model} — downloads ~20 GB on a cold runtime, watch the Resources panel")
    t_load = time.time()
    llm = LLM(model=args.model, quantization=args.quantization, max_model_len=args.max_model_len, dtype="auto", gpu_memory_utilization=0.92)
    tok = llm.get_tokenizer()
    log.info(f"model loaded in {time.time() - t_load:.0f}s")
    prog = Progress(len(caps), log, 'captions')
    sp = SamplingParams(temperature=0, max_tokens=160)

    def build(en):
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, *FEW_SHOT, {"role": "user", "content": en}]
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    for start in range(0, len(caps), args.chunk_size):
        end = min(start + args.chunk_size, len(caps))
        name = chunk_name(args.system, start, end)
        if name in existing:
            log.info(f"skip {name} (exists)"); prog.done += end - start; continue
        sub = caps.iloc[start:end]
        log.info(f"chunk {start // args.chunk_size + 1}/{n_chunks}: generating {len(sub):,} captions")
        outs = llm.generate([build(en) for en in sub.caption_en], sp)
        ur = [parse_translation(o.outputs[0].text) for o in outs]
        df = pd.DataFrame({"uid": sub.uid.values, "caption_en": sub.caption_en.values, f"ur_{args.system}": ur})
        buf = io.BytesIO(); df.to_parquet(buf, index=False); buf.seek(0)
        api.upload_file(path_or_fileobj=buf, path_in_repo=name, repo_id=args.hf_repo, repo_type="dataset")
        empty = sum(1 for u in ur if not u)
        prog.step(len(df), f"chunk {start // args.chunk_size + 1}/{n_chunks} uploaded ({empty} empty outputs)")


if __name__ == "__main__":
    main()

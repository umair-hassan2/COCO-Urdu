"""Zero-shot Urdu captioning baselines on N validation images (Colab L4; ~1 h per 7B model).

  python scripts/10_vlm_zero_shot.py --model Qwen/Qwen2.5-VL-7B-Instruct --n 500
  python scripts/10_vlm_zero_shot.py --model google/gemma-3-12b-it --n 500
Outputs results/vlm/<model>.jsonl and chrF++/BLEU vs the Urdu references in --ref-col (MT-derived; say so in the paper).
"""
import argparse
import io
import json
import sys
from pathlib import Path

import sacrebleu
import torch
from datasets import load_dataset
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import RESULTS
from cocourdu.data import DS_IMAGES_V1

PROMPT = "اس تصویر کا ایک جملے میں اردو میں بیان کریں۔ صرف اردو جملہ لکھیں۔"  # describe this image in one Urdu sentence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--max-new-tokens", type=int, default=80)
    args = ap.parse_args()
    from transformers import AutoModelForImageTextToText, AutoProcessor
    proc = AutoProcessor.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="auto").eval()
    out_dir = RESULTS / "vlm"; out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model.split('/')[-1]}.jsonl"
    done = {json.loads(l)["image_id"] for l in out.open()} if out.exists() else set()
    ds = load_dataset(DS_IMAGES_V1, split="validation", streaming=True)
    hyps, refs = [], []
    with out.open("a", encoding="utf-8") as f:
        for i, ex in enumerate(tqdm(ds, total=args.n)):
            if i >= args.n:
                break
            if ex["image_id"] in done:
                continue
            img = ex["image"]; img = Image.open(io.BytesIO(img["bytes"])) if isinstance(img, dict) else img
            msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
            text = proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
            inputs = proc(text=[text], images=[img.convert("RGB")], return_tensors="pt").to(model.device)
            with torch.no_grad():
                gen = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
            hyp = proc.batch_decode(gen[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip()
            rec = {"image_id": ex["image_id"], "hyp": hyp, "refs": ex["annotations"]["translated_captions"]}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); hyps.append(hyp); refs.append(rec["refs"])
    rows = [json.loads(l) for l in out.open(encoding="utf-8")]
    hyps = [r["hyp"] for r in rows]; refs = [r["refs"] for r in rows]
    k = min(len(r) for r in refs); ref_sets = [[r[j] for r in refs] for j in range(k)]
    res = {"model": args.model, "n": len(rows), "chrF++": sacrebleu.corpus_chrf(hyps, ref_sets, word_order=2).score, "BLEU": sacrebleu.corpus_bleu(hyps, ref_sets, tokenize="flores200").score}
    (out_dir / f"{args.model.split('/')[-1]}_metrics.json").write_text(json.dumps(res, indent=1)); print(res)


if __name__ == "__main__":
    main()

"""Build an Urdu word list for non-word detection from fineweb-2 (urd_Arab), streamed. -> data/lexicon/urdu_words.txt

Keeps tokens seen >= --min-count times in --docs documents (default 50K docs ≈ a few minutes).
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA
from cocourdu.urdu_text import ARABIC_BLOCK, tokenize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=50000)
    ap.add_argument("--min-count", type=int, default=3)
    args = ap.parse_args()
    ds = load_dataset("HuggingFaceFW/fineweb-2", name="urd_Arab", split="train", streaming=True)
    counts = Counter()
    for i, ex in enumerate(tqdm(ds, total=args.docs)):
        counts.update(t for t in tokenize(ex["text"]) if ARABIC_BLOCK.search(t))
        if i + 1 >= args.docs:
            break
    words = [w for w, c in counts.items() if c >= args.min_count]
    out = DATA / "lexicon"; out.mkdir(parents=True, exist_ok=True)
    (out / "urdu_words.txt").write_text("\n".join(sorted(words)), encoding="utf-8")
    print(f"{len(words):,} words (>= {args.min_count} occurrences in {args.docs:,} docs) -> {out / 'urdu_words.txt'}")


if __name__ == "__main__":
    main()

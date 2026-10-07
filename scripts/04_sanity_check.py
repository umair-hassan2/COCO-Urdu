"""Automatic sanity checks on a translation file (run on the 1K sanity pass BEFORE the full run, and after).

Reports: empty, untranslated English, wrong script, length-ratio outliers, repeated n-grams, OOV (non-word) rate.
Usage: python scripts/04_sanity_check.py --translations data/translations/gemma27b.parquet [--lexicon data/lexicon/urdu_words.txt]
       python scripts/04_sanity_check.py --v1   # same checks on v1 SeamlessM4T output
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA, RESULTS
from cocourdu.data import load_captions_v1
from cocourdu.urdu_text import Lexicon, caption_checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--translations", help="parquet with uid + ur_<system>")
    ap.add_argument("--v1", action="store_true", help="check v1 ur_seamless instead")
    ap.add_argument("--lexicon", default=str(DATA / "lexicon" / "urdu_words.txt"))
    ap.add_argument("--examples", type=int, default=15)
    args = ap.parse_args()

    caps = load_captions_v1()[["uid", "caption_en", "ur_seamless"]]
    if args.v1:
        df, col, name = caps.rename(columns={"ur_seamless": "ur"}), "ur", "seamless_v1"
    else:
        t = pd.read_parquet(args.translations)
        col = [c for c in t.columns if c.startswith("ur_")][0]
        name = col[3:]
        df = caps.drop(columns="ur_seamless").merge(t[["uid", col]], on="uid").rename(columns={col: "ur"})
    lex = Lexicon.load(args.lexicon) if Path(args.lexicon).exists() else None
    checks = pd.DataFrame([caption_checks(e, u or "", lex) for e, u in zip(df.caption_en, df.ur)])
    flags = [c for c in checks.columns if checks[c].dtype == bool]
    summary = {c: f"{checks[c].mean():.2%} ({int(checks[c].sum())})" for c in flags}
    summary["len_ratio_mean"] = f"{checks.len_ratio.mean():.2f}"
    md = [f"# Sanity check: {name} ({len(df):,} captions)", "", "| check | rate (count) |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in summary.items()]
    if lex is not None:
        oov = Counter(t for toks in checks.oov_tokens for t in toks)
        md += ["", f"Top OOV tokens (lexicon {len(lex.words):,} words): " + ", ".join(f"{w} ({c})" for w, c in oov.most_common(40))]
    bad = df[checks[[c for c in flags if c != "has_oov"]].any(axis=1)].head(args.examples)
    md += ["", "## Example flagged rows", ""] + [f"- EN: {r.caption_en}\n  UR: {r.ur}" for r in bad.itertuples()]
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"sanity_{name}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    pd.concat([df.reset_index(drop=True), checks], axis=1).to_parquet(RESULTS / f"sanity_{name}.parquet", index=False)
    print("\n".join(md[:len(summary) + 4]), f"\n-> {out}")


if __name__ == "__main__":
    main()

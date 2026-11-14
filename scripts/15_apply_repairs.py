"""Apply the reviewed repair map to a translation file, leaving a full before/after audit trail.

  python scripts/15_apply_repairs.py --translations data/translations/gemma27b.parquet
  python scripts/15_apply_repairs.py --translations ... --verified-only   # skip unreviewed rows

The raw model output is never modified -- it is the evidence for docs/FINDINGS.md Finding 1.
Writes:
  data/translations/<system>_repaired.parquet   the corpus downstream steps consume
  results/contamination_before.txt              every affected caption, foreign characters bracketed
  results/contamination_after.txt               the same captions, same order, after repair
  results/contamination_diff.txt                uid-keyed before/after pairs for review
  results/repair_report.md                      what was applied, what is left
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA, RESULTS, ROOT
from cocourdu.urdu_text import foreign_script_chars, tokenize, _has_repeated_ngram

BRACKETS = ("⟦", "⟧")


def highlight(text):
    return "".join(f"{BRACKETS[0]}{c}{BRACKETS[1]}" if foreign_script_chars(c) else c for c in text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--translations", required=True)
    ap.add_argument("--map", default=None, help="default: repairs/script_contamination_<system>.tsv")
    ap.add_argument("--verified-only", action="store_true", help="apply only rows marked status=verified")
    args = ap.parse_args()

    t = pd.read_parquet(args.translations)
    col = [c for c in t.columns if c.startswith("ur_")][0]
    system = col[3:]
    mp = Path(args.map) if args.map else ROOT / "repairs" / f"script_contamination_{system}.tsv"
    rows = list(csv.DictReader(mp.open(encoding="utf-8"), delimiter="\t"))

    # A verified row with an empty replacement means "delete this token" -- the neighbouring
    # token carries the whole phrase (e.g. 'ال 字 کی شکل' = L-shaped).
    usable = [r for r in rows if r["status"] == "verified"
              or (r["replacement"].strip() and r["status"] != "rejected")]
    if args.verified_only:
        usable = [r for r in usable if r["status"] == "verified"]
    sub = {r["form"]: r["replacement"].strip() for r in usable}
    by_status = Counter(r["status"] for r in usable)

    before = t[col].fillna("")
    affected = before.map(lambda s: bool(foreign_script_chars(s)))
    after = before.map(lambda s: " ".join(t for t in (sub.get(tok, tok) for tok in s.split()) if t))

    repaired = t.copy()
    repaired[col] = after
    out_parquet = DATA / "translations" / f"{system}_repaired.parquet"
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    repaired.to_parquet(out_parquet, index=False)

    idx = before.index[affected]
    RESULTS.mkdir(exist_ok=True)
    hdr = (f"# Cross-script contamination in {system}: {len(idx):,} affected captions\n"
           f"# Foreign-script characters are bracketed {BRACKETS[0]} {BRACKETS[1]}.\n"
           f"# Paired line-for-line with contamination_after.txt. See docs/FINDINGS.md Finding 1.\n\n")
    (RESULTS / "contamination_before.txt").write_text(
        hdr + "".join(f"{t.uid[i]}\t{highlight(before[i])}\n" for i in idx), encoding="utf-8")
    (RESULTS / "contamination_after.txt").write_text(
        hdr.replace("Foreign-script characters are bracketed", "After repair; any remaining foreign characters are bracketed")
        + "".join(f"{t.uid[i]}\t{highlight(after[i])}\n" for i in idx), encoding="utf-8")
    (RESULTS / "contamination_diff.txt").write_text(
        hdr + "".join(f"uid: {t.uid[i]}\n  en    : {t.caption_en[i]}\n  before: {highlight(before[i])}\n"
                      f"  after : {highlight(after[i])}\n\n" for i in idx), encoding="utf-8")

    left = after.map(lambda s: bool(foreign_script_chars(s)))
    unfixed = Counter(tok for s in after[left] for tok in s.split() if foreign_script_chars(tok))
    degenerate = [i for i in idx if _has_repeated_ngram(tokenize(after[i]), 3)]

    md = [f"# Repair report: {system}", "",
          f"Source: `{args.translations}` ({len(t):,} captions) · map: `{mp.relative_to(ROOT)}`",
          f"Repaired corpus: `{out_parquet.relative_to(ROOT)}` — the raw file is left untouched.", "",
          "| | forms | occurrences |", "|---|---|---|"]
    for st, k in by_status.most_common():
        md.append(f"| applied ({st}) | {k} | {sum(int(r['occurrences']) for r in usable if r['status'] == st):,} |")
    md += ["", "| | captions | rate |", "|---|---|---|",
           f"| contaminated before | {int(affected.sum()):,} | {affected.mean():.3%} |",
           f"| contaminated after | {int(left.sum()):,} | {left.mean():.3%} |",
           f"| repaired | {int(affected.sum()) - int(left.sum()):,} | — |"]
    if len(unfixed):
        md += ["", f"## Still contaminated ({len(unfixed)} forms)", "",
               "Rows in the map with an empty `replacement`, or marked `rejected`.", "",
               "| form | occurrences |", "|---|---|"]
        md += [f"| `{w}` | {c:,} |" for w, c in unfixed.most_common(25)]
    if degenerate:
        md += ["", f"## Degenerate captions ({len(degenerate)})", "",
               "These repeat a phrase and cannot be fixed by substitution — regenerate or exclude them.", ""]
        md += [f"- `{t.uid[i]}` — {t.caption_en[i]}" for i in degenerate[:10]]
    md += ["", "## Audit trail", "",
           "- `results/contamination_before.txt` — every affected caption, as the model produced it",
           "- `results/contamination_after.txt` — the same captions, same order, after repair",
           "- `results/contamination_diff.txt` — uid, English source, before and after together"]
    (RESULTS / "repair_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

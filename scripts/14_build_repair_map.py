"""Build the editable repair map for cross-script contamination -> repairs/script_contamination_<system>.tsv

One row per contaminated word-form, with a pre-filled proposal from cocourdu.translit. A human edits
the `replacement` column and sets `status` to `verified`; scripts/15_apply_repairs.py then applies it.

  python scripts/14_build_repair_map.py --translations data/translations/gemma27b.parquet
  python scripts/14_build_repair_map.py --translations ... --preserve   # keep edits already made

Columns
  rank          by occurrence count, so the high-value rows sort to the top
  form          the contaminated word-form, verbatim
  occurrences   how many times it appears
  captions      how many distinct captions it appears in (one caption can repeat a form)
  codepoints    the foreign characters, as U+XXXX -- readable without an RTL-capable renderer
  scripts       which writing systems they come from
  class         auto | needs-review | needs-translation (see cocourdu.translit.classify)
  proposal      machine transliteration; never applied on its own
  replacement   what will actually be substituted -- EDIT THIS
  status        proposed | verified | rejected  -- set `verified` once a human has checked the row
  example_en    an English source caption containing the form
  example_ur    the Urdu output containing the form
"""
import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import ROOT
from cocourdu.translit import classify, transliterate
from cocourdu.urdu_text import foreign_script_chars, script_of

FIELDS = ["rank", "form", "occurrences", "captions", "codepoints", "scripts", "class",
          "proposal", "replacement", "status", "example_en", "example_ur"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--translations", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--preserve", action="store_true", help="keep `replacement`/`status` from the existing file")
    args = ap.parse_args()

    t = pd.read_parquet(args.translations)
    col = [c for c in t.columns if c.startswith("ur_")][0]
    system = col[3:]
    out = Path(args.out) if args.out else ROOT / "repairs" / f"script_contamination_{system}.tsv"

    kept = {}
    if args.preserve and out.exists():
        with out.open(encoding="utf-8", newline="") as fh:
            kept = {r["form"]: (r["replacement"], r["status"]) for r in csv.DictReader(fh, delimiter="\t")}

    occ, caps, ex = Counter(), defaultdict(set), {}
    for i, (en, ur) in enumerate(zip(t.caption_en, t[col].fillna(""))):
        for tok in ur.split():
            if foreign_script_chars(tok):
                occ[tok] += 1
                caps[tok].add(i)
                ex.setdefault(tok, (en, ur))

    rows = []
    for rank, (form, n) in enumerate(occ.most_common(), 1):
        foreign = foreign_script_chars(form)
        proposal = transliterate(form)
        replacement, status = kept.get(form, (proposal, "proposed"))
        en, ur = ex[form]
        rows.append({
            "rank": rank, "form": form, "occurrences": n, "captions": len(caps[form]),
            "codepoints": " ".join(f"U+{ord(c):04X}" for c in dict.fromkeys(foreign)),
            "scripts": ",".join(sorted({script_of(c) for c in foreign})),
            "class": classify(form), "proposal": proposal, "replacement": replacement,
            "status": status,
            "example_en": en.replace("\t", " ").strip(), "example_ur": ur.replace("\t", " ").strip(),
        })

    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    by_class = Counter(r["class"] for r in rows)
    verified = sum(1 for r in rows if r["status"] == "verified")
    print(f"{len(rows):,} forms, {sum(occ.values()):,} occurrences -> {out}")
    for k, v in by_class.most_common():
        print(f"  {k:<18} {v:>4} forms  {sum(r['occurrences'] for r in rows if r['class'] == k):>6,} occurrences")
    print(f"  verified so far    {verified:>4} / {len(rows)}")


if __name__ == "__main__":
    main()

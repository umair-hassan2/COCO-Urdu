"""
Finds captions containing a character from a writing system other than Urdu's -- katakana, Devanagari,
Cyrillic and others -- which `wrong_script` in 04_sanity_check cannot see, because one stray character
leaves a caption's Arabic ratio near 1.0.
"""
import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import RESULTS, ROOT
from cocourdu.data import load_captions_v1
from cocourdu.urdu_text import ARABIC_BLOCK, foreign_script_chars, script_of

# COCO nouns whose translations the v2 model most often mis-scripts; --trigger-words to override.
TRIGGERS = ["frisbee", "owl", "jeans", "skirt", "snowboard", "tomato", "statue", "broccoli",
            "ski", "skier", "skateboard", "zebra", "giraffe", "elephant", "umbrella", "scissors",
            "graffiti", "teddy", "pepperoni", "stroller", "chopstick"]


def codepoints(chars):
    return " ".join(f"U+{ord(c):04X}" for c in dict.fromkeys(chars))


def highlight(text, marks=("⟦", "⟧")):
    """Bracket every foreign-script character so it is visible in a terminal or a diff."""
    return "".join(f"{marks[0]}{c}{marks[1]}" if foreign_script_chars(c) else c for c in text)


def load(args):
    if args.v1:
        caps = load_captions_v1()
        return caps[["uid", "caption_en", "ur_seamless"]].rename(columns={"ur_seamless": "ur"}), "seamless_v1"
    t = pd.read_parquet(args.translations)
    col = [c for c in t.columns if c.startswith("ur_")][0]
    if "caption_en" not in t.columns:
        t = t.merge(load_captions_v1()[["uid", "caption_en"]], on="uid")
    return t[["uid", "caption_en", col]].rename(columns={col: "ur"}), col[3:]


def flag(df):
    df = df.copy()
    df["ur"] = df.ur.fillna("")
    df["foreign_chars"] = df.ur.map(foreign_script_chars)
    df["n_foreign"] = df.foreign_chars.map(len)
    df["scripts"] = df.foreign_chars.map(lambda cs: sorted({script_of(c) for c in cs}))
    df["codepoints"] = df.foreign_chars.map(codepoints)
    return df


def tokens(df):
    """Contaminated word-forms and their counts."""
    c = Counter()
    for s in df.ur:
        c.update(t for t in s.split() if foreign_script_chars(t))
    return c


def summary_block(df, n, title):
    """Headline count plus the by-writing-system table -- used for both before and after."""
    hit = df[df.n_foreign > 0]
    distinct = len(set().union(*df.foreign_chars)) if len(hit) else 0
    caps = Counter(sc for ss in hit.scripts for sc in ss)
    chars = Counter(script_of(c) for cs in df.foreign_chars for c in cs)
    md = [title, "",
          f"**{len(hit):,} of {n:,} captions ({len(hit) / n:.3%})** are affected: "
          f"{int(df.n_foreign.sum()):,} characters, {distinct} distinct."]
    if len(hit):
        md += ["", "| script | captions | % of corpus | characters |", "|---|---|---|---|"]
        md += [f"| {sc} | {c:,} | {c / n:.3%} | {chars[sc]:,} |" for sc, c in caps.most_common()]
    return md


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--translations", help="parquet with uid + ur_<system>")
    src.add_argument("--v1", action="store_true", help="check the v1 SeamlessM4T output instead")
    ap.add_argument("--compare-v1", action="store_true", help="add the v1 SeamlessM4T rate as a baseline row")
    ap.add_argument("--word", help="print every caption containing this word-form, then exit")
    ap.add_argument("--show", type=int, default=20, help="highlighted examples in the report")
    ap.add_argument("--top", type=int, default=25, help="rows in the word-form table")
    ap.add_argument("--trigger-words", nargs="+", default=TRIGGERS)
    ap.add_argument("--after", default=None,
                    help="repaired parquet to re-check and append as an AFTER FIXING section "
                         "(default: <system>_repaired.parquet beside the input, if it exists)")
    args = ap.parse_args()

    df, name = load(args)
    n = len(df)
    df = flag(df)
    hit = df[df.n_foreign > 0]

    if args.word:
        sub = df[df.ur.str.contains(re.escape(args.word), regex=True)]
        print(f"{len(sub):,} caption(s) containing {args.word!r}  [{codepoints(foreign_script_chars(args.word))}]\n")
        for r in sub.itertuples():
            print(f"  EN: {r.caption_en}\n  UR: {highlight(r.ur)}\n")
        return

    md = [f"# Cross-script contamination: {name}", "",
          f"Source: `{args.translations or 'captions_v1.ur_seamless'}` — {n:,} captions.",
          "A caption is flagged if it contains a character outside the Arabic/Urdu blocks, Latin,",
          "digits and shared punctuation (`cocourdu.urdu_text.URDU_OK`).", "",
          f"**{len(hit):,} of {n:,} captions ({len(hit) / n:.3%})** are affected: "
          f"{int(df.n_foreign.sum()):,} characters, {len(set().union(*df.foreign_chars)) if len(hit) else 0} distinct."]

    if args.compare_v1 and not args.v1:
        v1 = flag(load_captions_v1()[["uid", "caption_en", "ur_seamless"]].rename(columns={"ur_seamless": "ur"}))
        v1_hit = int((v1.n_foreign > 0).sum())
        md += ["", "| system | affected | rate |", "|---|---|---|",
               f"| {name} | {len(hit):,} | **{len(hit) / n:.3%}** |",
               f"| seamless_v1 | {v1_hit:,} | {v1_hit / len(v1):.3%} |", ""]
        if v1_hit:
            md.append(f"A **{(len(hit) / n) / (v1_hit / len(v1)):.0f}x** difference "
                      f"on the same {n:,} source captions.")
        else:
            md.append(f"SeamlessM4T produces **none** on the same {n:,} source captions.")

    by_script_caps = Counter(s for ss in hit.scripts for s in ss)
    by_script_chars = Counter(script_of(c) for cs in df.foreign_chars for c in cs)
    md += ["", "## By writing system", "", "| script | captions | % of corpus | characters |", "|---|---|---|---|"]
    md += [f"| {s} | {c:,} | {c / n:.3%} | {by_script_chars[s]:,} |" for s, c in by_script_caps.most_common()]

    mixed = sum(1 for s in hit.ur for t in s.split() if foreign_script_chars(t) and ARABIC_BLOCK.search(t))
    whole = sum(1 for s in hit.ur for t in s.split() if foreign_script_chars(t) and not ARABIC_BLOCK.search(t))
    tot_tok = mixed + whole
    corpus_tok = max(1, sum(len(x.split()) for x in df.ur))
    md += ["", "## Shape of the contaminated tokens", "",
           f"Denominator is the {tot_tok:,} contaminated token occurrences, **not** the {n:,}-caption corpus.",
           "", "| shape | occurrences | % of contaminated tokens | % of corpus tokens |", "|---|---|---|---|",
           f"| Urdu word with an embedded foreign fragment | {mixed:,} | {mixed / max(1, tot_tok):.1%} | {mixed / corpus_tok:.3%} |",
           f"| token entirely in another script | {whole:,} | {whole / max(1, tot_tok):.1%} | {whole / corpus_tok:.3%} |"]

    forms = tokens(hit)
    tot = sum(forms.values()) or 1
    md += ["", "## Word-forms", "", f"{len(forms):,} distinct forms, {tot:,} occurrences.", "",
           "| # | form | code points | count | % of contaminated tokens | cumulative |",
           "|---|---|---|---|---|---|"]
    run = 0
    for i, (w, c) in enumerate(forms.most_common(args.top), 1):
        run += c
        md.append(f"| {i} | `{w}` | {codepoints(foreign_script_chars(w))} | {c:,} | {c / tot:.1%} | {run / tot:.1%} |")
    run = 0
    for pct in (0.80, 0.90, 0.95):
        run, k = 0, 0
        for k, (_, c) in enumerate(forms.most_common(), 1):
            run += c
            if run / tot >= pct:
                break
        md.append(f"\nTop {k} forms cover {pct:.0%} of occurrences.")

    md += ["", "## Trigger words", "",
           "Share of captions containing each English word whose translation is contaminated.", "",
           "| EN word | captions | contaminated | rate |", "|---|---|---|---|"]
    for w in args.trigger_words:
        m = df.caption_en.str.contains(rf"\b{re.escape(w)}", case=False, regex=True)
        tn, tc = int(m.sum()), int((m & (df.n_foreign > 0)).sum())
        if tn:
            md.append(f"| {w} | {tn:,} | {tc:,} | {tc / tn:.1%} |")

    md += ["", f"## Examples ({min(args.show, len(hit))} of {len(hit):,})", "",
           "Foreign-script characters are bracketed `⟦ ⟧`."]
    for r in hit.head(args.show).itertuples():
        md.append(f"\n- EN: {r.caption_en}\n  UR: {highlight(r.ur)}\n  chars: {r.codepoints} ({', '.join(r.scripts)})")

    after_path = Path(args.after) if args.after else (
        Path(args.translations).with_name(f"{name}_repaired.parquet") if args.translations else None)
    if after_path and after_path.exists() and after_path != Path(args.translations or ""):
        a = pd.read_parquet(after_path)
        acol = [c for c in a.columns if c.startswith("ur_")][0]
        if "caption_en" not in a.columns:
            a = a.merge(load_captions_v1()[["uid", "caption_en"]], on="uid")
        a = flag(a[["uid", "caption_en", acol]].rename(columns={acol: "ur"}))
        before_n, after_n = len(hit), int((a.n_foreign > 0).sum())
        md += ["", "---", ""]
        md += summary_block(a, len(a), f"# AFTER FIXING: {name}")
        md += ["", f"Source: `{after_path.relative_to(ROOT) if ROOT in after_path.parents else after_path}`"
                   f" — repaired with `repairs/script_contamination_{name}.tsv`"
                   f" via `scripts/15_apply_repairs.py`.", "",
               "| | captions | rate |", "|---|---|---|",
               f"| before | {before_n:,} | {before_n / n:.3%} |",
               f"| after | {after_n:,} | {after_n / len(a):.3%} |",
               f"| repaired | {before_n - after_n:,} | — |"]

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"script_contamination_{name}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    cols = ["uid", "caption_en", "ur", "n_foreign", "codepoints"]
    hit.assign(scripts=hit.scripts.map(", ".join), highlighted=hit.ur.map(highlight))[cols + ["scripts", "highlighted"]] \
        .to_parquet(RESULTS / f"script_contamination_{name}.parquet", index=False)
    # stdout: the headline tables, then the AFTER FIXING section if there is one -- the long
    # word-form, trigger and example tables stay in the file.
    cut = next((i for i, l in enumerate(md) if l.startswith("## Shape")), 40)
    tail = next((i for i, l in enumerate(md) if l.startswith("# AFTER FIXING")), None)
    print("\n".join(md[:cut]))
    if tail is not None:
        print("\n".join(md[tail:]))
    print(f"\n-> {out}\n-> {RESULTS / f'script_contamination_{name}.parquet'}")


if __name__ == "__main__":
    main()

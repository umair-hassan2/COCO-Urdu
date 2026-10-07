"""What did Table 2 (BLEU 0.31 -> 0.76 'after refinement') actually compare?

Recomputes chrF / BLEU on the flagged subset under four pairings:
  (a) v1 MT vs NLLB ref            — the paper's 'before'
  (b) refined MT vs refined ref    — the paper's 'after' (both LLM outputs from ONE prompt)
  (c) refined MT vs original ref   — the honest 'after'
  (d) refined ref vs original ref  — how much the *reference* was rewritten
Also checks the A/B swap in notebooks/legacy/targetted_refinements.ipynb.
"""
import sys
from pathlib import Path

import sacrebleu

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import RESULTS
from cocourdu.data import load_captions_v1, load_refined_v1


def corpus(hyp, ref):
    bleu = sacrebleu.corpus_bleu(hyp, [ref], tokenize="flores200").score
    chrf = sacrebleu.corpus_chrf(hyp, [ref], word_order=2).score
    return bleu, chrf


def main():
    v1 = load_captions_v1()
    rf = load_refined_v1()
    m = v1.merge(rf[["split", "row_idx", "ur_refined_mt", "ur_refined_ref"]], on=["split", "row_idx"], how="inner")
    low = m[m.final_score < 0.7].copy()
    changed_mt = (low.ur_refined_mt != low.ur_seamless).mean()
    changed_ref = (low.ur_refined_ref != low.ur_nllb_ref).mean()
    rows = [
        ("(a) v1 MT vs NLLB ref  [paper 'before']", *corpus(low.ur_seamless.tolist(), low.ur_nllb_ref.tolist())),
        ("(b) refined MT vs refined ref  [paper 'after']", *corpus(low.ur_refined_mt.tolist(), low.ur_refined_ref.tolist())),
        ("(c) refined MT vs ORIGINAL ref  [honest 'after']", *corpus(low.ur_refined_mt.tolist(), low.ur_nllb_ref.tolist())),
        ("(d) refined ref vs ORIGINAL ref  [ref drift]", *corpus(low.ur_refined_ref.tolist(), low.ur_nllb_ref.tolist())),
    ]
    md = ["# Table 2 forensics", "",
          f"Flagged subset (final_score < 0.7): **{len(low):,}** captions.",
          f"Refined MT differs from v1 MT in {changed_mt:.1%} of rows; refined *reference* differs from NLLB ref in {changed_ref:.1%} of rows.",
          "", "| Pairing | BLEU | chrF++ |", "|---|---|---|"]
    md += [f"| {n} | {b:.2f} | {c:.2f} |" for n, b, c in rows]
    md += ["", "Interpretation: if (b) >> (c), the reported gain came from scoring one LLM output against another from the same prompt.",
           "Code evidence (legacy notebook): prompt asks to improve A=Reference and B=MT; the code then sets `refined_mt = A` and `refined_ref = B` (swapped) and overwrites both columns before computing metrics."]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "table2_forensics.md").write_text("\n".join(md) + "\n")
    low[["split", "row_idx", "image_id", "caption_en", "ur_seamless", "ur_nllb_ref", "ur_refined_mt", "ur_refined_ref", "final_score"]].to_parquet(RESULTS / "table2_flagged_rows.parquet", index=False)
    print("\n".join(md))


if __name__ == "__main__":
    main()

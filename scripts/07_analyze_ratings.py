"""Human-study analysis -> results/human_study/*.md|csv

1. System comparison: adequacy/fluency means with item-level bootstrap CIs; pairwise win rates; error-type rates.
2. Agreement on the core: Krippendorff's alpha (interval), ICC(2,1).
3. QE meta-evaluation: correlation of each metric with mean adequacy; fitted weights vs v1's 0.4/0.4/0.2.
Input: ratings DB from the rating tool (sqlite) and data/study/qe_scores.parquet (optional).
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA, RESULTS
from cocourdu.stats import fit_weights, icc_2_1, item_level_bootstrap, krippendorff_alpha_interval, metric_correlations, pairwise_win_rates

ERRORS = ["mistranslation", "omission", "addition", "agreement", "spelling", "word_order", "untranslated"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(RESULTS / "ratings.sqlite"))
    ap.add_argument("--min-raters", type=int, default=2)
    args = ap.parse_args()
    out = RESULTS / "human_study"; out.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(args.db)
    r = pd.read_sql("SELECT * FROM ratings", con)
    r["errors"] = r.errors.fillna("").apply(lambda s: [e for e in s.split(",") if e])
    for e in ERRORS:
        r[f"err_{e}"] = r.errors.apply(lambda l: e in l)
    md = [f"# Human study results", "", f"{len(r):,} ratings · {r.item_id.nunique()} items · {r.rater.nunique()} raters · systems: {sorted(r.system.unique())}", ""]

    # 1. systems
    for v in ["adequacy", "fluency"]:
        t = item_level_bootstrap(r, v, "system"); t.to_csv(out / f"system_{v}.csv")
        md += [f"## {v.title()} by system (item-level bootstrap 95% CI)", "", t.round(2).to_markdown(), ""]
    w = pairwise_win_rates(r, "adequacy", "system"); w.to_csv(out / "pairwise_adequacy.csv", index=False)
    md += ["## Pairwise adequacy win rate (row beats column)", "", w.round(3).to_markdown(index=False), ""]
    err = r.groupby("system")[[f"err_{e}" for e in ERRORS]].mean().rename(columns=lambda c: c[4:]); err.to_csv(out / "error_rates.csv")
    md += ["## Error-type rate by system (share of ratings with the tag)", "", (err * 100).round(1).to_markdown(), ""]

    # 2. agreement on items with >= 3 raters
    core = r.groupby(["item_id", "system"]).rater.nunique()
    core_keys = core[core >= 3].index
    rc = r.set_index(["item_id", "system"]).loc[core_keys].reset_index()
    for v in ["adequacy", "fluency"]:
        mat = rc.pivot_table(index="rater", columns=["item_id", "system"], values=v)
        md += [f"- {v}: Krippendorff α (interval) = **{krippendorff_alpha_interval(mat.to_numpy()):.3f}**, ICC(2,1) = {icc_2_1(mat.to_numpy()):.3f} on {mat.shape[1]} (item, system) pairs"]
    md.append("")

    # 3. QE meta-eval
    qe_path = DATA / "study" / "qe_scores.parquet"
    if qe_path.exists():
        qe = pd.read_parquet(qe_path)
        human = r.groupby(["item_id", "system"]).agg(adequacy=("adequacy", "mean"), fluency=("fluency", "mean"), n=("rater", "nunique")).reset_index()
        human = human[human.n >= args.min_raters]
        m = human.merge(qe, on=["item_id", "system"])
        metric_cols = [c for c in qe.columns if c not in {"item_id", "uid", "image_id", "image_url", "system", "caption_en", "ur"}]
        corr = metric_correlations(m[metric_cols], m.adequacy); corr.to_csv(out / "metric_correlations.csv", index=False)
        md += ["## QE metrics vs mean human adequacy", "", corr.round(3).to_markdown(index=False), ""]
        base = [c for c in ["comet_kiwi", "siglip2_rel", "metricx24_qe", "xcomet_qe"] if c in m]
        if len(base) >= 2:
            fw = fit_weights(m[base], m.adequacy)
            md += [f"Fitted NNLS weights on half the items: {fw['weights']} → held-out Spearman {fw['test_spearman']:.3f} (n_test={fw['n_test']})", ""]
    else:
        md += ["_No qe_scores.parquet yet — run scripts/06_score_qe.py for the QE meta-evaluation._", ""]
    (out / "README.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

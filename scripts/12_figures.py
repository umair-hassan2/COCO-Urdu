"""Paper figures from results/ -> results/figures/*.pdf|png. Run after 07 (and 08 for the retrieval plot).

F1 system_scores      adequacy/fluency per system with 95% CI (the headline)
F2 error_types        error-tag rates per system (grouped bars)
F3 metric_corr        Spearman of each QE metric with human adequacy (sorted bars)
F4 qe_vs_human        scatter: v1 hybrid score vs mean human adequacy, colored by system (shows what 0.7 threshold missed)
F5 retrieval          R@1/5/10 per training condition
"""
import json
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cocourdu import DATA, RESULTS

HS, FIG = RESULTS / "human_study", RESULTS / "figures"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig); print("saved", name)


def f1_system_scores():
    fig, axes = plt.subplots(1, 2, figsize=(6, 2.4), sharey=True)
    for ax, v in zip(axes, ["adequacy", "fluency"]):
        t = pd.read_csv(HS / f"system_{v}.csv", index_col=0)
        ax.bar(t.index, t["mean"], yerr=[t["mean"] - t.ci_lo, t.ci_hi - t["mean"]], capsize=3, color="#4C72B0")
        ax.set_title(v.title()); ax.set_ylim(0, 100)
    axes[0].set_ylabel("mean rating (0–100), 95% item-bootstrap CI")
    save(fig, "F1_system_scores")


def f2_error_types():
    err = pd.read_csv(HS / "error_rates.csv", index_col=0) * 100
    fig, ax = plt.subplots(figsize=(6, 2.6))
    err.T.plot.bar(ax=ax, width=0.8)
    ax.set_ylabel("% of ratings with tag"); ax.set_xlabel(""); ax.legend(title="system", frameon=False)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    save(fig, "F2_error_types")


def f3_metric_corr():
    c = pd.read_csv(HS / "metric_correlations.csv").sort_values("spearman")
    fig, ax = plt.subplots(figsize=(4.5, 0.35 * len(c) + 0.8))
    ax.barh(c.metric, c.spearman, color="#55A868"); ax.axvline(0, color="k", lw=0.5)
    ax.set_xlabel("Spearman ρ with mean human adequacy")
    save(fig, "F3_metric_corr")


def f4_qe_vs_human(db=RESULTS / "ratings.sqlite"):
    r = pd.read_sql("SELECT item_id, system, adequacy FROM ratings", sqlite3.connect(db)).groupby(["item_id", "system"]).adequacy.mean().reset_index()
    items = pd.DataFrame([json.loads(l) for l in (DATA / "study" / "items.jsonl").open(encoding="utf-8")])
    m = r.merge(items[["item_id", "v1_final_score"]], on="item_id")
    m = m[m.system == "seamless"]  # v1 score only describes the Seamless output
    fig, ax = plt.subplots(figsize=(3.6, 3))
    ax.scatter(m.v1_final_score, m.adequacy, s=8, alpha=0.4, color="#C44E52")
    ax.axvline(0.7, ls="--", lw=0.8, color="k"); ax.text(0.705, 5, "v1 flag threshold", fontsize=7)
    ax.set_xlabel("v1 hybrid QE score"); ax.set_ylabel("mean human adequacy")
    save(fig, "F4_qe_vs_human")


def f5_retrieval():
    rows = [json.load(open(p)) for p in (RESULTS / "retrieval").glob("*.json")]
    if not rows:
        return print("no retrieval results yet")
    df = pd.DataFrame(rows).groupby("condition")[["t2i_R@1", "t2i_R@5", "t2i_R@10"]].mean() * 100
    fig, ax = plt.subplots(figsize=(5, 2.6))
    df.plot.bar(ax=ax, width=0.8); ax.set_ylabel("Urdu text→image recall (%)"); ax.set_xlabel("")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right"); ax.legend(frameon=False)
    save(fig, "F5_retrieval")


if __name__ == "__main__":
    for f in (f1_system_scores, f2_error_types, f3_metric_corr, f4_qe_vs_human, f5_retrieval):
        try:
            f()
        except FileNotFoundError as e:
            print(f"skip {f.__name__}: missing {e.filename}")

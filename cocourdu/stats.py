"""Statistics for the human study: bootstrap CIs, pairwise wins, Krippendorff's alpha, correlations."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def bootstrap_mean_ci(values: np.ndarray, n_boot: int = 2000, ci: float = 0.95, seed: int = 0) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    values = np.asarray(values, dtype=float)
    boots = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    lo, hi = np.quantile(boots, [(1 - ci) / 2, 1 - (1 - ci) / 2])
    return float(values.mean()), float(lo), float(hi)


def item_level_bootstrap(df: pd.DataFrame, value: str, group: str, item: str = "item_id",
                         n_boot: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Resample ITEMS (not ratings) so the CI respects the clustered design."""
    rng = np.random.default_rng(seed)
    per_item = df.groupby([item, group])[value].mean().unstack(group)
    items = per_item.index.to_numpy()
    out = {}
    boots = np.empty((n_boot, per_item.shape[1]))
    for b in range(n_boot):
        idx = rng.choice(len(items), size=len(items), replace=True)
        boots[b] = per_item.iloc[idx].mean(axis=0).to_numpy()
    for j, g in enumerate(per_item.columns):
        out[g] = {"mean": per_item[g].mean(), "ci_lo": np.quantile(boots[:, j], 0.025), "ci_hi": np.quantile(boots[:, j], 0.975), "n_items": per_item[g].notna().sum()}
    return pd.DataFrame(out).T


def pairwise_win_rates(df: pd.DataFrame, value: str, group: str, item: str = "item_id") -> pd.DataFrame:
    """For each ordered pair (a, b): share of items where mean(a) > mean(b), ties split 0.5."""
    per_item = df.groupby([item, group])[value].mean().unstack(group)
    systems = list(per_item.columns)
    rows = []
    for a in systems:
        for b in systems:
            if a == b:
                continue
            both = per_item[[a, b]].dropna()
            wins = (both[a] > both[b]).mean() + 0.5 * (both[a] == both[b]).mean()
            # sign test p-value on non-ties
            nt = both[both[a] != both[b]]
            p = stats.binomtest((nt[a] > nt[b]).sum(), len(nt), 0.5).pvalue if len(nt) else np.nan
            rows.append({"a": a, "b": b, "win_rate_a": wins, "n": len(both), "sign_test_p": p})
    return pd.DataFrame(rows)


def krippendorff_alpha_interval(matrix: np.ndarray) -> float:
    """Krippendorff's alpha, interval metric. matrix: raters x items, NaN for missing."""
    m = np.asarray(matrix, dtype=float)
    # pairable values: items with >= 2 ratings
    valid_items = np.sum(~np.isnan(m), axis=0) >= 2
    m = m[:, valid_items]
    if m.size == 0:
        return float("nan")
    n_total = np.sum(~np.isnan(m))
    # observed disagreement
    Do = 0.0
    for j in range(m.shape[1]):
        col = m[:, j][~np.isnan(m[:, j])]
        mj = len(col)
        if mj < 2:
            continue
        diffs = (col[:, None] - col[None, :]) ** 2
        Do += diffs.sum() / (mj - 1)
    Do /= n_total
    # expected disagreement
    allv = m[~np.isnan(m)]
    De = ((allv[:, None] - allv[None, :]) ** 2).sum() / (n_total * (n_total - 1))
    return float(1 - Do / De) if De > 0 else float("nan")


def icc_2_1(matrix: np.ndarray) -> float:
    """ICC(2,1) two-way random, single rating; requires complete raters x items matrix."""
    m = np.asarray(matrix, dtype=float)
    m = m[:, ~np.isnan(m).any(axis=0)]
    k, n = m.shape
    if n < 2 or k < 2:
        return float("nan")
    grand = m.mean()
    ms_rows = k * ((m.mean(axis=0) - grand) ** 2).sum() / (n - 1)
    ms_cols = n * ((m.mean(axis=1) - grand) ** 2).sum() / (k - 1)
    resid = m - m.mean(axis=0, keepdims=True) - m.mean(axis=1, keepdims=True) + grand
    ms_err = (resid ** 2).sum() / ((n - 1) * (k - 1))
    return float((ms_rows - ms_err) / (ms_rows + (k - 1) * ms_err + k * (ms_cols - ms_err) / n))


def metric_correlations(scores: pd.DataFrame, human: pd.Series) -> pd.DataFrame:
    """scores: DataFrame indexed like human, one column per metric. Returns Pearson/Spearman/Kendall per metric."""
    rows = []
    for col in scores.columns:
        s = scores[col]
        ok = s.notna() & human.notna()
        if ok.sum() < 10:
            continue
        rows.append({
            "metric": col, "n": int(ok.sum()),
            "pearson": stats.pearsonr(s[ok], human[ok])[0],
            "spearman": stats.spearmanr(s[ok], human[ok])[0],
            "kendall": stats.kendalltau(s[ok], human[ok])[0],
        })
    return pd.DataFrame(rows).sort_values("spearman", ascending=False)


def fit_weights(scores: pd.DataFrame, human: pd.Series, seed: int = 0) -> dict:
    """Non-negative least squares weights on a random half; Spearman on the other half."""
    from scipy.optimize import nnls
    ok = scores.notna().all(axis=1) & human.notna()
    X, y = scores[ok].to_numpy(), human[ok].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    tr, te = idx[: len(y) // 2], idx[len(y) // 2:]
    w, _ = nnls(X[tr], y[tr])
    w = w / w.sum() if w.sum() > 0 else w
    pred = X[te] @ w
    return {"weights": dict(zip(scores.columns, w.round(3))), "test_spearman": float(stats.spearmanr(pred, y[te])[0]), "n_train": len(tr), "n_test": len(te)}

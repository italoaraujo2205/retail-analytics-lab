"""Predeclared primary outcome: contribution per randomized customer (ITT)."""
import numpy as np
import pandas as pd
from scipy import stats

from .quality import DataQualityError


def analyze(frame: pd.DataFrame, seed: int = 44, bootstrap_samples: int = 1000) -> dict:
    required = {"customer_id", "variant", "converted", "contribution", "net_revenue", "cogs", "fulfillment_cost"}
    if not required.issubset(frame.columns) or frame[list(required)].isna().any().any():
        raise DataQualityError("Missing experiment columns or values")
    if frame.customer_id.duplicated().any():
        raise DataQualityError("Experiment requires one row per randomized customer")
    if not frame.variant.isin(["control", "discount"]).all() or not frame.converted.isin([0, 1]).all():
        raise DataQualityError("Invalid experiment group or conversion flag")
    for col in ["contribution", "net_revenue", "cogs", "fulfillment_cost"]:
        if not np.isfinite(frame[col].to_numpy(dtype=float)).all():
            raise DataQualityError(f"Non-finite experiment outcome: {col}")
    if not np.allclose(frame.contribution, frame.net_revenue - frame.cogs - frame.fulfillment_cost, atol=.011, rtol=0):
        raise DataQualityError("Experiment contribution reconciliation failed")
    if (frame.loc[frame.converted == 0, ["net_revenue", "cogs", "fulfillment_cost", "contribution"]] != 0).any().any():
        raise DataQualityError("Non-converter with purchase outcome")
    groups = {name: frame.loc[frame.variant == name] for name in ["control", "discount"]}
    counts = [len(groups[name]) for name in ["control", "discount"]]
    if min(counts) < 30:
        raise DataQualityError("Insufficient experimental units")
    srm_p = float(stats.chisquare(counts, f_exp=[sum(counts) / 2] * 2).pvalue)
    if srm_p < .001:
        raise DataQualityError("Sample ratio mismatch: investigate assignment before inference")
    a = groups["control"].contribution.to_numpy(float)
    b = groups["discount"].contribution.to_numpy(float)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = np.sqrt(va + vb)
    if se <= 0:
        raise DataQualityError("Primary outcome has zero sampling variance")
    dof = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    difference = float(b.mean() - a.mean())
    critical = float(stats.t.ppf(.975, dof))
    ci = [difference - critical * se, difference + critical * se]
    rng = np.random.default_rng(seed)
    if bootstrap_samples < 100:
        raise ValueError("Use at least 100 bootstrap resamples")
    bootstrap = np.empty(bootstrap_samples)
    for i in range(bootstrap_samples):
        bootstrap[i] = rng.choice(b, len(b), replace=True).mean() - rng.choice(a, len(a), replace=True).mean()
    result = {
        "primary_metric": "contribution_per_randomized_customer", "currency": "BRL",
        "unit": "randomized_customer", "alpha": .05, "srm_p_value": srm_p,
        "groups": {name: {"n": len(data), "conversion": float(data.converted.mean()), "mean_contribution": float(data.contribution.mean())} for name, data in groups.items()},
        "difference": difference, "ci_95": [float(x) for x in ci],
        "welch_p_value": float(stats.ttest_ind(b, a, equal_var=False).pvalue),
        "bootstrap_ci_95": np.quantile(bootstrap, [.025, .975]).tolist(),
        "bootstrap_samples": bootstrap_samples,
        "conversion_difference_pp": float((groups["discount"].converted.mean() - groups["control"].converted.mean()) * 100),
        "decision": "Nao expandir o desconto" if ci[1] < 0 else ("Avaliar expansao com guardrails" if ci[0] > 0 else "Resultado inconclusivo"),
        "scope": "Synthetic fixed-horizon demonstration; not evidence about a real retailer.",
    }
    return result

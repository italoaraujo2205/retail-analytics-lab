"""Behavioral analyses with explicit observation windows."""
import numpy as np
import pandas as pd


def cohorts(orders: pd.DataFrame, observed_through: str = "2025-12-31", horizon: int = 3) -> pd.DataFrame:
    cutoff = pd.Timestamp(observed_through)
    data = orders.loc[(orders.status == "delivered") & (pd.to_datetime(orders.order_date) <= cutoff), ["customer_id", "order_date"]].copy()
    columns = ["cohort", "cohort_size", "age_month", "retention"]
    if data.empty:
        return pd.DataFrame(columns=columns)
    data["month"] = pd.to_datetime(data.order_date).dt.to_period("M")
    data["cohort"] = data.groupby("customer_id").month.transform("min")
    sizes = data.groupby("cohort").customer_id.nunique()
    data["age_month"] = data.month.astype("int64") - data.cohort.astype("int64")
    active = data.groupby(["cohort", "age_month"]).customer_id.nunique()
    # A partially observed month is not treated as a complete retention window.
    last_complete = cutoff.to_period("M") if cutoff.normalize() == (cutoff + pd.offsets.MonthEnd(0)).normalize() else cutoff.to_period("M") - 1
    rows = []
    for cohort, size in sizes.items():
        for age in range(horizon + 1):
            mature = cohort + age <= last_complete
            retained = active.get((cohort, age), 0) / size if mature else np.nan
            rows.append((str(cohort), int(size), age, retained))
    return pd.DataFrame(rows, columns=columns)


def rfm(orders: pd.DataFrame, snapshot: str = "2026-01-01") -> pd.DataFrame:
    cutoff = pd.Timestamp(snapshot)
    data = orders.loc[(orders.status == "delivered") & (pd.to_datetime(orders.order_date) < cutoff)].copy()
    data["order_date"] = pd.to_datetime(data.order_date)
    result = data.groupby("customer_id").agg(last_purchase=("order_date", "max"), frequency=("order_id", "nunique"), monetary_cents=("net_revenue_cents", "sum"))
    result["recency_days"] = (cutoff - result.last_purchase).dt.days
    result["monetary"] = result.monetary_cents / 100
    # Explicit heuristic segments: no predictive/churn claim.
    result["segment"] = np.select(
        [(result.recency_days <= 60) & (result.frequency >= 4), result.recency_days > 120],
        ["Recentes frequentes", "Sem compra ha mais de 120 dias"], default="Demais clientes")
    return result.reset_index()[["customer_id", "recency_days", "frequency", "monetary", "segment"]]

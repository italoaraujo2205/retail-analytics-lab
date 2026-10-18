"""Fixed-calendar synthetic fixtures; no network, personal data or credentials."""
from pathlib import Path

import numpy as np
import pandas as pd


def generate(root: Path, seed: int = 42, n_orders: int = 24000) -> dict[str, pd.DataFrame]:
    if n_orders < 1:
        raise ValueError("n_orders must be positive")
    rng = np.random.default_rng(seed)
    n_customers = 6000
    customers = pd.DataFrame({
        "customer_id": np.arange(1, n_customers + 1),
        "region": rng.choice(["Nordeste", "Sudeste", "Sul", "Norte", "Centro-Oeste"], n_customers),
    })
    products = pd.DataFrame({
        "product_id": np.arange(1, 25),
        "category": np.repeat(["Casa", "Esporte", "Moda", "Tecnologia"], 6),
        "unit_price": np.round(rng.uniform(35, 350, 24), 2),
    })
    products["unit_cost"] = (products.unit_price * rng.uniform(.48, .77, 24)).round(2)
    # Month weighting encodes seasonality in the simulation, not an empirical finding.
    dates = pd.date_range("2025-01-01", "2025-12-31")
    weights = np.where(dates.month == 11, 1.9, np.where(dates.month == 12, 1.4, 1.0))
    sampled = rng.choice(dates.to_numpy(), n_orders, p=weights / weights.sum())
    status = rng.choice(["delivered", "returned", "cancelled"], n_orders, p=[.92, .05, .03])
    orders = pd.DataFrame({
        "order_id": np.arange(1, n_orders + 1),
        "customer_id": rng.integers(1, n_customers + 1, n_orders),
        "order_date": pd.to_datetime(sampled).strftime("%Y-%m-%d"),
        "status": status,
        "fulfillment_cost": np.where(status == "cancelled", 0, np.round(rng.uniform(7, 15, n_orders), 2)),
    })
    rows = []
    for order in orders.itertuples(index=False):
        for product_id in rng.choice(products.product_id, int(rng.integers(1, 4)), replace=False):
            product = products.iloc[int(product_id) - 1]
            discount = .18 if order.order_date[5:7] == "11" else float(rng.choice([0, .05, .1], p=[.6, .3, .1]))
            rows.append((len(rows) + 1, order.order_id, int(product_id), int(rng.integers(1, 4)),
                         float(product.unit_price), float(product.unit_cost), discount))
    items = pd.DataFrame(rows, columns=["item_id", "order_id", "product_id", "quantity", "unit_price", "unit_cost", "discount_rate"])
    # Repeated identical source records demonstrate deduplication; conflicting keys fail.
    orders = pd.concat([orders, orders.iloc[:20]], ignore_index=True)
    frames = {"customers": customers, "products": products, "orders": orders, "order_items": items}
    directory = root / "data" / "raw"
    directory.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(directory / f"{name}.csv", index=False)
    return frames


def generate_experiment(root: Path, seed: int = 43, n: int = 16000) -> pd.DataFrame:
    """One row per randomized customer, including zero-outcome non-buyers.

    This experiment is independent of the observational orders dataset.
    The treatment changes both conversion probability and discount cost by design.
    """
    rng = np.random.default_rng(seed)
    group = rng.choice(["control", "discount"], n)
    converted = (rng.random(n) < np.where(group == "discount", .27, .21)).astype(int)
    gross = np.round(rng.lognormal(np.log(220), .4, n), 2) * converted
    discount = np.where(group == "discount", .15, 0) * gross
    net = np.round(gross - discount, 2)
    cogs = np.round(.68 * gross, 2)
    fulfillment = 10 * converted
    frame = pd.DataFrame({
        "customer_id": np.arange(1, n + 1), "variant": group, "converted": converted,
        "gross_revenue": gross, "discount_amount": np.round(discount, 2),
        "net_revenue": net, "cogs": cogs, "fulfillment_cost": fulfillment,
        "contribution": np.round(net - cogs - fulfillment, 2),
    })
    path = root / "data" / "raw"
    path.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path / "experiment.csv", index=False)
    return frame

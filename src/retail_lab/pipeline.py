import hashlib
import logging
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from . import __version__
from .analysis import cohorts, rfm
from .experiment import analyze
from .generate import generate, generate_experiment
from .quality import prepare
from .report import write_reports
from .warehouse import build, query

LOG = logging.getLogger(__name__)


def run(root: Path, seed: int = 42, n_orders: int = 24000) -> dict:
    root = Path(root).resolve()
    if not (root / "sql" / "warehouse.sql").is_file():
        raise FileNotFoundError("Run from the repository root, or pass --root with the project path")
    LOG.info("Generating explicitly synthetic data; seed=%s", seed)
    generate(root, seed=seed, n_orders=n_orders)
    generate_experiment(root, seed=seed + 1)
    raw = root / "data" / "raw"
    frames = {name: pd.read_csv(raw / f"{name}.csv") for name in ["customers", "products", "orders", "order_items"]}
    clean, audit = prepare(frames)
    experiment = analyze(pd.read_csv(raw / "experiment.csv"), seed=seed + 2)
    LOG.info("Quality checks passed; removed %s identical order duplicates", audit["orders"]["exact_duplicates_removed"])
    database = build(root, clean)
    orders = query(database, "SELECT * FROM fct_order")
    monthly = query(database, "SELECT * FROM mart_monthly ORDER BY month")
    category = query(database, "SELECT * FROM mart_category ORDER BY category")
    cohort = cohorts(orders)
    segments = rfm(orders)
    manifest = {
        "project_version": __version__, "synthetic": True, "seed": seed,
        "historical_start": "2025-01-01", "historical_end": "2025-12-31",
        "rfm_snapshot": "2026-01-01", "experiment_window_days": 14,
        "order_count": len(orders), "load_strategy": "atomic_full_snapshot_rebuild",
        "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(raw.glob("*.csv"))},
    }
    write_reports(root, monthly, category, cohort, segments, experiment, audit, manifest)
    LOG.info("Report ready: %s", root / "reports" / "report.html")
    return experiment

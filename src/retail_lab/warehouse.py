"""Atomic, repeatable snapshot rebuild using SQLite and integer-cent facts."""
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


def build(root: Path, frames: dict[str, pd.DataFrame]) -> Path:
    target = root / "data" / "warehouse.sqlite"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".building.sqlite")
    temporary.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(temporary)) as conn:
            with conn:
                for name, frame in frames.items():
                    frame.to_sql(f"stg_{name}", conn, index=False, if_exists="replace")
                conn.executescript((root / "sql" / "warehouse.sql").read_text(encoding="utf-8"))
                # Staging is retained for lineage/reconciliation in this educational project.
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return target


def query(database: Path, sql: str) -> pd.DataFrame:
    with closing(sqlite3.connect(database)) as conn:
        return pd.read_sql_query(sql, conn)

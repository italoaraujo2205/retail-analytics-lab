import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np

from retail_lab.generate import generate
from retail_lab.quality import DataQualityError, prepare
from retail_lab.warehouse import build, query


class QualityWarehouseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "sql").mkdir()
        shutil.copy(Path(__file__).resolve().parents[1] / "sql" / "warehouse.sql", self.root / "sql" / "warehouse.sql")
        self.frames = generate(self.root, seed=7, n_orders=60)

    def test_exact_duplicates_are_deduplicated(self):
        clean, audit = prepare(self.frames)
        self.assertEqual(len(clean["orders"]), 60)
        self.assertEqual(audit["orders"]["exact_duplicates_removed"], 20)

    def test_conflicting_duplicate_fails(self):
        self.frames["orders"].loc[60, "customer_id"] = 999999
        with self.assertRaisesRegex(DataQualityError, "Conflicting"):
            prepare(self.frames)

    def test_broken_relationship_fails(self):
        self.frames["order_items"].loc[0, "product_id"] = 999999
        with self.assertRaisesRegex(DataQualityError, "relationship"):
            prepare(self.frames)

    def test_negative_quantity_and_nonfinite_amount_fail(self):
        self.frames["order_items"].loc[0, "quantity"] = -1
        with self.assertRaises(DataQualityError):
            prepare(self.frames)
        self.frames["order_items"].loc[0, "quantity"] = 1
        self.frames["order_items"].loc[0, "unit_price"] = np.inf
        with self.assertRaises(DataQualityError):
            prepare(self.frames)

    def test_fulfillment_not_duplicated_by_item_join(self):
        clean, _ = prepare(self.frames)
        database = build(self.root, clean)
        orders = query(database, "SELECT * FROM fct_order")
        expected = round(clean["orders"].fulfillment_cost.sum() * 100)
        self.assertEqual(int(orders.fulfillment_cents.sum()), expected)
        self.assertTrue((orders.contribution_cents == orders.net_revenue_cents - orders.cogs_cents - orders.fulfillment_cents).all())
        self.assertEqual(orders.net_revenue_cents.sum(), query(database, "SELECT SUM(net_revenue_cents) AS total FROM fct_order_item").total.iloc[0])

    def test_second_load_does_not_duplicate_orders(self):
        clean, _ = prepare(self.frames)
        first = build(self.root, clean)
        a = query(first, "SELECT * FROM fct_order ORDER BY order_id")
        second = build(self.root, clean)
        b = query(second, "SELECT * FROM fct_order ORDER BY order_id")
        self.assertTrue(a.equals(b))

    def test_failed_rebuild_preserves_previous_database(self):
        clean, _ = prepare(self.frames)
        path = build(self.root, clean)
        before = path.read_bytes()
        (self.root / "sql" / "warehouse.sql").write_text("INVALID SQL;")
        with self.assertRaises(sqlite3.Error):
            build(self.root, clean)
        self.assertEqual(before, path.read_bytes())

    def test_returned_and_cancelled_orders_have_no_sales(self):
        clean, _ = prepare(self.frames)
        path = build(self.root, clean)
        invalid = query(path, "SELECT * FROM fct_order WHERE status != 'delivered' AND (net_revenue_cents != 0 OR cogs_cents != 0)")
        self.assertTrue(invalid.empty)


if __name__ == "__main__":
    unittest.main()

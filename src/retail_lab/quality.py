"""Fail closed on invalid dimensions, measures or referential integrity."""
import numpy as np
import pandas as pd


class DataQualityError(ValueError):
    pass


def prepare(frames: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict]:
    keys = {"customers": "customer_id", "products": "product_id", "orders": "order_id", "order_items": "item_id"}
    required = {
        "customers": {"customer_id", "region"},
        "products": {"product_id", "category", "unit_price", "unit_cost"},
        "orders": {"order_id", "customer_id", "order_date", "status", "fulfillment_cost"},
        "order_items": {"item_id", "order_id", "product_id", "quantity", "unit_price", "unit_cost", "discount_rate"},
    }
    clean, audit = {}, {}
    for name, key in keys.items():
        if name not in frames or not required[name].issubset(frames[name].columns):
            raise DataQualityError(f"Missing required table/columns: {name}")
        frame = frames[name].copy()
        if frame[list(required[name])].isna().any().any():
            raise DataQualityError(f"Null in required column: {name}")
        dedup = frame.drop_duplicates()
        if dedup[key].duplicated().any():
            raise DataQualityError(f"Conflicting duplicate key: {name}.{key}")
        audit[name] = {"input_rows": len(frame), "accepted_rows": len(dedup), "exact_duplicates_removed": len(frame) - len(dedup)}
        clean[name] = dedup
    for table, columns in {"products": ["product_id", "unit_price", "unit_cost"],
                            "orders": ["order_id", "customer_id", "fulfillment_cost"],
                            "customers": ["customer_id"],
                            "order_items": ["item_id", "order_id", "product_id", "quantity", "unit_price", "unit_cost", "discount_rate"]}.items():
        for column in columns:
            values = pd.to_numeric(clean[table][column], errors="coerce")
            if not np.isfinite(values.to_numpy(dtype=float)).all() or (values < 0).any():
                raise DataQualityError(f"Invalid number: {table}.{column}")
            if column.endswith("_id") or column == "quantity":
                if (values <= 0).any() or (values % 1 != 0).any():
                    raise DataQualityError(f"Expected positive integer: {table}.{column}")
            clean[table][column] = values
    items, orders = clean["order_items"], clean["orders"]
    if not items.discount_rate.between(0, 1).all():
        raise DataQualityError("discount_rate outside [0, 1]")
    if not orders.status.isin(["delivered", "returned", "cancelled"]).all():
        raise DataQualityError("Unknown order status")
    parsed = pd.to_datetime(orders.order_date, format="%Y-%m-%d", errors="coerce")
    if parsed.isna().any():
        raise DataQualityError("Invalid order_date")
    orders["order_date"] = parsed.dt.strftime("%Y-%m-%d")
    for child, child_key, parent, parent_key in [
        ("orders", "customer_id", "customers", "customer_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
    ]:
        if not clean[child][child_key].isin(clean[parent][parent_key]).all():
            raise DataQualityError(f"Broken relationship: {child}.{child_key}")
    if not orders.order_id.isin(items.order_id).all():
        raise DataQualityError("Order without items")
    if (orders.loc[orders.status == "cancelled", "fulfillment_cost"] != 0).any():
        raise DataQualityError("Cancelled order with fulfillment cost")
    return clean, audit

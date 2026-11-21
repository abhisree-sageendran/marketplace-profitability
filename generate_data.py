from pathlib import Path
from random import Random
from datetime import date, timedelta

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

rng = Random(42)

products = pd.DataFrame(
    [
        ("P01", "Wireless Headphones", "Electronics", 2400, 1450),
        ("P02", "Bluetooth Speaker", "Electronics", 1800, 1100),
        ("P03", "Cotton Shirt", "Fashion", 1200, 450),
        ("P04", "Running Shoes", "Fashion", 2600, 1250),
        ("P05", "Desk Lamp", "Home", 1500, 750),
        ("P06", "Storage Organizer", "Home", 900, 380),
        ("P07", "Yoga Mat", "Fitness", 1100, 460),
        ("P08", "Resistance Bands", "Fitness", 700, 240),
    ],
    columns=[
        "product_id",
        "product_name",
        "category",
        "unit_price",
        "unit_cost",
    ],
)

sellers = pd.DataFrame(
    [
        ("S01", "Northstar Retail"),
        ("S02", "Urban Basket"),
        ("S03", "Everyday Goods"),
        ("S04", "Value Avenue"),
    ],
    columns=["seller_id", "seller_name"],
)

product_lookup = products.set_index("product_id").to_dict("index")
product_ids = products["product_id"].tolist()
seller_ids = sellers["seller_id"].tolist()

orders = []
returns = []

for number in range(1, 4001):
    order_id = f"O{number:05d}"
    product_id = rng.choice(product_ids)
    seller_id = rng.choice(seller_ids)
    product = product_lookup[product_id]

    order_date = date(2025, 1, 1) + timedelta(
        days=rng.randrange(365)
    )
    quantity = rng.randint(1, 3)
    discount_rate = rng.choice([0, 0.05, 0.10, 0.15, 0.20])

    gross_sales = quantity * product["unit_price"]
    discount = round(gross_sales * discount_rate, 2)
    paid_amount = round(gross_sales - discount, 2)

    shipping_cost = rng.randint(50, 140)
    fee_rate = 0.12

    orders.append(
        {
            "order_id": order_id,
            "order_date": order_date,
            "product_id": product_id,
            "seller_id": seller_id,
            "quantity": quantity,
            "unit_price": product["unit_price"],
            "unit_cost": product["unit_cost"],
            "gross_sales": gross_sales,
            "discount": discount,
            "paid_amount": paid_amount,
            "shipping_cost": shipping_cost,
            "fee_rate": fee_rate,
        }
    )

    return_probability = {
        "Electronics": 0.12,
        "Fashion": 0.27,
        "Home": 0.10,
        "Fitness": 0.08,
    }[product["category"]]

    if seller_id == "S04":
        return_probability += 0.08

    if rng.random() < return_probability:
        returned_quantity = rng.randint(1, quantity)

        # Some multi-unit returns arrive as separate return events.
        portions = [returned_quantity]
        if returned_quantity > 1 and rng.random() < 0.35:
            portions = [1, returned_quantity - 1]

        remaining_refund = round(
            paid_amount * returned_quantity / quantity, 2
        )

        for index, portion in enumerate(portions):
            refund = remaining_refund

            if index < len(portions) - 1:
                refund = round(
                    paid_amount * portion / quantity, 2
                )

            remaining_refund = round(
                remaining_refund - refund, 2
            )

            reason = rng.choice(
                [
                    "Damaged",
                    "Wrong item",
                    "Not as described",
                    "Changed mind",
                    "Size or fit",
                ]
            )

            restockable = reason != "Damaged"

            returns.append(
                {
                    "return_id": f"R{len(returns) + 1:05d}",
                    "order_id": order_id,
                    "return_date": order_date
                    + timedelta(days=rng.randint(3, 30)),
                    "returned_quantity": portion,
                    "refund_amount": refund,
                    "return_shipping_cost": rng.randint(40, 100),
                    "recovered_inventory_cost": (
                        portion * product["unit_cost"]
                        if restockable
                        else 0
                    ),
                    "reason": reason,
                }
            )

orders = pd.DataFrame(orders)
returns = pd.DataFrame(returns)

assert orders["order_id"].is_unique
assert products["product_id"].is_unique
assert sellers["seller_id"].is_unique
assert returns["return_id"].is_unique

assert orders["product_id"].isin(products["product_id"]).all()
assert orders["seller_id"].isin(sellers["seller_id"]).all()
assert returns["order_id"].isin(orders["order_id"]).all()

return_totals = returns.groupby("order_id").agg(
    returned_quantity=("returned_quantity", "sum"),
    refund_amount=("refund_amount", "sum"),
    recovered_inventory_cost=("recovered_inventory_cost", "sum"),
)

checks = orders.set_index("order_id").join(
    return_totals, rsuffix="_returned"
).fillna(0)

assert (
    checks["returned_quantity"] <= checks["quantity"]
).all()

assert (
    checks["refund_amount"] <= checks["paid_amount"] + 0.01
).all()

assert (
    checks["recovered_inventory_cost"]
    <= checks["returned_quantity"] * checks["unit_cost"]
).all()

return_dates = returns.merge(
    orders[["order_id", "order_date"]],
    on="order_id",
    validate="many_to_one",
)

assert (
    return_dates["return_date"] >= return_dates["order_date"]
).all()

for name, frame in [
    ("products", products),
    ("sellers", sellers),
    ("orders", orders),
    ("returns", returns),
]:
    frame.to_csv(DATA / f"{name}.csv", index=False)

print(f"Created {len(orders):,} orders.")
print(f"Created {len(returns):,} return events.")
print("All data validation checks passed.")
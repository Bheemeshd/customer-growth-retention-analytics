"""Generate a seeded synthetic customer and order history for growth analytics."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


OBSERVATION_END = pd.Timestamp("2025-06-30")
OUTCOME_END = pd.Timestamp("2025-12-31")


def _random_dates(rng: np.random.Generator, start: pd.Timestamp, end: pd.Timestamp, count: int, recency_bias: float) -> list[pd.Timestamp]:
    days = max((end - start).days, 1)
    # Larger bias concentrates activity near the observation-window end.
    positions = rng.beta(recency_bias, 1.35, count)
    return [start + pd.Timedelta(days=int(p * days)) for p in positions]


def generate(seed: int = 77, n_customers: int = 8_000) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    channels = np.array(["organic", "paid_search", "paid_social", "affiliate", "referral"])
    channel = rng.choice(channels, n_customers, p=[0.27, 0.24, 0.20, 0.12, 0.17])
    signup_days = rng.integers(0, (pd.Timestamp("2025-02-28") - pd.Timestamp("2023-01-01")).days, n_customers)
    signup_date = pd.Timestamp("2023-01-01") + pd.to_timedelta(signup_days, unit="D")
    latent = rng.choice(["core", "growing", "occasional", "fragile"], n_customers, p=[0.18, 0.29, 0.34, 0.19])
    cac_base = {"organic": 8, "paid_search": 42, "paid_social": 35, "affiliate": 28, "referral": 14}
    acquisition_cost = np.array([max(2, rng.normal(cac_base[c], 5)) for c in channel])
    customers = pd.DataFrame(
        {
            "customer_id": [f"C{i:06d}" for i in range(1, n_customers + 1)],
            "signup_date": pd.to_datetime(signup_date).strftime("%Y-%m-%d"),
            "acquisition_channel": channel,
            "region": rng.choice(["north", "south", "east", "west"], n_customers),
            "email_opt_in": rng.binomial(1, 0.73, n_customers),
            "acquisition_cost": np.round(acquisition_cost, 2),
        }
    )

    pre_rate = {"core": 10.0, "growing": 6.3, "occasional": 2.7, "fragile": 1.2}
    retention_probability = {"core": 0.89, "growing": 0.75, "occasional": 0.51, "fragile": 0.25}
    order_value = {"core": 72, "growing": 58, "occasional": 45, "fragile": 38}
    recency_bias = {"core": 2.8, "growing": 2.0, "occasional": 1.25, "fragile": 0.68}
    order_rows: list[dict[str, object]] = []
    order_number = 1
    for idx, customer in customers.iterrows():
        archetype = latent[idx]
        start = max(pd.Timestamp(customer["signup_date"]), pd.Timestamp("2024-01-01"))
        available_years = max((OBSERVATION_END - start).days / 365.25, 0.15)
        pre_count = max(1, int(rng.poisson(pre_rate[archetype] * available_years)))
        pre_dates = _random_dates(rng, start, OBSERVATION_END, pre_count, recency_bias[archetype])
        retained = rng.binomial(1, retention_probability[archetype])
        future_count = int(rng.poisson(pre_rate[archetype] * 0.50)) if retained else 0
        if retained and future_count == 0 and rng.random() < 0.72:
            future_count = 1
        future_dates = _random_dates(rng, OBSERVATION_END + pd.Timedelta(days=1), OUTCOME_END, future_count, 1.0)
        for order_date in pre_dates + future_dates:
            gross = max(8.0, rng.gamma(shape=2.8, scale=order_value[archetype] / 2.8))
            return_probability = 0.06 + (0.03 if customer["acquisition_channel"] == "paid_social" else 0)
            returned = int(rng.random() < return_probability)
            net_revenue = 0.0 if returned else gross
            margin_rate = float(np.clip(rng.normal(0.43, 0.06), 0.20, 0.65))
            order_rows.append(
                {
                    "order_id": f"O{order_number:08d}",
                    "customer_id": customer["customer_id"],
                    "order_date": order_date.strftime("%Y-%m-%d"),
                    "gross_revenue": round(gross, 2),
                    "returned": returned,
                    "net_revenue": round(net_revenue, 2),
                    "gross_margin": round(net_revenue * margin_rate, 2),
                }
            )
            order_number += 1
    orders = pd.DataFrame(order_rows).sort_values(["order_date", "order_id"]).reset_index(drop=True)
    return customers, orders


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=77)
    parser.add_argument("--customers", type=int, default=8_000)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    customers, orders = generate(args.seed, args.customers)
    customers.to_csv(args.output_dir / "customers.csv", index=False)
    orders.to_csv(args.output_dir / "orders.csv", index=False)
    print(f"Generated {len(customers):,} customers and {len(orders):,} orders.")


if __name__ == "__main__":
    main()


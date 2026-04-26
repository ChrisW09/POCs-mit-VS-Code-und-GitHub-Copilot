"""Generate a realistic demo dataset for testing analytics endpoints."""
from __future__ import annotations

import numpy as np
import pandas as pd

RNG_SEED = 42
N_ROWS = 500


def generate_sample_dataframe(n_rows: int = N_ROWS, seed: int = RNG_SEED) -> pd.DataFrame:
    """Return a mixed numeric/categorical demo dataset."""
    rng = np.random.default_rng(seed)

    regions = ["North", "South", "East", "West", "Central"]
    segments = ["Consumer", "Corporate", "Home Office"]
    channels = ["Online", "Retail", "Partner"]

    region = rng.choice(regions, size=n_rows, p=[0.25, 0.2, 0.2, 0.2, 0.15])
    segment = rng.choice(segments, size=n_rows, p=[0.55, 0.3, 0.15])
    channel = rng.choice(channels, size=n_rows)

    age = rng.integers(18, 75, size=n_rows)
    tenure_months = rng.integers(1, 120, size=n_rows)

    base_price = rng.normal(loc=120, scale=35, size=n_rows).clip(5, None)
    quantity = rng.integers(1, 12, size=n_rows)
    discount = rng.beta(2, 8, size=n_rows).round(3)
    revenue = (base_price * quantity * (1 - discount)).round(2)

    satisfaction = rng.normal(loc=7.2, scale=1.4, size=n_rows).clip(1, 10).round(1)
    churned = rng.choice([0, 1], size=n_rows, p=[0.82, 0.18])

    start = pd.Timestamp("2024-01-01")
    order_date = start + pd.to_timedelta(rng.integers(0, 730, size=n_rows), unit="D")

    df = pd.DataFrame(
        {
            "order_date": order_date,
            "region": region,
            "segment": segment,
            "channel": channel,
            "customer_age": age,
            "tenure_months": tenure_months,
            "unit_price": base_price.round(2),
            "quantity": quantity,
            "discount": discount,
            "revenue": revenue,
            "satisfaction": satisfaction,
            "churned": churned,
        }
    )

    # Inject a small amount of missing values to make analysis realistic.
    missing_idx = rng.choice(n_rows, size=max(1, n_rows // 50), replace=False)
    df.loc[missing_idx, "satisfaction"] = np.nan
    missing_idx2 = rng.choice(n_rows, size=max(1, n_rows // 60), replace=False)
    df.loc[missing_idx2, "channel"] = None

    return df


def write_sample_csv(path) -> pd.DataFrame:
    """Write the demo dataset to ``path`` and return the DataFrame."""
    df = generate_sample_dataframe()
    df.to_csv(path, index=False)
    return df

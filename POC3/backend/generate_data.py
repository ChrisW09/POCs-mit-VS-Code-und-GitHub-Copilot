"""Generate a synthetic but realistic churn dataset and save it to data/customers.csv."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

N_ROWS = 5000
SEED = 42

CONTRACT_TYPES = ("Month-to-month", "One year", "Two year")
PAYMENT_METHODS = (
    "Electronic check",
    "Mailed check",
    "Bank transfer",
    "Credit card",
)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate(n_rows: int = N_ROWS, seed: int = SEED) -> list[dict]:
    rng = np.random.default_rng(seed)

    # --- Features -----------------------------------------------------------
    age = np.clip(rng.normal(loc=42, scale=14, size=n_rows), 18, 90).astype(int)

    # Tenure: long-tail distribution, capped at 72 months.
    tenure_months = np.clip(rng.exponential(scale=24, size=n_rows), 0, 72).astype(int)

    # Monthly charges depend slightly on tenure (loyal customers tend to pay more).
    monthly_charges = np.clip(
        rng.normal(loc=70, scale=25, size=n_rows) + tenure_months * 0.15,
        18.0,
        200.0,
    ).round(2)

    contract_type = rng.choice(
        CONTRACT_TYPES, size=n_rows, p=[0.55, 0.25, 0.20]
    )
    payment_method = rng.choice(
        PAYMENT_METHODS, size=n_rows, p=[0.35, 0.20, 0.22, 0.23]
    )

    # Support calls: Poisson, slightly higher for short-tenure customers.
    support_lambda = 1.2 + np.maximum(0, 12 - tenure_months) * 0.08
    support_calls = rng.poisson(lam=support_lambda, size=n_rows).astype(int)

    # --- Churn probability --------------------------------------------------
    contract_weight = np.where(
        contract_type == "Month-to-month",
        1.4,
        np.where(contract_type == "One year", -0.2, -1.2),
    )
    payment_weight = np.where(payment_method == "Electronic check", 0.6, -0.1)

    logit = (
        -2.4
        + contract_weight
        + payment_weight
        - 0.045 * tenure_months
        + 0.012 * (monthly_charges - 70)
        + 0.28 * support_calls
        - 0.010 * (age - 42)
    )
    # Add a bit of noise so the relationship isn't perfectly deterministic.
    logit += rng.normal(0, 0.5, size=n_rows)

    prob = _sigmoid(logit)
    churn = (rng.random(n_rows) < prob).astype(int)

    # Calibrate to ~20% churn rate by adjusting the intercept if needed.
    target_rate = 0.20
    actual_rate = churn.mean()
    if abs(actual_rate - target_rate) > 0.02:
        # Bisection on intercept shift.
        lo, hi = -3.0, 3.0
        for _ in range(40):
            mid = (lo + hi) / 2
            p = _sigmoid(logit + mid)
            r = p.mean()
            if r > target_rate:
                hi = mid
            else:
                lo = mid
        prob = _sigmoid(logit + (lo + hi) / 2)
        churn = (rng.random(n_rows) < prob).astype(int)

    rows = [
        {
            "id": i + 1,
            "age": int(age[i]),
            "tenure_months": int(tenure_months[i]),
            "monthly_charges": float(monthly_charges[i]),
            "contract_type": str(contract_type[i]),
            "payment_method": str(payment_method[i]),
            "support_calls": int(support_calls[i]),
            "churn": int(churn[i]),
        }
        for i in range(n_rows)
    ]
    return rows


def save_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "age",
        "tenure_months",
        "monthly_charges",
        "contract_type",
        "payment_method",
        "support_calls",
        "churn",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = generate()
    out_path = Path(__file__).resolve().parents[1] / "data" / "customers.csv"
    save_csv(rows, out_path)
    churn_rate = sum(r["churn"] for r in rows) / len(rows)
    print(f"Wrote {len(rows)} rows to {out_path} (churn rate: {churn_rate:.2%})")


if __name__ == "__main__":
    main()

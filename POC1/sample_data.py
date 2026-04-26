"""Hilfsmodul zur Erzeugung eines realistischen Beispieldatensatzes."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_CSV_PATH = Path(__file__).parent / "data" / "sample.csv"


def get_sample_df(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    """Erzeugt einen Beispieldatensatz mit ~500 Zeilen, gemischten Typen
    und einigen fehlenden Werten. Speichert die Datei einmalig unter
    data/sample.csv und gibt das DataFrame zurück.
    """
    rng = np.random.default_rng(seed)

    # Numerische Features
    age = rng.normal(loc=40, scale=12, size=n_rows).clip(18, 90).round(0)
    income = rng.lognormal(mean=10.5, sigma=0.45, size=n_rows).round(2)
    score = rng.normal(loc=70, scale=15, size=n_rows).clip(0, 100).round(1)
    purchases = rng.poisson(lam=4, size=n_rows)

    # Kategorische Features
    cities = rng.choice(
        ["Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart"],
        size=n_rows,
        p=[0.25, 0.18, 0.20, 0.12, 0.15, 0.10],
    )
    segments = rng.choice(["A", "B", "C", "D"], size=n_rows, p=[0.4, 0.3, 0.2, 0.1])
    subscribed = rng.choice([True, False], size=n_rows, p=[0.35, 0.65])

    # Datum
    start = np.datetime64("2024-01-01")
    days = rng.integers(0, 730, size=n_rows)
    signup_date = start + days.astype("timedelta64[D]")

    df = pd.DataFrame(
        {
            "age": age,
            "income": income,
            "score": score,
            "purchases": purchases,
            "city": cities,
            "segment": segments,
            "subscribed": subscribed,
            "signup_date": signup_date,
        }
    )

    # Fehlende Werte einstreuen (~5% pro ausgewählter Spalte)
    for col, frac in [("income", 0.05), ("score", 0.04), ("city", 0.03), ("segment", 0.02)]:
        mask = rng.random(n_rows) < frac
        df.loc[mask, col] = np.nan

    # Einmalig als CSV speichern
    if not SAMPLE_CSV_PATH.exists():
        SAMPLE_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(SAMPLE_CSV_PATH, index=False)

    return df


if __name__ == "__main__":
    df = get_sample_df()
    print(df.head())
    print(f"Gespeichert unter: {SAMPLE_CSV_PATH}")

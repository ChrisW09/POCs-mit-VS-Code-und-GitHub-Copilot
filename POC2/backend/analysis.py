"""Compute column statistics and generate plots for an upload."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .models import ColumnStat


def compute_column_stats(df: pd.DataFrame, run_id: int) -> list[ColumnStat]:
    stats: list[ColumnStat] = []
    for col in df.columns:
        series = df[col]
        dtype = str(series.dtype)
        count = int(series.count())
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))

        stat = ColumnStat(
            run_id=run_id,
            column_name=str(col),
            dtype=dtype,
            count=count,
            missing=missing,
            unique=unique,
        )

        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if not non_null.empty:
                stat.mean = float(non_null.mean())
                stat.std = float(non_null.std()) if len(non_null) > 1 else 0.0
                stat.min = float(non_null.min())
                stat.max = float(non_null.max())
        else:
            non_null = series.dropna().astype(str)
            if not non_null.empty:
                vc = non_null.value_counts()
                stat.top = str(vc.index[0])
                stat.freq = int(vc.iloc[0])

        stats.append(stat)
    return stats


def generate_plot(df: pd.DataFrame, output_path: Path) -> Path:
    """Render an overview plot (histograms for numeric, bars for categorical)."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [
        c for c in df.select_dtypes(exclude=[np.number, "datetime64[ns]"]).columns
    ]

    panels: list[tuple[str, str]] = []  # (column, kind)
    panels += [(c, "hist") for c in numeric_cols[:4]]
    panels += [(c, "bar") for c in cat_cols[:2]]
    if not panels:
        panels = [(df.columns[0], "bar")]

    n = len(panels)
    cols = 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows))
    axes = np.atleast_1d(axes).flatten()

    for ax, (col, kind) in zip(axes, panels):
        if kind == "hist":
            df[col].dropna().plot(kind="hist", bins=30, ax=ax, edgecolor="white")
            ax.set_title(f"Distribution: {col}")
            ax.set_xlabel(col)
        else:
            counts = df[col].astype(str).value_counts().head(10)
            counts.plot(kind="bar", ax=ax)
            ax.set_title(f"Top values: {col}")
            ax.tick_params(axis="x", rotation=30)

    for ax in axes[len(panels):]:
        ax.set_visible(False)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=110)
    plt.close(fig)
    return output_path

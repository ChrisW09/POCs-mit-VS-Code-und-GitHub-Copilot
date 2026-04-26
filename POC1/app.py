"""Streamlit-App: CSV-Upload oder Beispieldaten analysieren."""
from __future__ import annotations

import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from sample_data import get_sample_df

st.set_page_config(page_title="CSV Explorer", layout="wide")
st.title("📊 CSV Explorer")
st.caption("Lade eine eigene CSV hoch oder nutze die integrierten Beispieldaten.")

# --- Datenquelle auswählen ---
col1, col2 = st.columns([2, 1])
with col1:
    uploaded = st.file_uploader("Eigene CSV hochladen", type=["csv"])
with col2:
    st.write("")
    st.write("")
    use_sample = st.button("Beispieldaten laden", use_container_width=True)

# Auswahl in Session State persistieren
if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.source = None

if uploaded is not None:
    try:
        st.session_state.df = pd.read_csv(uploaded)
        st.session_state.source = f"Upload: {uploaded.name}"
    except Exception as e:
        st.error(f"Fehler beim Lesen der CSV: {e}")

if use_sample:
    st.session_state.df = get_sample_df()
    st.session_state.source = "Beispieldatensatz"

df: pd.DataFrame | None = st.session_state.df

if df is None:
    st.info("Bitte eine CSV hochladen oder auf **Beispieldaten laden** klicken.")
    st.stop()

st.success(f"Quelle: {st.session_state.source}")

# --- (1) Zeilen-/Spaltenanzahl ---
st.subheader("1. Übersicht")
c1, c2 = st.columns(2)
c1.metric("Zeilen", f"{df.shape[0]:,}")
c2.metric("Spalten", f"{df.shape[1]:,}")

with st.expander("Datenvorschau (erste 20 Zeilen)"):
    st.dataframe(df.head(20), use_container_width=True)

# --- (2) Datentypen und fehlende Werte ---
st.subheader("2. Datentypen & fehlende Werte")
info_df = pd.DataFrame(
    {
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(2),
    }
)
st.dataframe(info_df, use_container_width=True)

# --- (3) describe() ---
st.subheader("3. Statistische Kennzahlen (describe)")
try:
    st.dataframe(df.describe(include="all").T, use_container_width=True)
except Exception as e:
    st.warning(f"describe() konnte nicht vollständig berechnet werden: {e}")
    st.dataframe(df.describe().T, use_container_width=True)

# --- (4) Histogramm + Boxplot je numerische Spalte ---
st.subheader("4. Verteilungen numerischer Spalten")
numeric_cols = df.select_dtypes(include="number").columns.tolist()

if not numeric_cols:
    st.info("Keine numerischen Spalten gefunden.")
else:
    for col in numeric_cols:
        st.markdown(f"**{col}**")
        series = df[col].dropna()
        fig, axes = plt.subplots(1, 2, figsize=(10, 3))
        axes[0].hist(series, bins=30, color="#4C8BF5", edgecolor="white")
        axes[0].set_title(f"Histogramm – {col}")
        axes[0].set_xlabel(col)
        axes[0].set_ylabel("Häufigkeit")

        axes[1].boxplot(series, vert=False)
        axes[1].set_title(f"Boxplot – {col}")
        axes[1].set_xlabel(col)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

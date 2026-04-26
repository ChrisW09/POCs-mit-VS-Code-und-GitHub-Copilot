"""Streamlit frontend for POC2 analytics backend."""
from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
TIMEOUT = 60

st.set_page_config(page_title="POC2 – Analytics", layout="wide")
st.title("POC2 – Daten-Analyse")

# Session state defaults
st.session_state.setdefault("upload_id", None)
st.session_state.setdefault("upload_filename", None)
st.session_state.setdefault("analysis_done", False)


def _api_url(path: str) -> str:
    return f"{API_BASE.rstrip('/')}{path}"


def _reset_analysis() -> None:
    st.session_state["analysis_done"] = False


# --- Datenquelle -------------------------------------------------------------
st.header("1. Datenquelle wählen")
source = st.radio(
    "Datenquelle",
    options=["Eigene CSV", "Beispieldaten"],
    horizontal=True,
    label_visibility="collapsed",
)

if source == "Eigene CSV":
    uploaded = st.file_uploader("CSV-Datei auswählen", type=["csv", "tsv"])
    if uploaded is not None and st.button("Hochladen", type="primary"):
        try:
            files = {"file": (uploaded.name, uploaded.getvalue(), "text/csv")}
            resp = requests.post(_api_url("/api/upload"), files=files, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            st.session_state["upload_id"] = data["id"]
            st.session_state["upload_filename"] = data["filename"]
            _reset_analysis()
            st.success(
                f"Upload erfolgreich: {data['filename']} "
                f"({data['rows']} Zeilen, {data['columns']} Spalten) – ID {data['id']}"
            )
        except requests.RequestException as exc:
            st.error(f"Upload fehlgeschlagen: {exc}")
else:
    if st.button("Beispieldaten laden", type="primary"):
        try:
            resp = requests.post(_api_url("/api/sample"), timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            st.session_state["upload_id"] = data["upload_id"]
            st.session_state["upload_filename"] = "sample.csv"
            _reset_analysis()
            msg = "Neuer Beispiel-Upload angelegt" if data["created"] else "Bestehenden Beispiel-Upload geladen"
            st.success(f"{msg} – upload_id {data['upload_id']}")
        except requests.RequestException as exc:
            st.error(f"Beispieldaten konnten nicht geladen werden: {exc}")

upload_id = st.session_state.get("upload_id")
if upload_id is not None:
    st.info(
        f"Aktiver Upload: **{st.session_state.get('upload_filename')}** "
        f"(ID {upload_id})"
    )

# --- Analyse ----------------------------------------------------------------
st.header("2. Analyse")
analyze_disabled = upload_id is None
if st.button("Analyse starten", disabled=analyze_disabled):
    with st.spinner("Analyse läuft …"):
        try:
            resp = requests.post(
                _api_url(f"/api/analyze/{upload_id}"), timeout=TIMEOUT
            )
            resp.raise_for_status()
            st.session_state["analysis_done"] = True
            st.success("Analyse abgeschlossen.")
        except requests.RequestException as exc:
            st.session_state["analysis_done"] = False
            st.error(f"Analyse fehlgeschlagen: {exc}")

# --- Ergebnisse -------------------------------------------------------------
if st.session_state.get("analysis_done") and upload_id is not None:
    st.header("3. Ergebnisse")

    col_stats, col_plot = st.columns([3, 2])

    with col_stats:
        st.subheader("Spalten-Statistiken")
        try:
            r = requests.get(_api_url(f"/api/stats/{upload_id}"), timeout=TIMEOUT)
            r.raise_for_status()
            payload = r.json()
            run = payload.get("run", {})
            st.caption(
                f"Run #{run.get('id')} – Status: {run.get('status')} – "
                f"finished: {run.get('finished_at')}"
            )
            st.dataframe(payload.get("stats", []), use_container_width=True)
        except requests.RequestException as exc:
            st.error(f"Stats konnten nicht geladen werden: {exc}")

    with col_plot:
        st.subheader("Übersichts-Plot")
        try:
            r = requests.get(_api_url(f"/api/plots/{upload_id}"), timeout=TIMEOUT)
            r.raise_for_status()
            st.image(r.content, use_column_width=True)
        except requests.RequestException as exc:
            st.error(f"Plot konnte nicht geladen werden: {exc}")

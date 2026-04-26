"""Streamlit frontend for the Churn POC."""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"
TIMEOUT = 10

CONTRACT_TYPES = ["Month-to-month", "One year", "Two year"]
PAYMENT_METHODS = [
    "Electronic check",
    "Mailed check",
    "Bank transfer",
    "Credit card",
]

st.set_page_config(page_title="Churn POC", layout="wide")
st.title("Churn Prediction POC")


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
def api_get(path: str, params: dict | None = None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def api_post(path: str, json: dict | None = None):
    r = requests.post(f"{API_URL}{path}", json=json, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def render_prediction(result: dict) -> None:
    proba = float(result["churn_probability"])
    pred = int(result["churn_prediction"])
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Churn-Wahrscheinlichkeit",
            f"{proba:.1%}",
            delta="HIGH RISK" if pred == 1 else "low risk",
            delta_color="inverse",
        )
    with col2:
        st.metric("Vorhersage", "Churn" if pred == 1 else "Kein Churn")
    st.progress(min(max(proba, 0.0), 1.0))
    with st.expander("Details"):
        st.json(result)


# ---------------------------------------------------------------------------
# Form state defaults
# ---------------------------------------------------------------------------
DEFAULTS = {
    "f_age": 40,
    "f_tenure_months": 12,
    "f_monthly_charges": 70.0,
    "f_contract_type": "Month-to-month",
    "f_payment_method": "Electronic check",
    "f_support_calls": 1,
}
for key, val in DEFAULTS.items():
    st.session_state.setdefault(key, val)


def apply_features(features: dict) -> None:
    st.session_state["f_age"] = int(features["age"])
    st.session_state["f_tenure_months"] = int(features["tenure_months"])
    st.session_state["f_monthly_charges"] = float(features["monthly_charges"])
    st.session_state["f_contract_type"] = features["contract_type"]
    st.session_state["f_payment_method"] = features["payment_method"]
    st.session_state["f_support_calls"] = int(features["support_calls"])


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_customers, tab_predict, tab_history = st.tabs(
    ["Kunden", "Vorhersage", "Historie"]
)

# ---------- Kunden ----------
with tab_customers:
    st.subheader("Kundenliste")
    contract_filter = st.selectbox(
        "Filter: contract_type",
        ["(alle)"] + CONTRACT_TYPES,
        key="filter_contract",
    )
    limit = st.slider("Anzahl Zeilen", 10, 1000, 200, step=10)

    try:
        customers = api_get("/api/customers", params={"limit": limit})
    except Exception as exc:
        st.error(f"Fehler beim Laden: {exc}")
        customers = []

    df = pd.DataFrame(customers)
    if not df.empty and contract_filter != "(alle)":
        df = df[df["contract_type"] == contract_filter]

    st.caption(f"{len(df)} Zeilen")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ---------- Vorhersage ----------
with tab_predict:
    st.subheader("Churn-Vorhersage")

    col_a, col_b = st.columns(2)

    with col_a:
        profile = st.selectbox(
            "Beispiel-Profil",
            ["random", "high_risk", "low_risk"],
            key="sample_profile",
        )
        if st.button("Beispielkunde laden"):
            try:
                sample = api_get(
                    "/api/sample-customer", params={"profile": profile}
                )
                apply_features(sample["features"])
                st.success(f"Beispiel ({sample['label']}) geladen.")
                st.rerun()
            except Exception as exc:
                st.error(f"Fehler: {exc}")

    with col_b:
        try:
            customer_options = api_get(
                "/api/customers", params={"limit": 1000}
            )
        except Exception:
            customer_options = []
        ids = [c["id"] for c in customer_options]
        chosen_id = st.selectbox(
            "Vorhandenen Kunden wählen",
            options=[None] + ids,
            format_func=lambda x: "—" if x is None else f"Kunde #{x}",
            key="chosen_customer",
        )
        if st.button("Vorhersage für gewählten Kunden") and chosen_id:
            try:
                result = api_post(f"/api/predict/{chosen_id}")
                st.session_state["last_prediction"] = result
            except Exception as exc:
                st.error(f"Fehler: {exc}")

    st.divider()

    with st.form("predict_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input("Alter", min_value=18, max_value=100, key="f_age")
            st.number_input(
                "Tenure (Monate)", min_value=0, max_value=120, key="f_tenure_months"
            )
        with c2:
            st.number_input(
                "Monatliche Gebühr",
                min_value=0.0,
                max_value=500.0,
                step=1.0,
                key="f_monthly_charges",
            )
            st.number_input(
                "Support Calls", min_value=0, max_value=50, key="f_support_calls"
            )
        with c3:
            st.selectbox(
                "Vertragsart", CONTRACT_TYPES, key="f_contract_type"
            )
            st.selectbox(
                "Zahlungsart", PAYMENT_METHODS, key="f_payment_method"
            )

        submitted = st.form_submit_button("Predict")

    if submitted:
        payload = {
            "age": st.session_state["f_age"],
            "tenure_months": st.session_state["f_tenure_months"],
            "monthly_charges": st.session_state["f_monthly_charges"],
            "contract_type": st.session_state["f_contract_type"],
            "payment_method": st.session_state["f_payment_method"],
            "support_calls": st.session_state["f_support_calls"],
        }
        try:
            result = api_post("/api/predict", json=payload)
            st.session_state["last_prediction"] = result
        except Exception as exc:
            st.error(f"Fehler: {exc}")

    if "last_prediction" in st.session_state:
        st.divider()
        render_prediction(st.session_state["last_prediction"])


# ---------- Historie ----------
with tab_history:
    st.subheader("Prediction-Historie")
    try:
        preds = api_get("/api/predictions", params={"limit": 500})
    except Exception as exc:
        st.error(f"Fehler beim Laden: {exc}")
        preds = []
    df = pd.DataFrame(preds)
    st.caption(f"{len(df)} Predictions")
    st.dataframe(df, use_container_width=True, hide_index=True)

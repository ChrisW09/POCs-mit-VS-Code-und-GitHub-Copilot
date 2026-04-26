"""FastAPI app for the Churn POC."""

from __future__ import annotations

import json
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, SessionLocal, engine
from .train_model import (
    CATEGORICAL_COLUMNS,
    DATA_PATH,
    MODEL_PATH,
    train as run_training,
)

BACKEND_DIR = Path(__file__).resolve().parent
GENERATE_SCRIPT = BACKEND_DIR / "generate_data.py"

# In-memory model state.
_model_state: dict = {"model": None, "columns": []}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_csv() -> None:
    if DATA_PATH.exists():
        return
    print(f"[startup] {DATA_PATH} missing - running generate_data.py")
    subprocess.run([sys.executable, str(GENERATE_SCRIPT)], check=True)


def _seed_customers_if_empty(db: Session) -> int:
    if db.query(models.Customer).count() > 0:
        return 0
    _ensure_csv()
    df = pd.read_csv(DATA_PATH)
    rows = [
        models.Customer(
            id=int(r["id"]),
            age=int(r["age"]),
            tenure_months=int(r["tenure_months"]),
            monthly_charges=float(r["monthly_charges"]),
            contract_type=str(r["contract_type"]),
            payment_method=str(r["payment_method"]),
            support_calls=int(r["support_calls"]),
            churn=int(r["churn"]) if "churn" in df.columns else None,
        )
        for _, r in df.iterrows()
    ]
    db.bulk_save_objects(rows)
    db.commit()
    print(f"[startup] Imported {len(rows)} customers from {DATA_PATH}")
    return len(rows)


def _load_model_if_available() -> None:
    if not MODEL_PATH.exists():
        _model_state["model"] = None
        _model_state["columns"] = []
        return
    bundle = joblib.load(MODEL_PATH)
    _model_state["model"] = bundle["model"]
    _model_state["columns"] = list(bundle["columns"])
    print(f"[startup] Loaded model from {MODEL_PATH}")


def _features_to_frame(features: schemas.CustomerFeatures) -> pd.DataFrame:
    df = pd.DataFrame([features.model_dump()])
    df = pd.get_dummies(df, columns=CATEGORICAL_COLUMNS, drop_first=False)
    cols = _model_state["columns"]
    # Add missing one-hot columns and order them.
    for col in cols:
        if col not in df.columns:
            df[col] = 0
    df = df[cols]
    return df


def _predict(features: schemas.CustomerFeatures) -> tuple[float, int]:
    model = _model_state["model"]
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Call POST /api/train first.",
        )
    X = _features_to_frame(features)
    proba = float(model.predict_proba(X)[0, 1])
    pred = int(proba >= 0.5)
    return proba, pred


def _latest_model_run(db: Session) -> Optional[models.ModelRun]:
    return (
        db.query(models.ModelRun)
        .order_by(models.ModelRun.created_at.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_customers_if_empty(db)
    finally:
        db.close()
    _load_model_if_available()
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Churn POC API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": _model_state["model"] is not None}


# ---------- Customers ----------
@app.get("/api/customers", response_model=list[schemas.CustomerOut])
def list_customers(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Customer)
        .order_by(models.Customer.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/api/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.get("/api/sample-customer", response_model=schemas.SampleCustomer)
def sample_customer(
    profile: str = "random",
    db: Session = Depends(get_db),
):
    """Return a sample feature vector for testing predictions.

    profile: "random" | "high_risk" | "low_risk"
    """
    profile = profile.lower()

    if profile == "high_risk":
        features = schemas.CustomerFeatures(
            age=29,
            tenure_months=2,
            monthly_charges=95.5,
            contract_type="Month-to-month",
            payment_method="Electronic check",
            support_calls=6,
        )
        return schemas.SampleCustomer(label="high_risk", features=features)

    if profile == "low_risk":
        features = schemas.CustomerFeatures(
            age=52,
            tenure_months=58,
            monthly_charges=65.0,
            contract_type="Two year",
            payment_method="Bank transfer",
            support_calls=0,
        )
        return schemas.SampleCustomer(label="low_risk", features=features)

    # Random real customer.
    customer = (
        db.query(models.Customer).order_by(func.random()).limit(1).first()
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="No customers available")
    features = schemas.CustomerFeatures(
        age=customer.age,
        tenure_months=customer.tenure_months,
        monthly_charges=customer.monthly_charges,
        contract_type=customer.contract_type,
        payment_method=customer.payment_method,
        support_calls=customer.support_calls,
    )
    return schemas.SampleCustomer(
        label="random", features=features, customer_id=customer.id
    )


# ---------- Predictions ----------
@app.post("/api/predict", response_model=schemas.PredictionOut)
def predict(
    payload: schemas.PredictionRequest,
    db: Session = Depends(get_db),
):
    proba, pred = _predict(payload)
    run = _latest_model_run(db)
    record = models.Prediction(
        customer_id=None,
        age=payload.age,
        tenure_months=payload.tenure_months,
        monthly_charges=payload.monthly_charges,
        contract_type=payload.contract_type,
        payment_method=payload.payment_method,
        support_calls=payload.support_calls,
        churn_probability=proba,
        churn_prediction=pred,
        model_run_id=run.id if run else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.post("/api/predict/{customer_id}", response_model=schemas.PredictionOut)
def predict_for_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    features = schemas.CustomerFeatures(
        age=customer.age,
        tenure_months=customer.tenure_months,
        monthly_charges=customer.monthly_charges,
        contract_type=customer.contract_type,
        payment_method=customer.payment_method,
        support_calls=customer.support_calls,
    )
    proba, pred = _predict(features)
    run = _latest_model_run(db)
    record = models.Prediction(
        customer_id=customer.id,
        age=customer.age,
        tenure_months=customer.tenure_months,
        monthly_charges=customer.monthly_charges,
        contract_type=customer.contract_type,
        payment_method=customer.payment_method,
        support_calls=customer.support_calls,
        churn_probability=proba,
        churn_prediction=pred,
        model_run_id=run.id if run else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/api/predictions", response_model=list[schemas.PredictionOut])
def list_predictions(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Prediction)
        .order_by(models.Prediction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# ---------- Training ----------
@app.post("/api/train", response_model=schemas.TrainResponse)
def train_endpoint(db: Session = Depends(get_db)):
    result = run_training()
    run = models.ModelRun(
        accuracy=result["accuracy"],
        roc_auc=result["roc_auc"],
        n_train=result["n_train"],
        n_test=result["n_test"],
        feature_columns=json.dumps(result["columns"]),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    _load_model_if_available()
    return schemas.TrainResponse(
        accuracy=result["accuracy"],
        roc_auc=result["roc_auc"],
        n_train=result["n_train"],
        n_test=result["n_test"],
        model_run_id=run.id,
    )


@app.get("/api/model/info", response_model=schemas.ModelInfo)
def model_info(db: Session = Depends(get_db)):
    last_run = _latest_model_run(db)
    return schemas.ModelInfo(
        loaded=_model_state["model"] is not None,
        model_path=str(MODEL_PATH),
        feature_columns=list(_model_state["columns"]),
        last_run=last_run,
    )

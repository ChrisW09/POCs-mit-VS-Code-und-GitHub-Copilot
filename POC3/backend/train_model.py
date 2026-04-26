"""Train an XGBoost churn classifier and persist it to backend/model.pkl."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_PATH = PROJECT_DIR / "data" / "customers.csv"
MODEL_PATH = BACKEND_DIR / "model.pkl"

CATEGORICAL_COLUMNS = ["contract_type", "payment_method"]
TARGET = "churn"
DROP_COLUMNS = ["id", TARGET]


def ensure_dataset() -> None:
    if DATA_PATH.exists():
        return
    print(f"{DATA_PATH} not found - running generate_data.py ...")
    subprocess.run(
        [sys.executable, str(BACKEND_DIR / "generate_data.py")],
        check=True,
    )


def load_features() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(DATA_PATH)
    y = df[TARGET].astype(int)
    X = df.drop(columns=DROP_COLUMNS)
    X = pd.get_dummies(X, columns=CATEGORICAL_COLUMNS, drop_first=False)
    return X, y


def train() -> dict:
    """Train the model and persist it. Returns metrics + metadata."""
    ensure_dataset()
    X, y = load_features()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    acc = float(accuracy_score(y_test, preds))
    auc = float(roc_auc_score(y_test, proba))

    columns = list(X.columns)
    joblib.dump({"model": model, "columns": columns}, MODEL_PATH)

    return {
        "accuracy": acc,
        "roc_auc": auc,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "columns": columns,
        "model_path": str(MODEL_PATH),
    }


def main() -> None:
    result = train()
    print(f"Accuracy: {result['accuracy']:.4f}")
    print(f"ROC-AUC : {result['roc_auc']:.4f}")
    print(f"Saved model to {result['model_path']}")


if __name__ == "__main__":
    main()

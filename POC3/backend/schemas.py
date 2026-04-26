"""Pydantic schemas for API I/O."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ContractType = Literal["Month-to-month", "One year", "Two year"]
PaymentMethod = Literal[
    "Electronic check",
    "Mailed check",
    "Bank transfer",
    "Credit card",
]


class CustomerFeatures(BaseModel):
    age: int = Field(..., ge=18, le=100)
    tenure_months: int = Field(..., ge=0, le=120)
    monthly_charges: float = Field(..., ge=0)
    contract_type: ContractType
    payment_method: PaymentMethod
    support_calls: int = Field(..., ge=0)


class CustomerOut(CustomerFeatures):
    model_config = ConfigDict(from_attributes=True)

    id: int
    churn: Optional[int] = None
    created_at: Optional[datetime] = None


class PredictionRequest(CustomerFeatures):
    pass


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: Optional[int] = None
    age: int
    tenure_months: int
    monthly_charges: float
    contract_type: str
    payment_method: str
    support_calls: int
    churn_probability: float
    churn_prediction: int
    model_run_id: Optional[int] = None
    created_at: datetime


class ModelRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    accuracy: Optional[float] = None
    roc_auc: Optional[float] = None
    n_train: Optional[int] = None
    n_test: Optional[int] = None
    created_at: datetime


class ModelInfo(BaseModel):
    loaded: bool
    model_path: str
    feature_columns: list[str] = []
    last_run: Optional[ModelRunOut] = None


class TrainResponse(BaseModel):
    accuracy: float
    roc_auc: float
    n_train: int
    n_test: int
    model_run_id: int


class SampleCustomer(BaseModel):
    label: str  # "random" | "high_risk" | "low_risk"
    features: CustomerFeatures
    customer_id: Optional[int] = None

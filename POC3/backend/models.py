"""SQLAlchemy ORM models for the churn POC."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    monthly_charges = Column(Float, nullable=False)
    contract_type = Column(String, nullable=False)
    payment_method = Column(String, nullable=False)
    support_calls = Column(Integer, nullable=False)
    churn = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship(
        "Prediction", back_populates="customer", cascade="all, delete-orphan"
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    age = Column(Integer, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    monthly_charges = Column(Float, nullable=False)
    contract_type = Column(String, nullable=False)
    payment_method = Column(String, nullable=False)
    support_calls = Column(Integer, nullable=False)
    churn_probability = Column(Float, nullable=False)
    churn_prediction = Column(Integer, nullable=False)
    model_run_id = Column(Integer, ForeignKey("model_runs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="predictions")
    model_run = relationship("ModelRun", back_populates="predictions")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    accuracy = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    n_train = Column(Integer, nullable=True)
    n_test = Column(Integer, nullable=True)
    feature_columns = Column(Text, nullable=True)  # JSON-encoded list
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="model_run")

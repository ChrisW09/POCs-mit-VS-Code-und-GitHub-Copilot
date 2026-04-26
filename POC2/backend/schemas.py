from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    rows: int
    columns: int
    created_at: datetime


class ColumnStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    column_name: str
    dtype: str
    count: int
    missing: int
    unique: int
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    top: Optional[str] = None
    freq: Optional[int] = None


class AnalysisRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    upload_id: int
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class StatsOut(BaseModel):
    run: AnalysisRunOut
    stats: List[ColumnStatOut]


class SampleOut(BaseModel):
    upload_id: int
    created: bool

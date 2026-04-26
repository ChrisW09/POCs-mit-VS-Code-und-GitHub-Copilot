from datetime import datetime

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
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    top: str | None = None
    freq: int | None = None


class AnalysisRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    upload_id: int
    status: str
    created_at: datetime
    finished_at: datetime | None = None
    error: str | None = None


class StatsOut(BaseModel):
    run: AnalysisRunOut
    stats: list[ColumnStatOut]


class SampleOut(BaseModel):
    upload_id: int
    created: bool

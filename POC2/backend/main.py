from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import schemas
from .analysis import compute_column_stats, generate_plot
from .database import Base, PLOT_DIR, UPLOAD_DIR, engine, get_db, SessionLocal
from .models import AnalysisRun, ColumnStat, Upload
from .sample_data import write_sample_csv

SAMPLE_FILENAME = "sample.csv"


def _create_sample_upload(db: Session) -> Upload:
    target = UPLOAD_DIR / SAMPLE_FILENAME
    df = write_sample_csv(target)
    upload = Upload(
        filename=SAMPLE_FILENAME,
        file_path=str(target),
        rows=int(df.shape[0]),
        columns=int(df.shape[1]),
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def _seed_sample_if_empty() -> None:
    with SessionLocal() as db:
        if db.query(Upload).count() == 0:
            _create_sample_upload(db)


app = FastAPI(title="POC2 Analytics Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _seed_sample_if_empty()


@app.post("/api/upload", response_model=schemas.UploadOut)
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    if not file.filename.lower().endswith((".csv", ".tsv")):
        raise HTTPException(status_code=400, detail="Only CSV/TSV files are supported")

    safe_name = Path(file.filename).name
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    stored_name = f"{timestamp}_{safe_name}"
    target = UPLOAD_DIR / stored_name

    contents = file.file.read()
    target.write_bytes(contents)

    sep = "\t" if safe_name.lower().endswith(".tsv") else ","
    try:
        df = pd.read_csv(target, sep=sep)
    except Exception as exc:  # pragma: no cover
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}")

    upload = Upload(
        filename=safe_name,
        file_path=str(target),
        rows=int(df.shape[0]),
        columns=int(df.shape[1]),
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


@app.get("/api/uploads", response_model=List[schemas.UploadOut])
def list_uploads(db: Session = Depends(get_db)):
    return db.query(Upload).order_by(Upload.created_at.desc()).all()


@app.post("/api/sample", response_model=schemas.SampleOut)
def create_or_get_sample(db: Session = Depends(get_db)):
    existing = (
        db.query(Upload)
        .filter(Upload.filename == SAMPLE_FILENAME)
        .order_by(Upload.created_at.asc())
        .first()
    )
    if existing:
        return schemas.SampleOut(upload_id=existing.id, created=False)
    upload = _create_sample_upload(db)
    return schemas.SampleOut(upload_id=upload.id, created=True)


@app.post("/api/analyze/{upload_id}", response_model=schemas.AnalysisRunOut)
def analyze_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.get(Upload, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")

    run = AnalysisRun(upload_id=upload.id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        path = Path(upload.file_path)
        sep = "\t" if path.suffix.lower() == ".tsv" else ","
        df = pd.read_csv(path, sep=sep)

        stats = compute_column_stats(df, run_id=run.id)
        db.add_all(stats)

        plot_path = PLOT_DIR / f"run_{run.id}.png"
        generate_plot(df, plot_path)

        run.plot_path = str(plot_path)
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
        run.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    return run


def _latest_completed_run(db: Session, upload_id: int) -> AnalysisRun:
    upload = db.get(Upload, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.upload_id == upload_id, AnalysisRun.status == "completed")
        .order_by(AnalysisRun.created_at.desc())
        .first()
    )
    if run is None:
        raise HTTPException(
            status_code=404,
            detail="No completed analysis run for this upload. Call /api/analyze first.",
        )
    return run


@app.get("/api/stats/{upload_id}", response_model=schemas.StatsOut)
def get_stats(upload_id: int, db: Session = Depends(get_db)):
    run = _latest_completed_run(db, upload_id)
    stats = (
        db.query(ColumnStat)
        .filter(ColumnStat.run_id == run.id)
        .order_by(ColumnStat.id.asc())
        .all()
    )
    return schemas.StatsOut(run=schemas.AnalysisRunOut.model_validate(run), stats=stats)


@app.get("/api/plots/{upload_id}")
def get_plot(upload_id: int, db: Session = Depends(get_db)):
    run = _latest_completed_run(db, upload_id)
    if not run.plot_path or not Path(run.plot_path).exists():
        raise HTTPException(status_code=404, detail="Plot file missing")
    return FileResponse(run.plot_path, media_type="image/png")


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

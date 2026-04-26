# POC2 – Analytics Backend

FastAPI + SQLAlchemy + SQLite backend for uploading CSVs, computing column
statistics, and rendering an overview plot.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn backend.main:app --reload
```

The first startup creates the SQLite DB under `data/app.db` and seeds a demo
dataset (`data/uploads/sample.csv`, ~500 rows, mixed numeric/categorical).

CORS is enabled for `http://localhost:8501` (Streamlit frontend).

## Endpoints

| Method | Path                       | Description                                 |
| ------ | -------------------------- | ------------------------------------------- |
| POST   | `/api/upload`              | Upload a CSV/TSV file                       |
| GET    | `/api/uploads`             | List all uploads                            |
| POST   | `/api/sample`              | Create or return the demo upload (`upload_id`) |
| POST   | `/api/analyze/{upload_id}` | Run analysis (stats + plot)                 |
| GET    | `/api/stats/{upload_id}`   | Latest column stats for an upload           |
| GET    | `/api/plots/{upload_id}`   | Latest plot (PNG) for an upload             |

## Models

- `Upload` – uploaded file metadata
- `AnalysisRun` – one analysis execution per upload
- `ColumnStat` – per-column metrics for a run

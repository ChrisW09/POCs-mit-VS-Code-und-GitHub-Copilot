# POC 3 — Churn Prediction (End-to-End ML)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.x-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.x-EB0028)](https://xgboost.readthedocs.io/)
[![joblib](https://img.shields.io/badge/joblib-model%20persistence-3F88C5)](https://joblib.readthedocs.io/)
[![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.x-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![Architecture](https://img.shields.io/badge/architecture-end--to--end%20ML-blueviolet)](#architektur)
[![Status](https://img.shields.io/badge/status-teaching%20demo-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

> **Komplexitätsstufe 3 — End-to-End ML.** Vollständige ML-Anwendung in vier
> Schichten: **Daten → Training → API → UI**. Synthetische Kunden, ein
> XGBoost-Modell, eine FastAPI-Service-Schicht und ein Streamlit-Frontend mit
> drei Tabs.

Das ist die typische Architektur einer kleinen produktionsnahen ML-App —
auf das absolute Minimum reduziert, damit man sie in einer Sitzung
nachbauen kann.

---

## Was die App kann

- **Datenerzeugung** (`generate_data.py`): synthetisiert ~5 000 Kunden mit
  plausiblen Korrelationen zur Zielvariable `churn` (Churn-Rate ~20 %).
- **Training** (`train_model.py`): One-Hot-Encoding der kategorischen Spalten,
  stratified 80/20-Split, **XGBoost-Klassifikator**, persistiert Modell
  + Feature-Spalten als `backend/model.pkl` (joblib).
- **Backend** (FastAPI + SQLAlchemy + SQLite): seedet Kunden beim Start,
  liefert CRUD-artige Reads, **einzelne und Batch-Vorhersagen**, einen
  Trainings-Trigger und Modell-Metadaten. Speichert jede Vorhersage als
  Audit-Trail.
- **Frontend** (Streamlit, drei Tabs): **Kundenliste mit Filter**,
  **Vorhersage-Formular** (mit Profilen *random / high_risk / low_risk* und
  Auswahl bestehender Kunden), **Historie** der letzten Predictions.

---

## Architektur

```mermaid
flowchart LR
    USER(["👤 User"]) --> FE

    subgraph FRONT["💻 Frontend (Port 8501)"]
        direction TB
        FE["Streamlit<br/>frontend/app.py<br/>Tabs: Kunden · Vorhersage · Historie"]
    end

    FE -- "HTTP / JSON" --> BE

    subgraph BACK["⚙️ Backend (Port 8000)"]
        direction TB
        BE["FastAPI<br/>backend/main.py<br/>Routen + Lifespan"]
        BE --> SCH["schemas.py<br/>Pydantic"]
        BE --> ORM["models.py<br/>SQLAlchemy"]
        BE -- "predict_proba" --> MODEL{{"In-Memory<br/>_model_state"}}
    end

    ORM --> DB[("🗄️ SQLite<br/>customers · predictions · model_runs")]

    subgraph PIPE["🔬 Offline-Pipeline (einmalig oder via /api/train)"]
        direction LR
        GEN["generate_data.py<br/>numpy"] --> CSV[("data/customers.csv")]
        CSV --> TRAIN["train_model.py<br/>sklearn split + XGBoost"]
        TRAIN --> PKL[("backend/model.pkl<br/>joblib bundle:<br/>model + feature columns")]
    end

    CSV -. Startup-Seed .-> DB
    PKL -. Startup-Load .-> MODEL
    BE -. "POST /api/train" .-> TRAIN

    style USER fill:#dbeafe,stroke:#1e40af
    style FRONT fill:#f3e8ff,stroke:#6b21a8
    style BACK fill:#fef3c7,stroke:#b45309
    style PIPE fill:#fce7f3,stroke:#9d174d
    style DB fill:#bbf7d0,stroke:#15803d
    style PKL fill:#bbf7d0,stroke:#15803d
    style CSV fill:#bbf7d0,stroke:#15803d
```

**Vier Schichten — kurz:**

1. **Daten:** synthetische CSV (`generate_data.py`).
2. **Modell:** trainiert offline und als `.pkl` persistiert.
3. **Service:** FastAPI lädt das Modell in Memory, beantwortet HTTP-Predicts.
4. **UI:** Streamlit ruft die Service-Schicht und zeigt Tabs.

---

## Datenmodell

```mermaid
erDiagram
    CUSTOMER ||--o{ PREDICTION : "0..n"
    MODEL_RUN ||--o{ PREDICTION : "0..n"

    CUSTOMER {
      int id PK
      int age
      int tenure_months
      float monthly_charges
      string contract_type
      string payment_method
      int support_calls
      int churn
      datetime created_at
    }
    PREDICTION {
      int id PK
      int customer_id FK
      int age
      int tenure_months
      float monthly_charges
      string contract_type
      string payment_method
      int support_calls
      float churn_probability
      int churn_prediction
      int model_run_id FK
      datetime created_at
    }
    MODEL_RUN {
      int id PK
      float accuracy
      float roc_auc
      int n_train
      int n_test
      text feature_columns
      datetime created_at
    }
```

### Eine Vorhersage von oben nach unten

```mermaid
sequenceDiagram
    actor User
    participant FE as Streamlit Frontend
    participant BE as FastAPI Backend
    participant M as In-Memory Modell
    participant DB as SQLite

    Note over BE: Lifespan-Hook beim Start:<br/>customers seeden + model.pkl laden
    User->>FE: Tab „Vorhersage" → Beispielkunde laden (high_risk)
    FE->>BE: GET /api/sample-customer?profile=high_risk
    BE-->>FE: Feature-Vektor
    User->>FE: Klick „Predict"
    FE->>BE: POST /api/predict { features }
    BE->>BE: One-Hot + Spalten ausrichten
    BE->>M: model.predict_proba(X)
    M-->>BE: churn_probability
    BE->>DB: INSERT Prediction
    BE-->>FE: { churn_probability, churn_prediction }
    FE-->>User: Metrik + Progress-Bar
```

---

## API-Endpunkte

| Methode | Pfad                              | Beschreibung                                                                  |
| ------- | --------------------------------- | ----------------------------------------------------------------------------- |
| `GET`   | `/api/health`                     | Liveness-Check, inkl. `model_loaded`-Flag.                                    |
| `GET`   | `/api/customers`                  | Liste der Kunden (`limit`, `offset` als Query-Parameter).                     |
| `GET`   | `/api/customers/{id}`             | Einzelner Kunde.                                                              |
| `GET`   | `/api/sample-customer`            | Beispiel-Feature-Vektor — `profile=random \| high_risk \| low_risk`.          |
| `POST`  | `/api/predict`                    | Vorhersage für einen ad-hoc übergebenen Feature-Vektor.                       |
| `POST`  | `/api/predict/{customer_id}`      | Vorhersage für einen bestehenden Kunden aus der DB.                           |
| `GET`   | `/api/predictions`                | Historie aller Vorhersagen (neueste zuerst).                                  |
| `POST`  | `/api/train`                      | Trigger fürs (Re-)Training des Modells; legt einen `ModelRun`-Eintrag an.     |
| `GET`   | `/api/model/info`                 | Aktuelle Modell-Metadaten (Accuracy, ROC-AUC, Spaltenliste, Trainingsdatum).  |

Interaktive Doku: <http://localhost:8000/docs>

---

## Komponenten-Walk-through

| Datei                                                 | Rolle                                                                                |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [`backend/generate_data.py`](backend/generate_data.py) | Erzeugt `data/customers.csv` (~5 000 Zeilen, Churn-Rate ~20 %).                      |
| [`backend/train_model.py`](backend/train_model.py)     | Lädt CSV → One-Hot → 80/20-Split → XGBoost → speichert `model.pkl` (Modell + Spalten). |
| [`backend/main.py`](backend/main.py)                   | FastAPI-App mit `lifespan`-Hook: seedet Kunden, lädt Modell, registriert Routen.     |
| [`backend/models.py`](backend/models.py)               | SQLAlchemy: `Customer`, `Prediction`, `ModelRun`.                                    |
| [`backend/schemas.py`](backend/schemas.py)             | Pydantic: `CustomerOut`, `CustomerFeatures`, `PredictionRequest`, `PredictionOut`, `SampleCustomer`. |
| [`backend/database.py`](backend/database.py)           | Engine, `SessionLocal`, `get_db()`.                                                  |
| [`frontend/app.py`](frontend/app.py)                   | Streamlit-UI: Tabs **Kunden**, **Vorhersage**, **Historie**.                         |

---

## Setup

```bash
cd POC3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Starten

```bash
# (optional, läuft beim 1. Backend-Start sonst automatisch)
python backend/generate_data.py

# (optional, kann auch später per POST /api/train ausgelöst werden)
python backend/train_model.py

# Zwei Terminals:
uvicorn backend.main:app --reload          # http://localhost:8000
streamlit run frontend/app.py              # http://localhost:8501
```

Beim ersten Backend-Start passiert (Lifespan-Hook):

1. `data/customers.csv` wird erzeugt, falls sie fehlt.
2. Kunden werden in die SQLite-Tabelle importiert (falls leer).
3. `backend/model.pkl` wird in Memory geladen, falls vorhanden.

> Wenn das Modell noch nicht trainiert wurde, antwortet `/api/predict` mit
> **HTTP 503**. Lösung: einmal `POST /api/train` aufrufen oder vor dem Start
> `python backend/train_model.py` ausführen.

---

## Testplan & erwartetes Verhalten

| Schritt | Aktion                                                              | Erwartetes Verhalten                                                                                          |
| ------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 1       | Backend starten                                                     | Logs: *„Imported N customers …"* und *„Loaded model from …"* (falls vorab trainiert).                         |
| 2       | `curl http://localhost:8000/api/health`                             | `{"status":"ok","model_loaded":true}`                                                                          |
| 3       | Frontend öffnen                                                     | Drei Tabs sichtbar: **Kunden · Vorhersage · Historie**.                                                       |
| 4       | Tab **Kunden**                                                      | Tabelle mit Kunden, Filter nach `contract_type` funktioniert.                                                 |
| 5       | Tab **Vorhersage** → **Beispielkunde laden** mit `profile=high_risk` | Formular wird mit Hochrisiko-Werten befüllt.                                                                  |
| 6       | **Predict** klicken                                                 | Metriken **Churn-Wahrscheinlichkeit** (z. B. > 70 %) und **Vorhersage = Churn** mit Progress-Bar.             |
| 7       | „Vorhandenen Kunden wählen" → **Vorhersage für gewählten Kunden**   | Liefert `PredictionOut` mit `customer_id`, gespeichert in `predictions`-Tabelle.                              |
| 8       | Tab **Historie**                                                    | Liste der letzten Predictions (neueste zuerst).                                                               |
| 9       | `POST /api/train` aufrufen                                          | Antwortet mit `accuracy` und `roc_auc` (typ. ~0.85 / ~0.90 für diesen Datensatz). Neuer `ModelRun`-Eintrag.    |

---

## 📋 Der exakte Copilot-Prompt

> Im Copilot Agent Mode in einen leeren Ordner pasten — die vier Blöcke
> nacheinander.

### 1. Daten-Generator

```text
Erstelle backend/generate_data.py: erzeugt mit numpy einen realistischen
synthetischen Churn-Datensatz mit ca. 5000 Zeilen
(Felder: id, age, tenure_months, monthly_charges, contract_type,
payment_method, support_calls, churn) und speichert ihn als
data/customers.csv. Churn-Rate ca. 20 %, Features sollen plausibel mit
churn korrelieren.
```

### 2. Modelltraining

```text
Erstelle backend/train_model.py: ruft generate_data.py auf, falls
data/customers.csv fehlt; liest die CSV, One-Hot-kodiert contract_type
und payment_method, trainiert einen xgboost.XGBClassifier (stratifizierter
80/20-Split), gibt Accuracy und ROC-AUC aus und speichert Modell +
Spaltenliste nach backend/model.pkl (joblib).
```

### 3. Backend (FastAPI)

```text
Erstelle backend/main.py mit FastAPI: Modelle Customer, Prediction,
ModelRun (SQLAlchemy). Endpunkte: GET /api/customers,
GET /api/customers/{id}, POST /api/predict,
POST /api/predict/{customer_id}, POST /api/train, GET /api/model/info,
GET /api/predictions.

Bei App-Start: wenn customers-Tabelle leer ist, Daten aus
data/customers.csv importieren (und generate_data.py ausführen, falls
die Datei fehlt) — so sind sofort Beispielkunden abrufbar, ohne dass
irgendetwas hochgeladen wurde.

Zusätzlicher Endpunkt GET /api/sample-customer: liefert einen zufälligen
Beispiel-Feature-Vektor (z. B. einen echten Kunden oder typische
"high-risk"/"low-risk"-Profile) — damit das Frontend die Prediction testen
kann.

CORS für http://localhost:8501. Pydantic-Schemas nutzen.
```

### 4. Frontend (Streamlit)

```text
Erstelle frontend/app.py (Streamlit) mit drei Tabs:

Tab "Kunden": Tabelle aus /api/customers mit Filter nach contract_type.

Tab "Vorhersage": Formular mit allen Features (sinnvolle Defaults) plus
Button "Beispielkunde laden" (ruft GET /api/sample-customer und befüllt
das Formular) sowie Selectbox "Vorhandenen Kunden wählen" (nutzt
POST /api/predict/{id}). Button "Predict" ruft /api/predict und zeigt
Wahrscheinlichkeit als Metrik und Progress-Bar.

Tab "Historie": zeigt /api/predictions.
```

---

## Extension Ideas

- 📈 **Feature-Importance** im Frontend anzeigen (XGBoost `feature_importances_`).
- 🤖 **Modell-Vergleich**: zwei Modelle (z. B. LogisticRegression vs. XGBoost)
  parallel trainieren und im UI zur Auswahl stellen.
- 🧮 **Batch-Predict**: CSV hochladen → Vorhersagen für alle Zeilen.
- 🪪 **Auth**: API-Key-Header für `/api/predict` und `/api/train`.
- 🧊 **Background-Training** mit `BackgroundTasks` (Frontend pollt Status).
- 🔍 **Erklärbarkeit**: SHAP-Werte für eine einzelne Vorhersage berechnen
  und als Wasserfall-Plot zeigen.
- 📊 **Drift-Monitoring**: Verteilung neuer Predictions mit Trainings-Verteilung
  vergleichen.

---

## Projektstruktur

```text
POC3/
├── README.md                       ← ihr seid hier
├── requirements.txt
│
├── backend/
│   ├── __init__.py
│   ├── main.py                     ← FastAPI + Lifespan
│   ├── models.py                   ← SQLAlchemy: Customer, Prediction, ModelRun
│   ├── schemas.py                  ← Pydantic
│   ├── database.py
│   ├── generate_data.py            ← synthetischer Churn-Datensatz
│   ├── train_model.py              ← Training + joblib-Persistenz
│   └── (model.pkl)                 ← entsteht beim Training (gitignored)
│
├── frontend/
│   └── app.py                      ← Streamlit, drei Tabs
│
└── data/
    └── customers.csv               ← entsteht beim 1. Start
```

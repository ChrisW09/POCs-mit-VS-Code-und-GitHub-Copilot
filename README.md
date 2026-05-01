# POCs

This repository contains three small proof-of-concept projects that build on
each other in complexity — from a single-file Streamlit app to a full
backend + frontend + ML stack.

| POC | Stack | Theme |
| --- | --- | --- |
| [POC1](POC1/) | Streamlit | CSV exploration in a single app |
| [POC2](POC2/) | FastAPI + SQLAlchemy + SQLite + Streamlit | CSV upload, persisted analyses, plot rendering |
| [POC3](POC3/) | FastAPI + SQLAlchemy + scikit-learn + Streamlit | Customer churn prediction with a trained model |

---

## POC1 – CSV Explorer (Streamlit)

A minimal Streamlit app for quick CSV exploration. Users can upload their own
CSV or load a built-in demo dataset (~500 rows, mixed numeric/categorical with
missing values). The app shows row/column counts, dtypes and missing values,
`df.describe()`, and per-column histograms and boxplots (matplotlib).

**Run:**

```bash
cd POC1
pip install -r requirements.txt
streamlit run app.py
```

See [POC1/README.md](POC1/README.md) for details.

---

## POC2 – Analytics Backend + Frontend

Splits the explorer idea into a proper client/server architecture:

- **Backend** (`backend/`): FastAPI + SQLAlchemy on SQLite. Endpoints for
  uploading CSV/TSV files, listing uploads, running an analysis (per-column
  stats + overview plot) and retrieving stats and the rendered PNG.
- **Frontend** (`frontend/`): Streamlit UI that talks to the backend over HTTP.
- Persists `Upload`, `AnalysisRun`, and `ColumnStat` records; seeds a demo
  dataset on first start.

**Run:**

```bash
cd POC2
pip install -r requirements.txt
uvicorn backend.main:app --reload          # http://localhost:8000
streamlit run frontend/app.py              # http://localhost:8501
```

See [POC2/README.md](POC2/README.md) for the full endpoint list.

---

## POC3 – Churn Prediction

End-to-end ML POC for predicting customer churn.

- **Data** (`backend/generate_data.py`): generates a synthetic customer
  dataset (`data/customers.csv`).
- **Training** (`backend/train_model.py`): trains a scikit-learn classifier
  on the customer features (age, tenure, monthly charges, contract type,
  payment method, support calls) and persists the model artifact.
- **Backend** (`backend/main.py`): FastAPI service exposing customer CRUD-style
  reads, single and batch churn predictions, training trigger, and model
  metadata. Customers are seeded into SQLite on first start.
- **Frontend** (`frontend/app.py`): Streamlit UI to browse customers, request
  predictions for an existing customer or an ad-hoc input, and inspect model
  info.

**Key endpoints:** `/api/health`, `/api/customers`, `/api/customers/{id}`,
`/api/sample-customer`, `/api/predict`, `/api/predict/{customer_id}`,
`/api/predictions`, `/api/train`, `/api/model/info`.

**Run:**

```bash
cd POC3
pip install -r requirements.txt
python backend/generate_data.py            # optional, also auto-runs on startup
python backend/train_model.py              # optional, or call POST /api/train later
uvicorn backend.main:app --reload          # http://localhost:8000
streamlit run frontend/app.py              # http://localhost:8501
```

---

## Conventions

- Each POC has its own `requirements.txt`; create a separate virtual
  environment per POC if you want full isolation.
- Backends listen on `http://localhost:8000`, Streamlit frontends on
  `http://localhost:8501` (CORS is configured accordingly in POC2/POC3).
- Generated artifacts (uploads, plots, SQLite DB, model files) live under
  each POC's `data/` directory and are safe to delete to reset state.

---

# Lehrkontext: Vibe Coding mit GitHub Copilot Agent Mode

Die drei POCs sind als Begleitmaterial zur Veranstaltung *„POCs mit VS Code
und GitHub Copilot"* (HSBI, Sommersemester 2026) entstanden. Sie wurden
end-to-end im **Agent Mode** von GitHub Copilot gebaut. Die folgenden
Abschnitte fassen die didaktischen Leitlinien und die verwendeten Prompts
zusammen, damit jede:r die POCs selbst nachbauen kann.

## Lernziele

Nach dem Durcharbeiten der drei POCs könnt ihr …

- mit GitHub Copilot Agent Mode autonom kleine Apps bauen,
- Streamlit-Apps für Datenanalyse selbstständig erstellen,
- eine Drei-Schichten-Architektur (Streamlit + FastAPI + SQLite) verstehen
  *und* umsetzen,
- eine ML-Anwendung end-to-end bauen: Daten → Modell → API → UI,
- KI-generierten Code lesen, prüfen und gezielt verbessern,
- einen sauberen Git-/GitHub-Workflow für POCs fahren.

**Bewusst nicht im Fokus:** Unit-Tests, CI/CD, Production-Deployment,
ML-Theorie, Frontend-Frameworks (React/Vue/…), Docker/Kubernetes.

## Was ist ein POC?

- Ein **lauffähiger Prototyp**, der eine konkrete Idee belegt.
- Klein, fokussiert, in *Stunden bis Tagen* baubar.
- Optimiert auf **Lerngeschwindigkeit**, nicht auf Robustheit.
- Bewusst weggelassen: Tests, Auth, Multi-User, Caching, Background-Jobs,
  Production-Deployment, optisches Polish.

> **Faustregel:** Lieber drei Dinge belegen als ein Ding perfektionieren.

## Der Vibe-Coding-Zyklus

1. **Idee** beschreiben →
2. **KI generiert** Code →
3. **Prüfen** & ausführen →
4. **Anpassung** beschreiben → (zurück zu 1)

Jede Iteration dauert Sekunden bis Minuten — das ist der Unterschied zum
klassischen Coding-Loop.

## Agent Mode vs. Ask Mode

| Eigenschaft | Ask Mode | Agent Mode |
| --- | :---: | :---: |
| Code-Vorschläge | ✓ | ✓ |
| Fragen beantworten | ✓ | ✓ |
| Dateien erstellen/bearbeiten | ✗ | ✓ |
| Terminal-Befehle ausführen | ✗ | ✓ |
| Mehrstufige Aufgaben | ✗ | ✓ |
| Selbstständig Fehler beheben | ✗ | ✓ |
| Kontext: ganzes Projekt | eingeschränkt | ✓ |

**Faustregel:** Ask für Fragen, Agent für Aufgaben.

## Prompt-Engineering für Code

Anatomie eines guten Code-Prompts — fünf Bausteine:

1. **Stack explizit nennen** — z. B. „FastAPI + SQLAlchemy + SQLite".
2. **Dateien & Ordner vorgeben** — `backend/main.py`, `frontend/app.py`.
3. **Datenmodell & Endpunkte konkret** — Tabellen mit Spalten, REST-Routen
   mit Methoden.
4. **Demo-Daten einfordern** — `sample_data.py`, `/api/sample`.
5. **Randbedingungen** — CORS, Ports, Pydantic, erlaubte Bibliotheken.

> Schlechte Prompts produzieren *generischen* Code. Gute Prompts produzieren
> *euren* Code.

**Vager Prompt** (führt zu Generischem):

> Bau mir eine App, die CSVs analysieren kann und ein bisschen ML macht.

**Spezifischer Prompt** (führt zu *eurem* Code):

> Erstelle `backend/` mit FastAPI + SQLAlchemy + SQLite. Modelle: Upload,
> AnalysisRun, ColumnStat. Endpunkte: `POST /api/upload`, `GET /api/uploads`,
> `POST /api/analyze/{id}`. CORS für `http://localhost:8501`.
> Pydantic-Schemas. Demo-Daten via `sample_data.py`.

## Git/GitHub-Workflow: GitHub zuerst

1. **GitHub-Repo** online anlegen (mit `README`, `.gitignore`, Lizenz).
2. **Lokal klonen** (`git clone`).
3. **VS Code** öffnen.
4. **Dateien** anlegen.
5. **Commit & Push** — regelmäßig nach jeder funktionierenden Änderung.

**Warum so herum?** Remote ist von Anfang an verknüpft, kein nachträgliches
`git remote add`. Kollaboration, Issues und Branches sind ab Sekunde 1
einsatzbereit.

> **Goldene Regel:** Nach jeder funktionierenden Änderung committen.

### `.gitignore` — was *nicht* ins Repo gehört

```gitignore
.venv/
__pycache__/
*.db
*.pkl
.env
*.key
```

- `.venv/`, `__pycache__/` — lokal/maschinenspezifisch
- `*.db`, `*.pkl` — generiert beim Ausführen
- `.env`, `*.key` — Secrets (einmal gepusht = öffentlich)

## Fallstricke & Sicherheit

Top-Fallstricke beim Vibe Coding:

1. **Geheimnisse im Repo** — `.env`, API-Keys gepusht → *sofort rotieren*.
2. **Fehlende `.gitignore`** — `.venv/`, `__pycache__/`, `*.db` fehlen.
3. **Falsche Python-Umgebung** — Conda vs. venv vs. System-Python.
4. **Port-Konflikte** — 8000 / 8501 bereits belegt.
5. **CORS-Fehler** — Streamlit (8501) ruft FastAPI (8000), Header fehlt.
6. **Riesige Commits** ohne Botschaft — nichts mehr nachvollziehbar.

> **Niemals ins Repo:** API-Keys, Tokens, Passwörter, `.env`-Dateien mit
> echten Werten, Datenbanken mit personenbezogenen Daten. Wenn doch
> passiert: Schlüssel sofort rotieren — Löschen aus Git reicht *nicht*.

---

# Die verwendeten Agent-Prompts

Die folgenden Prompts wurden im Copilot Agent Mode verwendet, um die drei
POCs zu erzeugen. Sie sind hier dokumentiert, damit ihr sie als Vorlage für
eigene POCs nutzen könnt.

## POC 1 — Streamlit CSV-Explorer

```
Erstelle eine einfache Streamlit-App app.py mit zwei Datenquellen:
(a) st.file_uploader für eine eigene CSV,
(b) Button "Beispieldaten laden", der einen integrierten Demo-Datensatz
ohne Upload nutzt.

Erzeuge dazu ein Hilfsmodul sample_data.py mit einer Funktion
get_sample_df(), die per numpy/pandas einen realistischen Beispieldatensatz
(ca. 500 Zeilen, gemischt numerisch/kategorisch, mit einigen fehlenden
Werten) erzeugt; speichere ihn zusätzlich einmalig als data/sample.csv.

Zeige nach Auswahl der Quelle:
(1) Zeilen-/Spaltenanzahl,
(2) Datentypen und fehlende Werte je Spalte,
(3) df.describe() als Tabelle,
(4) für jede numerische Spalte Histogramm und Boxplot mit matplotlib.

Lege auch requirements.txt (streamlit, pandas, numpy, matplotlib),
.gitignore und ein kurzes README an.
```

## POC 2 — FastAPI + SQLite Backend

```
Erstelle backend/ mit FastAPI + SQLAlchemy + SQLite.
Modelle: Upload, AnalysisRun, ColumnStat.
Endpunkte: POST /api/upload, GET /api/uploads, POST /api/analyze/{id},
GET /api/stats/{id}, GET /api/plots/{id}.

Lege zusätzlich ein Modul sample_data.py an, das mit numpy/pandas einen
realistischen Demo-Datensatz (ca. 500 Zeilen, gemischt numerisch/
kategorisch) erzeugt. Beim App-Start prüfen: wenn noch kein Upload
existiert, diesen automatisch als "sample.csv" in die Upload-Tabelle seeden.

Zusätzlicher Endpunkt POST /api/sample — legt den Beispiel-Upload an
(oder liefert den bestehenden) und gibt dessen upload_id zurück, damit
das Frontend direkt testen kann.

Pydantic-Schemas nutzen, CORS für http://localhost:8501.
```

## POC 2 — Streamlit Frontend

```
Erstelle frontend/app.py (Streamlit): Datenquelle per st.radio wählbar —
"Eigene CSV" (st.file_uploader + POST /api/upload) oder "Beispieldaten"
(Button "Beispieldaten laden" ruft POST /api/sample). Die zurückgegebene
upload_id wird jeweils in st.session_state gespeichert.

Button "Analyse starten" ruft /api/analyze, Ergebnisse kommen über
/api/stats und /api/plots.
```

## POC 3 — Daten-Generator

```
Erstelle backend/generate_data.py: erzeugt mit numpy einen realistischen
synthetischen Churn-Datensatz mit ca. 5000 Zeilen
(Felder: id, age, tenure_months, monthly_charges, contract_type,
payment_method, support_calls, churn) und speichert ihn als
data/customers.csv. Churn-Rate ca. 20 %, Features sollen plausibel mit
churn korrelieren.
```

## POC 3 — Modelltraining

```
Erstelle backend/train_model.py: ruft generate_data.py auf, falls
data/customers.csv fehlt; liest die CSV, One-Hot-kodiert contract_type
und payment_method, trainiert einen xgboost.XGBClassifier (stratifizierter
80/20-Split), gibt Accuracy und ROC-AUC aus und speichert Modell +
Spaltenliste nach backend/model.pkl (joblib).
```

## POC 3 — Backend (FastAPI)

```
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

## POC 3 — Frontend (Streamlit)

```
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

## Take-aways

1. **POC = Lerngeschwindigkeit > Robustheit.** Drei kleine Apps schlagen
   ein perfektes Projekt.
2. **Vibe Coding ist ein Loop.** Sekunden pro Iteration, nicht Stunden.
3. **Prompt-Qualität = Code-Qualität.** Stack, Dateien, Schemas, Demo-Pfad
   in jeden Prompt.
4. **KI-Code immer lesen, ausführen, gegen Halluzinationen prüfen.**
5. **Architektur ist „wer ruft wen wie auf"** — nicht der Use Case.
6. **ML-App = Drei-Schichten + Modell-Schicht.** Mehr braucht's selten.
7. **Secrets niemals in Git.** `.gitignore` vor dem ersten Commit.

## Ressourcen

- Streamlit: <https://docs.streamlit.io>
- FastAPI: <https://fastapi.tiangolo.com>
- SQLAlchemy: <https://docs.sqlalchemy.org>
- XGBoost: <https://xgboost.readthedocs.io>
- GitHub Copilot: <https://docs.github.com/copilot>
- Git (deutsch): <https://git-scm.com/book/de>

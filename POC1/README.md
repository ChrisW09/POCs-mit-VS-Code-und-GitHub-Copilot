# POC1 – CSV Explorer (Streamlit)

Eine kleine Streamlit-App zur schnellen Exploration von CSV-Daten.

## Features

- **Zwei Datenquellen**
  - Upload einer eigenen CSV-Datei (`st.file_uploader`)
  - Button **„Beispieldaten laden"** – nutzt einen eingebauten Demo-Datensatz
    (~500 Zeilen, gemischt numerisch/kategorisch, mit fehlenden Werten)
- Anzeige von:
  1. Zeilen- und Spaltenanzahl
  2. Datentypen und fehlende Werte je Spalte
  3. `df.describe()` als Tabelle
  4. Histogramm und Boxplot (matplotlib) für jede numerische Spalte

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Starten

```bash
streamlit run app.py
```

## Projektstruktur

```
POC1/
├── app.py              # Streamlit-App
├── sample_data.py      # Erzeugt den Beispieldatensatz (get_sample_df)
├── data/
│   └── sample.csv      # Wird beim ersten Aufruf von get_sample_df() erzeugt
├── requirements.txt
└── README.md
```

## Beispieldaten erzeugen (optional, ohne App)

```bash
python sample_data.py
```

Erstellt `data/sample.csv` (falls noch nicht vorhanden).

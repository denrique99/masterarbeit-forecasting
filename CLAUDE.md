# Masterarbeit – XGBoost Revenue Forecasting (TU Berlin)

## Projektkontext

Hybrider Forecasting-Prototyp fuer ein industrielles B2B-Unternehmen (Kompressoren/Tools).

Maerkte: DE und US. Simulated current date: 31.12.2025.

Kernthese: Top-Down-Managementziele ohne Datenbasis fuehren zu Overplanning.

## Forecasting-Schichten

- B1: Bestaetigter Auftragsbestand + gewichtete Quotation Pipeline (bekannte Nachfrage)
- B2: Neukunden-Schaetzungen
- B3: XGBoost-Forecast fuer unbekannte Opportunities bei Bestandskunden
- Formel: Ergebnis_B3 = B3_gesamt minus (B1 + B2)

## Stack

- Python 3.13, XGBoost, pandas, scikit-learn, SHAP, statsmodels, fredapi
- SAP Analytics Cloud (SAC Planning) als Praesentationsschicht
- SAP-Tabellen: VBRP/VBRK (Rechnungen), VBAP (Vertriebsauftraege)
- Makro DE: Destatis Auftragseingangsindex Inland (Tabelle 42151-0004, DE-010)
- Makro DE: Destatis Produktionsindex (Tabelle 42153-0001, DE-011)
- Makro US: FRED DGORDER und INDPRO

## Projektstruktur

- notebooks/    - Jupyter Notebooks (EDA, XGBoost, SHAP, CCF, ADF)
- data/raw/     - Rohdaten (VBRP-Export, VBAP-Export, FRED, Destatis) – nicht im Git
- data/processed/ - Bereinigte Feature-Matrizen
- models/       - Trainierte XGBoost-Modelle und Scaler (.pkl) – nicht im Git
- .claude/      - Claude Code Konfiguration

## Coding-Konventionen

- Kommentare auf Deutsch
- Variablennamen auf Englisch
- Keine hardcodierten API-Keys, immer .env verwenden
- pip install immer mit --break-system-packages
- Notebooks numerisch praefix: 01_, 02_, 03_ etc.

## Wichtige Designentscheidungen

- Leaf-Node-Buchung in Produkthierarchie (kein Double-Counting)
- XGBoost ist nicht skalensensitiv (DGORDER bleibt in Millionen-Denomination)
- StandardScaler nur fuer SHAP-Visualisierung
- Destatis p-Werte (provisorisch) als Modelllimitation dokumentieren
- Inland-Spalte fuer DE-010 (Inlandsauftraege als direkter Nachfrage-Proxy)

## Datenquellen

### DGE_DE_DGORDER.csv
- Quelle: Destatis, Tabelle 42151-0004 (Auftragseingangsindex Inland, DE-010)
- Granularitaet: Monatlich, 2018-01 bis 2026-01 (~96 Zeilen)
- Schluessel-Spalten: `DateId` (YYYY-MM), `X13_JDemetra__kalender__und_saisonbereinigt` (saisonbereinigter Index)
- Einheit: Index (kein fester Basiswert angegeben), Wertebereich ca. 85–110

### DGE_DE_INDPRO.csv
- Quelle: Destatis, Tabelle 42153-0001 (Produktionsindex, DE-011)
- Granularitaet: Monatlich, 2018-01 bis 2026-01 (~96 Zeilen)
- Schluessel-Spalten: `DateId` (YYYY-MM), `X13_JDemetra___kalender__und_saisonbereinigt` (saisonbereinigter Index)
- Einheit: Index, Wertebereich ca. 85–115

### DGE_US_DGORDER.csv
- Quelle: FRED, Series DGORDER (Manufacturers' Durable Goods Orders)
- Granularitaet: Monatlich, 1992-02 bis 2025-12 (~406 Zeilen)
- Schluessel-Spalten: `observation_dateDATE` (YYYY-MM-DD), `DGORDER` (Bestellvolumen)
- Einheit: USD Millionen (nicht skalieren – XGBoost ist skalensensitivitaetsfrei)

### DGE_US_INDPRO.csv
- Quelle: FRED, Series INDPRO (Industrial Production Index)
- Granularitaet: Monatlich, 1919-01 bis 2025-12 (~1284 Zeilen)
- Schluessel-Spalten: `observation_dateDATE` (YYYY-MM-DD), `INDPRO`
- Einheit: Index (2017=100), Wertebereich ca. 4–110 (historisch sehr lang)

### DGE_Revenue_Planning_Actuals_Net_Value_US.xlsx
- Quelle: SAP Analytics Cloud (SAC) Export
- Sheet: DGE_Revenue_Planning_Actuals_N (aktive Daten), Appendix
- Granularitaet: Monatlich, 2022-10 bis 2025-12 (78 Zeilen = 2 Produkte x 39 Monate)
- Spalten: `Date` (YYYYMM), `Country` (US), `Product` (Accessories / Compressors), `Measures` (Net Value), Wert (USD)
- Zielgröße fuer US-Forecast

### DGE_Revenue_Planning_Actuals_Quantity_US.xlsx
- Quelle: SAP Analytics Cloud (SAC) Export
- Sheet: DGE_Revenue_Planning_Actuals_Q (aktive Daten), Appendix
- Granularitaet: Monatlich, 2022-10 bis 2025-12 (78 Zeilen = 2 Produkte x 39 Monate)
- Spalten: `Date` (YYYYMM), `Country` (US), `Product` (Accessories / Compressors), `Measures` (Order Quantity), Wert (Stueck)
- Komplementaere Mengensicht zum Net Value

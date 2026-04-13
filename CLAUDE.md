# Masterarbeit – XGBoost Revenue Forecasting (TU Berlin)

## Projektkontext

Hybrider Forecasting-Prototyp fuer ein industrielles B2B-Unternehmen (Kompressoren/Tools).

Maerkte: DE und US. Simulated current date: 31.12.2025.

Kernthese: Top-Down-Managementziele ohne Datenbasis fuehren zu Overplanning.

## Forecasting-Schichten

- B1: Bestaetigter Auftragsbestand + gewichtete Quotation Pipeline (bekannte Nachfrage)
- B2: Neukunden-Schaetzungen
- B3 (Kernbaustein): XGBoost-Marktpotenzial-Forecast fuer den US-Defense-Sektor
  - Fragestellung: Wie gross ist das adressierbare Marktvolumen in einem neuen Segment?
  - Formel: Segment_Forecast = ML_Marktvolumen_ADEFNO × Management_Marktanteil
  - ML prognostiziert das externe Marktvolumen; der Marktanteil ist Management-Input in SAC
- B3-Referenz (ML-Plausibilitaetscheck, optional): XGBoost-Forecast auf historischen
  Compressors/US-Umsatzdaten – dient dem Vertrieb als datenstuetzter Benchmark,
  nicht als eigenstaendiger Building Block
  - Formel (alt): Ergebnis_B3 = B3_gesamt minus (B1 + B2)

Hintergrund Nomenklatur: Im Stakeholder-Meeting vom 10.04.2026 wurde die Neuausrichtung
beschlossen. ML soll dort eingesetzt werden, wo der Mensch einen blinden Fleck hat
(neue Maerkte), nicht dort, wo Vertriebsdaten bereits vorliegen.

## Stack

- Python 3.13, XGBoost, pandas, scikit-learn, SHAP, statsmodels, fredapi
- SAP Analytics Cloud (SAC Planning) als Praesentationsschicht
- SAP-Tabellen: VBRP/VBRK (Rechnungen), VBAP (Vertriebsauftraege)
- Makro DE: Destatis Auftragseingangsindex Inland (Tabelle 42151-0004, DE-010)
- Makro DE: Destatis Produktionsindex (Tabelle 42153-0001, DE-011)
- Makro US (B3-Referenz): FRED DGORDER und INDPRO
- Makro US (B3 Kernbaustein): FRED ADEFNO, IPB52300S und FDEFX

## Projektstruktur

b3a_compressors/   - B3-Referenz: XGBoost auf Compressors/US-Umsatzdaten (alter Ansatz)
  notebooks/       - Jupyter Notebooks 01-06 (EDA, Macro, Features, XGBoost, SHAP, Forecast)
  data/raw/        - Rohdaten (VBRP-Export, FRED, Destatis) – nicht im Git
  data/processed/  - Bereinigte Feature-Matrizen
  models/          - Trainierte XGBoost-Modelle (.pkl) – nicht im Git
  api/             - Flask/FastAPI SAC write-back

b3b_defense/       - B3 Kernbaustein: XGBoost Defense-Marktpotenzial-Forecast
  notebooks/       - Jupyter Notebooks 01-06 (EDA, Macro, Features, XGBoost, SHAP, Forecast)
  data/raw/        - Rohdaten (FRED ADEFNO, IPB52300S) – nicht im Git
  data/processed/  - defense_feature_matrix.csv, defense_forecast_2026_sac.csv
  models/          - xgboost_defense_market.pkl – nicht im Git
  api/             - Flask/FastAPI SAC write-back (Marktvolumen + Marktanteil-Parameter)

.claude/           - Claude Code Konfiguration

## Coding-Konventionen

- Kommentare auf Englisch
- Variablennamen auf Englisch
- Keine hardcodierten API-Keys, immer .env verwenden (FRED_API_KEY)
- pip install immer mit --break-system-packages
- Notebooks numerisch praefix: 01_, 02_, 03_ etc.

## Wichtige Designentscheidungen

- Leaf-Node-Buchung in Produkthierarchie (kein Double-Counting)
- XGBoost ist nicht skalensensitiv (ADEFNO und DGORDER bleiben in Millionen-Denomination)
- StandardScaler nur fuer SHAP-Visualisierung
- Destatis p-Werte (provisorisch) als Modelllimitation dokumentieren
- Inland-Spalte fuer DE-010 (Inlandsauftraege als direkter Nachfrage-Proxy)
- B3b Zielvariable ist ADEFNO absolut (kein Diff) – Marktvolumen muss interpretierbar bleiben
- Marktanteil wird nicht durch ML bestimmt, sondern als Management-Input in SAC parametrisiert
  (conservative 0.02% / realistic 0.05% / optimistic 0.1%)

## Datenquellen – b3a_compressors

### DGE_DE_DGORDER.csv
- Quelle: Destatis, Tabelle 42151-0004 (Auftragseingangsindex Inland, DE-010)
- Granularitaet: Monatlich, 2018-01 bis 2026-01 (~96 Zeilen)
- Schluessel-Spalten: `DateId` (YYYY-MM), `X13_JDemetra__kalender__und_saisonbereinigt`
- Einheit: Index, Wertebereich ca. 85-110

### DGE_DE_INDPRO.csv
- Quelle: Destatis, Tabelle 42153-0001 (Produktionsindex, DE-011)
- Granularitaet: Monatlich, 2018-01 bis 2026-01 (~96 Zeilen)
- Schluessel-Spalten: `DateId` (YYYY-MM), `X13_JDemetra___kalender__und_saisonbereinigt`
- Einheit: Index, Wertebereich ca. 85-115

### DGE_US_DGORDER.csv
- Quelle: FRED, Series DGORDER (Manufacturers' Durable Goods Orders)
- Granularitaet: Monatlich, 1992-02 bis 2025-12 (~406 Zeilen)
- Schluessel-Spalten: `observation_dateDATE` (YYYY-MM-DD), `DGORDER`
- Einheit: USD Millionen

### DGE_US_INDPRO.csv
- Quelle: FRED, Series INDPRO (Industrial Production Index)
- Granularitaet: Monatlich, 1919-01 bis 2025-12 (~1284 Zeilen)
- Schluessel-Spalten: `observation_dateDATE` (YYYY-MM-DD), `INDPRO`
- Einheit: Index (2017=100), Wertebereich ca. 4-110

### DGE_Revenue_Planning_Actuals_Net_Value_US.xlsx
- Quelle: SAP Analytics Cloud (SAC) Export
- Granularitaet: Monatlich, 2022-10 bis 2025-12 (78 Zeilen = 2 Produkte x 39 Monate)
- Spalten: `Date` (YYYYMM), `Country` (US), `Product` (Accessories / Compressors), Wert (USD)
- Zielgroesse fuer B3-Referenz Forecast

### DGE_Revenue_Planning_Actuals_Quantity_US.xlsx
- Quelle: SAP Analytics Cloud (SAC) Export
- Granularitaet: Monatlich, 2022-10 bis 2025-12 (78 Zeilen = 2 Produkte x 39 Monate)
- Spalten: `Date` (YYYYMM), `Country` (US), `Product`, Wert (Stueck)

## Datenquellen – b3b_defense

### ADEFNO.csv
- Quelle: FRED, Series ADEFNO (Manufacturers' New Orders: Defense Capital Goods)
- Granularitaet: Monatlich, ab 2000, saisonbereinigt
- Schluessel-Spalten: `observation_dateDATE` (YYYY-MM-DD), `ADEFNO`
- Einheit: USD Millionen
- Rolle: Zielvariable des B3-Modells (Marktvolumen Defense-Sektor)

### IPB52300S.csv
- Quelle: FRED, Series IPB52300S (Industrial Production: Defense and Space Equipment)
- Granularitaet: Monatlich, ab 2000, Index
- Schluessel-Spalten: `observation_dateDATE` (YYYY-MM-DD), `IPB52300S`
- Einheit: Index
- Rolle: Feature (Produktionskapazitaet Defense-Sektor)

### FDEFX.csv
- Quelle: FRED, Series FDEFX (Federal Government: National Defense Consumption
  Expenditures and Gross Investment)
- Granularitaet: Quartalsweise (quarterly), ab 2000, saisonbereinigt
- Schluessel-Spalten: `observation_dateDATE` (YYYY-MM-DD), `FDEFX`
- Einheit: USD Millionen (Milliarden in manchen FRED-Exports – vor Verwendung pruefen)
- Rolle: Feature (tatsaechlich geflossene Staatsausgaben Defense, nicht nur Bestellungen)
- Verarbeitung: forward-fill auf Monatsfrequenz in Notebook 02
- Begruendung: ADEFNO misst Bestellungsintention, FDEFX misst realisierte Ausgaben –
  unterschiedliche Messperspektive reduziert Kollinearitaet zwischen den Features

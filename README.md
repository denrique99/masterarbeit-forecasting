# XGBoost Revenue Forecasting – Masterarbeit TU Berlin

Hybrid forecasting prototype for an industrial B2B company (compressors/tools) in the US market.
The core thesis: top-down management targets without a data foundation lead to overplanning.
This repository provides two ML-backed building blocks (B3 and B3-Reference) as a data-driven benchmark.

## Building Blocks

| Baustein | Ordner | Beschreibung |
|----------|--------|--------------|
| **B3 – Defense Market Forecast** | `b3b_defense/` | XGBoost forecast of the US Defense Capital Goods market volume (FRED ADEFNO). Answers: *How large is the addressable market in a new segment?* The ML model predicts external market volume; market share is a management input in SAC. **Core building block.** |
| **B3-Reference – Compressors Revenue** | `b3a_compressors/` | XGBoost forecast on historical Compressors/US revenue data. Serves as a data-backed benchmark for sales — not a standalone planning input. **Optional plausibility check.** |

## Nomenklatur-Hinweis

The naming was revised in a stakeholder meeting on 10.04.2026:
- **B3** now refers exclusively to the Defense market potential model (`b3b_defense/`)
- **B3-Reference** refers to the older compressors revenue model (`b3a_compressors/`)

ML is applied where humans have a blind spot (new markets), not where sales data already exists.

## Setup

1. Place the three raw CSV files in `data/raw/` of the relevant subfolder (no API key required – notebooks read from disk).
2. Install dependencies (from the subfolder):
   ```
   pip install -r requirements.txt --break-system-packages
   ```
3. Run notebooks in order: `01_eda` → `02_macro_data` → `03_feature_engineering` → `04_xgboost_training` → `05_shap_analysis` → `06_forecast_explainability`

## Forecasting Architecture

```
B1  Confirmed order backlog + weighted quotation pipeline  (known demand, from SAP)
B2  New customer estimates                                 (sales estimates)
B3  Defense market potential × management market share     (this repo – b3b_defense/)
    B3-Reference: Compressors revenue benchmark            (this repo – b3a_compressors/)
```

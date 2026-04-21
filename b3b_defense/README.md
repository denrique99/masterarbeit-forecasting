# B3b – Defense Market Potential Forecast

XGBoost-based forecast of the **US Defense Capital Goods market volume** (FRED series FDEFX).

This is the **B3 core building block** of the hybrid forecasting system. Unlike the B3-Reference model
(b3a_compressors), which operates on historical company revenue data, this model addresses a market
where the company has no historical footprint — the US defense sector.

## Approach

- **Target variable:** FDEFX (Federal Defense Consumption Expenditures), in USD billions (SAAR) — realized expenditures, semantically consistent with B1/B2 invoice-based forecasts in SAC. Absolute level, not differenced, to preserve interpretability.
- **ML task:** Forecast the external market volume; market share is a management input in SAC

### Target Rationale

B1 and B2 forecast invoice-based revenue. For consistent aggregation in SAC Planning, all
building blocks must represent the same economic quantity. ADEFNO (ordering intent) was
therefore reclassified from target to leading feature with lags 1–24, allowing the model to
learn the order-to-bill conversion dynamics data-driven rather than assuming a fixed lead time.
The 24-month lag window is empirically motivated by the heterogeneous order-to-shipment lead
times in Defense Capital Goods: ~3–6 months for small arms and ammunition, ~6–12 months for
communications equipment, ~12–24 months for aircraft and missiles (consistent with AlixPartners
documentation of A&D supply chain lead times "up to two years").

## Notebooks

| # | Notebook | Description |
|---|----------|-------------|
| 01 | `01_eda.ipynb` | Exploratory data analysis: ADEFNO, IPB52300S & FDEFX time series, correlations, stationarity preview |
| 02 | `02_macro_data.ipynb` | Load raw CSVs, resample FDEFX to monthly (forward-fill), ADF tests, first differencing, save processed output |
| 03 | `03_feature_engineering.ipynb` | Build defense feature matrix (lags, rolling windows, calendar) |
| 04 | `04_xgboost_training.ipynb` | TimeSeriesSplit training, metrics (MAE/RMSE/sMAPE/WMAPE), model export |
| 05 | `05_shap_analysis.ipynb` | SHAP beeswarm, importance bar chart, waterfall for last observation |
| 06 | `06_forecast_explainability.ipynb` | Rolling 2026 forecast, market share scenarios, SAC CSV export |
| 07 | `07_llm_analysis.ipynb` | Claude-powered macroeconomic narrative: data-grounded interpretation of the 2026 forecast, KPI table, risk assessment |

## Data Sources

### Raw (data/raw/)

| File | Series | Frequency | Unit | Role |
|------|--------|-----------|------|------|
| `FDEFX.csv` | FRED FDEFX | **Quarterly** | USD billions (SAAR) | **Target variable** – realized federal defense expenditures |
| `ADEFNO.csv` | FRED ADEFNO | Monthly | USD millions | Feature – leading indicator (lags 1–24), defense procurement orders |
| `IPB52300S.csv` | FRED IPB52300S | Monthly | Index | Feature – coincident indicator (lags 1–12), defense industrial production capacity |

**Why three series?** They measure different stages of the same economic pipeline:
FDEFX tracks *realized government spending* (target), ADEFNO captures *ordering intent*
(leading feature with lags 1–24 covering the full order-to-shipment spectrum), and
IPB52300S reflects *production capacity* (coincident feature). The complementary
perspectives reduce collinearity between features.

FDEFX is forward-filled to monthly frequency in Notebook 02. This disaggregation is a
deliberate design choice and documented as a model limitation — the effective information
density remains quarterly.

### Processed (data/processed/)

| File | Description |
|------|-------------|
| `macro_features_defense.csv` | Joined monthly series with levels and first differences |
| `defense_feature_matrix.csv` | Final feature matrix for XGBoost training (lags, rolling windows, calendar) |
| `defense_forecast_2026_sac.csv` | SAC export: 12 rows (Jan–Dec 2026), FDEFX SAAR in full USD (billions × 1e9) |
| `defense_forecast_2026_drivers_sac.csv` | SAC export: long-format SHAP driver breakdown (408 rows = 12 months × 34 entries), SHAP values in USD billions |
| `lllm_defense_analysis_2026.md` | LLM-generated macroeconomic narrative (NB07): forecast interpretation, KPI table, risk assessment |

## Setup

1. Place the three raw CSV files in `data/raw/` (no API key required – notebooks read from disk).
2. Install dependencies:
   ```
   pip install -r requirements.txt --break-system-packages
   ```
3. Run notebooks in order: 01 → 02 → 03 → 04 → 05 → 06 → 07

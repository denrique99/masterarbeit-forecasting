# B3b – Defense Market Potential Forecast

XGBoost-based forecast of the **US Defense Capital Goods market volume** (FRED series ADEFNO).

This is the **B3 core building block** of the hybrid forecasting system. Unlike the B3-Reference model
(b3a_compressors), which operates on historical company revenue data, this model addresses a market
where the company has no historical footprint — the US defense sector.

## Approach

- **Target variable:** ADEFNO (Manufacturers' New Orders: Defense Capital Goods), in USD millions — absolute level, not differenced, to keep the result interpretable
- **ML task:** Forecast the external market volume; market share is a management input in SAC
- **Formula:** `Segment_Forecast = ML_Market_Volume_ADEFNO × Management_Market_Share`
- **Market share scenarios (SAC parameters):** Conservative 0.02% / Realistic 0.05% / Optimistic 0.10%

## Notebooks

| # | Notebook | Description |
|---|----------|-------------|
| 01 | `01_eda.ipynb` | Exploratory data analysis: ADEFNO, IPB52300S & FDEFX time series, correlations, stationarity preview |
| 02 | `02_macro_data.ipynb` | Load raw CSVs, resample FDEFX to monthly (forward-fill), ADF tests, first differencing, save processed output |
| 03 | `03_feature_engineering.ipynb` | Build defense feature matrix (lags, rolling windows, calendar) |
| 04 | `04_xgboost_training.ipynb` | TimeSeriesSplit training, metrics (MAE/RMSE/sMAPE/WMAPE), model export |
| 05 | `05_shap_analysis.ipynb` | SHAP beeswarm, importance bar chart, waterfall for last observation |
| 06 | `06_forecast_explainability.ipynb` | Rolling 2026 forecast, market share scenarios, SAC CSV export |

## Data Sources

### Raw (data/raw/)

| File | Series | Frequency | Unit | Role |
|------|--------|-----------|------|------|
| `ADEFNO.csv` | FRED ADEFNO | Monthly | USD millions | **Target variable** – defense procurement orders |
| `IPB52300S.csv` | FRED IPB52300S | Monthly | Index | Feature – defense industrial production capacity |
| `FDEFX.csv` | FRED FDEFX | **Quarterly** | USD millions | Feature – realized federal defense expenditures |

**Why three series?** They measure different stages of the same economic pipeline:
ADEFNO captures *ordering intent*, IPB52300S reflects *production capacity*, and FDEFX tracks
*realized government spending*. The complementary perspectives reduce collinearity between features.
FDEFX is forward-filled to monthly frequency in Notebook 02.

### Processed (data/processed/)

| File | Description |
|------|-------------|
| `macro_features_defense.csv` | Joined monthly series with levels and first differences |
| `defense_feature_matrix.csv` | Final feature matrix for XGBoost training (lags, rolling windows, calendar) |
| `defense_forecast_2026_sac.csv` | SAC export: 36 rows (12 months × 3 scenarios), ready for import |

## Setup

1. Place the three raw CSV files in `data/raw/` (no API key required – notebooks read from disk).
2. Install dependencies:
   ```
   pip install -r requirements.txt --break-system-packages
   ```
3. Run notebooks in order: 01 → 02 → 03 → 04 → 05 → 06

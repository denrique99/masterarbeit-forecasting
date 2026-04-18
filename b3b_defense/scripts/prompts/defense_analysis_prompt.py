"""
Prompt templates for the B3b Defense LLM macroeconomic analysis.

All numerical placeholders are injected by run_defense_analysis.py from
verified CSV sources. The LLM is explicitly forbidden from adding numbers
not present in the prompt.
"""

SYSTEM_PROMPT = """\
You are a senior macroeconomic analyst specialising in US defense procurement markets.
Write for a corporate controller or enterprise planner who needs to defend forecast
assumptions in a management review. Prioritize verifiable sourcing over narrative
flourish. Brevity is a feature.\
"""


def build_user_prompt(
    # --- ADEFNO historical context ---
    adefno_last_month: str,
    adefno_last_value_mn: str,
    adefno_12m_avg_mn: str,
    adefno_range_min_mn: str,
    adefno_range_min_date: str,
    adefno_range_max_mn: str,
    adefno_range_max_date: str,
    # --- FDEFX historical context ---
    fdefx_last_quarter: str,
    fdefx_last_value_bn: str,
    fdefx_prior_value_bn: str,
    fdefx_yoy_pct: str,
    # --- IPB52300S historical context ---
    ipb_last_month: str,
    ipb_last_value: str,
    ipb_12m_start_value: str,
    ipb_12m_change: str,
    ipb_trend_direction: str,
    # --- Forecast ---
    forecast_table: str,
    annual_total_bn: str,
    base_value_mn: str,
    # --- SHAP ---
    importance_table: str,
    monthly_top3_table: str,
) -> str:
    return f"""\
## Sourcing Rules — Read Before Answering

Use **only** the numerical values explicitly provided in this prompt.
Do not introduce any statistics, percentages, ratios, or historical figures from memory.

For every factual claim that is not directly derivable from the data tables below,
cite an **official primary source** with a specific, verifiable URL from this list:
  - FRED:            https://fred.stlouisfed.org
  - BEA:             https://www.bea.gov
  - US Census:       https://www.census.gov
  - Federal Reserve: https://www.federalreserve.gov
  - CBO:             https://www.cbo.gov
  - DoD Comptroller: https://comptroller.defense.gov

No secondary sources. No industry association claims without a direct primary URL.

If you cannot support a claim with either (a) the data provided or (b) an official
primary source with a verifiable URL, **omit the claim entirely**.

Flag any scenario probabilities, thresholds, or ranges as **illustrative** unless
they are derived from a cited primary source.

---

## Company Context

An industrial B2B manufacturer (compressors and pneumatic tools, Germany-based) is
launching new products in the US defense segment in 2026. The company has zero prior
defense revenue. Revenue targets are set in SAP Analytics Cloud (SAC) using a
management-defined market share assumption applied to the ML-forecasted market volume
below. The market share decision is made in SAC — this analysis covers market volume
and macro conditions only.

---

## Verified Input Data

### 1. ADEFNO — US Manufacturers' New Orders: Defense Capital Goods
Source: FRED series ADEFNO (https://fred.stlouisfed.org/series/ADEFNO)
Unit: USD millions, seasonally adjusted

Last observed value:   {adefno_last_month}: {adefno_last_value_mn} USD mn
12-month average 2025: {adefno_12m_avg_mn} USD mn  (Jan–Dec 2025, from CSV)
2020–2025 range:       {adefno_range_min_mn} USD mn ({adefno_range_min_date}) to {adefno_range_max_mn} USD mn ({adefno_range_max_date})

### 2. FDEFX — Federal Government: National Defense Consumption Expenditures & Gross Investment
Source: FRED series FDEFX (https://fred.stlouisfed.org/series/FDEFX)
Unit: USD billions, seasonally adjusted annual rate

Last observed value:    {fdefx_last_quarter}: {fdefx_last_value_bn} USD bn
Prior-year same quarter: {fdefx_prior_value_bn} USD bn
YoY change:             {fdefx_yoy_pct}

### 3. IPB52300S — Industrial Production: Defense and Space Equipment
Source: FRED series IPB52300S (https://fred.stlouisfed.org/series/IPB52300S)
Unit: Index (2017=100), seasonally adjusted

Last observed value:  {ipb_last_month}: {ipb_last_value}
12-month trend 2025:  Jan 2025 = {ipb_12m_start_value} → Dec 2025 = {ipb_last_value} (change: {ipb_12m_change} index pts, {ipb_trend_direction})

### 4. XGBoost Forecast — ADEFNO Market Volume 2026
Model: rolling one-step-ahead XGBoost, trained on FRED macro data 2000–2025.
Macro features (IPB52300S, FDEFX) are carried forward at last known values (Dec 2025 / Q4 2025).
ADEFNO autoregressive features are updated each step from the prior predicted value.

Monthly forecast (USD mn):
{forecast_table}

Annual total 2026: {annual_total_bn} USD bn
Model baseline (SHAP expected value): {base_value_mn} USD mn / month

### 5. SHAP Driver Breakdown
Unit: USD millions contribution per month (positive = above baseline, negative = below).
Computed via TreeExplainer on the trained XGBoost model.

Top-10 drivers by mean absolute SHAP contribution (averaged over all 12 forecast months):
{importance_table}

Monthly top-3 contributing drivers:
{monthly_top3_table}

Feature glossary:
  adefno_lag_1/2/3          Autoregressive lags of ADEFNO (t-1, t-2, t-3)
  ADEFNO_diff               Month-over-month change in ADEFNO at forecast origin
  ADEFNO_diff_lag_1..6      Lagged first differences of ADEFNO
  adefno_rolling_3m_mean    Rolling 3-month average of ADEFNO (prior values only)
  adefno_rolling_6m_mean    Rolling 6-month average of ADEFNO (prior values only)
  FDEFX                     Realized federal defense expenditures (quarterly, forward-filled)
  IPB52300S                 Defense & space industrial production index
  year                      Calendar year (captures secular trend)
  month / quarter / is_q4   Seasonal and calendar pattern features

---

## Analysis Request

Provide a structured analysis covering exactly the four sections below, then an
Executive Summary. Do not add sections. Do not discuss market share scenarios
(handled in SAC). Do not add geopolitical speculation beyond what the data supports.

---

### Section 1 — Market Volume & Historical Context

Using only the ADEFNO values provided above:
- Describe the 2026 forecast trajectory (H1 trough, H2 recovery, year-end level).
- Place the annual total ({annual_total_bn} USD bn) in context of the 2020–2025 range.
- Note the January spike and explain it as an artefact of the Dec 2025 outlier
  feeding into the AR structure, not a genuine demand signal.
- Keep to 3–4 short paragraphs.

### Section 2 — Driver Interpretation

Using only the SHAP table and feature glossary above:
- **AR Momentum** (adefno_lag_1, ADEFNO_diff, rolling means): What does the dominance
  of these features tell planners about the nature of defense order patterns?
- **FDEFX (Policy)**: What economic dynamic does realized government expenditure capture
  that AR lags cannot? Reference only the FDEFX values provided.
- **IPB52300S (Supply-Side)**: What does the production index add to the model?
  Reference only the IPB52300S values provided.
- One paragraph per driver category. No invented numbers.

### Section 3 — Monitoring Indicators for 2026

Provide a table of exactly 4 KPIs the planner must track quarterly to validate or
revise the forecast assumption. For each KPI:
  - Name & description
  - Official primary source with exact URL
  - Update cadence (monthly / quarterly)
  - What to watch for (one sentence, no invented thresholds)

Use Markdown table format.

### Section 4 — Key Risks & Model Limitation

Cover exactly two risk areas:

(a) **US Federal Budget Dynamics**: Discuss continuing resolution risk and debt-ceiling
    dynamics as they affect ADEFNO. Do not invent probability estimates.
    If you reference budget figures, cite the CBO or DoD Comptroller with a URL.

(b) **Carry-Forward Limitation**: Explain in plain language what it means that
    IPB52300S and FDEFX are frozen at their {ipb_last_month} / {fdefx_last_quarter}
    values for the entire 12-month horizon. What class of macro shock would most
    rapidly invalidate the forecast?

---

### Executive Summary

Provide exactly 6 bullet points, maximum 2 lines each. Written for direct use in a
SAC Planning Story or management slide. Bullets must cover:
  1. Core forecast message (annual total, trajectory)
  2. Strongest driver and what it implies for forecast confidence
  3. Single most important monitoring KPI with update cadence
  4. Primary risk to the forecast
  5. Model caveat (carry-forward limitation, plain language)
  6. Recommendation for planning robustness (e.g., scenario band rather than point estimate)
"""

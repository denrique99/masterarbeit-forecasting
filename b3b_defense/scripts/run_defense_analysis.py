"""
B3b Defense — LLM Macroeconomic Analysis
=========================================
Loads verified CSV data, computes context statistics, builds the prompt,
prints it for review, then calls Claude and saves the response.

Usage:
    python scripts/run_defense_analysis.py

Requires:
    ANTHROPIC_API_KEY in ../../.env (project root)
"""

import os
import sys

# Force UTF-8 output on Windows (avoids CP1252 encoding errors)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import anthropic

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR     = Path(__file__).parent
BASE_DIR       = SCRIPT_DIR.parent
DATA_RAW       = BASE_DIR / 'data' / 'raw'
DATA_PROCESSED = BASE_DIR / 'data' / 'processed'
OUTPUT_DIR     = BASE_DIR / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

# Add scripts/ to path so we can import the prompt module
sys.path.insert(0, str(SCRIPT_DIR))
from prompts.defense_analysis_prompt import SYSTEM_PROMPT, build_user_prompt

# ---------------------------------------------------------------------------
# Load API key
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=BASE_DIR.parent / '.env')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise EnvironmentError(
        'ANTHROPIC_API_KEY not found. Add it to the project .env file.'
    )

# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------
# claude-sonnet-4-5   $3.00 input / $15.00 output per 1M tokens  (active)
MODEL = 'claude-sonnet-4-5'

# claude-haiku-4-5    $1.00 input / $5.00 output  per 1M tokens  (cheapest)
# MODEL = 'claude-haiku-4-5'

# claude-sonnet-4-6   $3.00 input / $15.00 output per 1M tokens  (latest)
# MODEL = 'claude-sonnet-4-6'

# claude-opus-4-6     $5.00 input / $25.00 output per 1M tokens  (most capable)
# MODEL = 'claude-opus-4-6'

MAX_TOKENS = 3500

# ===========================================================================
# 1. Load and compute ADEFNO statistics
# ===========================================================================
adefno_raw = pd.read_csv(DATA_RAW / 'ADEFNO.csv', parse_dates=['observation_date'])
adefno_raw = adefno_raw.rename(columns={'observation_date': 'date'}).sort_values('date')

# Last historical value = Dec 2025 (simulated current date: 31.12.2025)
adefno_hist = adefno_raw[adefno_raw['date'] <= '2025-12-31'].copy()
last_row     = adefno_hist.iloc[-1]
adefno_last_month = last_row['date'].strftime('%b %Y')
adefno_last_value = last_row['ADEFNO']

# 12-month average 2025 (Jan–Dec 2025)
adefno_2025 = adefno_hist[adefno_hist['date'].dt.year == 2025]['ADEFNO']
adefno_12m_avg = adefno_2025.mean()

# 2020–2025 range
adefno_2020_2025 = adefno_hist[adefno_hist['date'].dt.year >= 2020]['ADEFNO']
idx_min = adefno_2020_2025.idxmin()
idx_max = adefno_2020_2025.idxmax()
adefno_min_val  = adefno_2020_2025.loc[idx_min]
adefno_max_val  = adefno_2020_2025.loc[idx_max]
adefno_min_date = adefno_hist.loc[idx_min, 'date'].strftime('%b %Y')
adefno_max_date = adefno_hist.loc[idx_max, 'date'].strftime('%b %Y')

# ===========================================================================
# 2. Load and compute FDEFX statistics
# ===========================================================================
fdefx_raw = pd.read_csv(DATA_RAW / 'FDEFX.csv', parse_dates=['observation_date'])
fdefx_raw = fdefx_raw.rename(columns={'observation_date': 'date'}).sort_values('date')

# Last quarterly value on or before 2025-12-31
fdefx_hist     = fdefx_raw[fdefx_raw['date'] <= '2025-12-31'].copy()
fdefx_last_row = fdefx_hist.iloc[-1]
fdefx_last_val = fdefx_last_row['FDEFX']
fdefx_last_qtr = fdefx_last_row['date']

# Quarter label (e.g. "Q4 2025")
q_num = (fdefx_last_qtr.month - 1) // 3 + 1
fdefx_last_quarter = f'Q{q_num} {fdefx_last_qtr.year}'

# Prior-year same quarter
prior_date       = fdefx_last_qtr - pd.DateOffset(years=1)
fdefx_prior_row  = fdefx_hist[fdefx_hist['date'] == prior_date]
if fdefx_prior_row.empty:
    # Fallback: nearest row one year back
    fdefx_prior_row = fdefx_hist.iloc[-5:-4]
fdefx_prior_val = float(fdefx_prior_row['FDEFX'].iloc[0])
fdefx_yoy       = (fdefx_last_val - fdefx_prior_val) / fdefx_prior_val * 100

# ===========================================================================
# 3. Load and compute IPB52300S statistics
# ===========================================================================
ipb_raw = pd.read_csv(DATA_RAW / 'IPB52300S.csv', parse_dates=['observation_date'])
ipb_raw = ipb_raw.rename(columns={'observation_date': 'date'}).sort_values('date')

ipb_hist      = ipb_raw[ipb_raw['date'] <= '2025-12-31'].copy()
ipb_last_row  = ipb_hist.iloc[-1]
ipb_last_val  = ipb_last_row['IPB52300S']
ipb_last_month_label = ipb_last_row['date'].strftime('%b %Y')

# 12-month trend: Jan 2025 → Dec 2025
ipb_2025       = ipb_hist[ipb_hist['date'].dt.year == 2025]['IPB52300S']
ipb_jan_val    = ipb_hist[ipb_hist['date'] == '2025-01-01']['IPB52300S'].iloc[0]
ipb_12m_change = ipb_last_val - ipb_jan_val
ipb_direction  = 'upward' if ipb_12m_change > 0 else 'downward'

# ===========================================================================
# 4. Load forecast and compute table
# ===========================================================================
forecast_df = pd.read_csv(DATA_PROCESSED / 'defense_forecast_2026_sac.csv')
forecast_df['date_parsed'] = pd.to_datetime(
    forecast_df['Date'].astype(str), format='%Y%m'
)
forecast_df['Month']        = forecast_df['date_parsed'].dt.strftime('%b %Y')
forecast_df['ADEFNO_USD_mn'] = (forecast_df['Net_Value_USD'] / 1e6).round(1)
annual_total_bn = (forecast_df['Net_Value_USD'].sum() / 1e9).round(1)

forecast_table = forecast_df[['Month', 'ADEFNO_USD_mn']].to_string(index=False)

# ===========================================================================
# 5. Load SHAP drivers and compute tables
# ===========================================================================
drivers_df   = pd.read_csv(DATA_PROCESSED / 'defense_forecast_2026_drivers_sac.csv')
feature_shap = drivers_df[~drivers_df['Driver'].isin(['base_value', 'prediction'])].copy()
feature_shap['abs_shap'] = feature_shap['SHAP_Value_USD_mn'].abs()

# Base value (same for all months)
base_value_mn = float(
    drivers_df[drivers_df['Driver'] == 'base_value']['SHAP_Value_USD_mn'].iloc[0]
)

# Overall importance: mean |SHAP| across 12 months
importance_df = (
    feature_shap.groupby('Driver')['abs_shap']
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
    .rename(columns={'abs_shap': 'Mean_Abs_SHAP_USD_mn'})
)
importance_df['Mean_Abs_SHAP_USD_mn'] = importance_df['Mean_Abs_SHAP_USD_mn'].round(1)
importance_table = importance_df.to_string(index=False)

# Monthly top-3
monthly_top3 = (
    feature_shap.sort_values('abs_shap', ascending=False)
    .groupby('Date')
    .head(3)
    .sort_values(['Date', 'abs_shap'], ascending=[True, False])
    .copy()
)
monthly_top3['Month'] = pd.to_datetime(
    monthly_top3['Date'].astype(str), format='%Y%m'
).dt.strftime('%b %Y')
monthly_top3['SHAP_sign'] = monthly_top3['SHAP_Value_USD_mn'].apply(
    lambda x: f'+{x:.1f}' if x >= 0 else f'{x:.1f}'
)
monthly_top3_table = (
    monthly_top3[['Month', 'Driver', 'SHAP_sign']]
    .rename(columns={'SHAP_sign': 'SHAP_USD_mn'})
    .to_string(index=False)
)

# ===========================================================================
# 6. Build prompt
# ===========================================================================
user_prompt = build_user_prompt(
    adefno_last_month      = adefno_last_month,
    adefno_last_value_mn   = f'{adefno_last_value:,.0f}',
    adefno_12m_avg_mn      = f'{adefno_12m_avg:,.0f}',
    adefno_range_min_mn    = f'{adefno_min_val:,.0f}',
    adefno_range_min_date  = adefno_min_date,
    adefno_range_max_mn    = f'{adefno_max_val:,.0f}',
    adefno_range_max_date  = adefno_max_date,
    fdefx_last_quarter     = fdefx_last_quarter,
    fdefx_last_value_bn    = f'{fdefx_last_val:,.1f}',
    fdefx_prior_value_bn   = f'{fdefx_prior_val:,.1f}',
    fdefx_yoy_pct          = f'{fdefx_yoy:+.1f}%',
    ipb_last_month         = ipb_last_month_label,
    ipb_last_value         = f'{ipb_last_val:.2f}',
    ipb_12m_start_value    = f'{ipb_jan_val:.2f}',
    ipb_12m_change         = f'{ipb_12m_change:+.2f}',
    ipb_trend_direction    = ipb_direction,
    forecast_table         = forecast_table,
    annual_total_bn        = str(annual_total_bn),
    base_value_mn          = f'{base_value_mn:,.1f}',
    importance_table       = importance_table,
    monthly_top3_table     = monthly_top3_table,
)

# ===========================================================================
# 7. Print full prompt for review
# ===========================================================================
SEP = '=' * 72
print(SEP)
print('SYSTEM PROMPT')
print(SEP)
print(SYSTEM_PROMPT)
print()
print(SEP)
print('USER PROMPT')
print(SEP)
print(user_prompt)
print(SEP)
print(f'Model:         {MODEL}')
print(f'Max tokens:    {MAX_TOKENS}')
print(f'Prompt length: {len(user_prompt):,} characters')
print(SEP)
print()

# ===========================================================================
# 8. Confirm before calling the API
# ===========================================================================
answer = input('Send to API? [y/N] ').strip().lower()
if answer != 'y':
    print('Aborted. No API call made.')
    sys.exit(0)

# ===========================================================================
# 9. API call (streaming)
# ===========================================================================
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

print(f'\nCalling {MODEL} ...\n')
print('-' * 72)

llm_response = ''
with client.messages.stream(
    model=MODEL,
    max_tokens=MAX_TOKENS,
    system=SYSTEM_PROMPT,
    messages=[{'role': 'user', 'content': user_prompt}],
) as stream:
    for text in stream.text_stream:
        llm_response += text
        print(text, end='', flush=True)

print('\n' + '-' * 72)
print('Streaming complete.')

# ===========================================================================
# 10. Save output
# ===========================================================================
output_path = OUTPUT_DIR / 'defense_analysis_2026.md'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('# LLM Macroeconomic Analysis — US Defense Market 2026\n\n')
    f.write(f'**Model:** {MODEL}  \n')
    f.write(f'**Prompt length:** {len(user_prompt):,} characters  \n\n')
    f.write('---\n\n')
    f.write(llm_response)

print(f'\nResponse saved to: {output_path}')

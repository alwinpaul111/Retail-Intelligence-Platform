# Retail Intelligence & Demand Forecasting Platform

 **Live dashboard:** [retail-intelligence-platform-c7otajkennyrv5d5jfow8y.streamlit.app](https://retail-intelligence-platform-c7otajkennyrv5d5jfow8y.streamlit.app/)

An end-to-end analytics platform for a simulated nationwide retail chain (8 stores,
4 Indian cities, 40 SKUs across 5 categories, 2 years of daily transactions).
Built to demonstrate the full data science stack: **advanced SQL → statistics →
EDA → feature engineering → ML modeling → business insights → interactive
dashboard → containerized deployment.**

## Why this project

Most portfolio projects stop at "trained a model, got 85% accuracy." This one
is scoped around a realistic business question retail chains actually pay for:
*where should we stock more inventory, and what's it worth?* Every layer below
feeds into that answer — the SQL views compute the KPIs, the stats module
validates whether a promotion campaign actually worked, the model forecasts
demand, and the final output is a concrete profit number tied to a stocking
decision.

## Architecture

```
retail-intelligence/
├── data/                  # generated CSVs + engineered feature table + EDA outputs
├── sql/
│   ├── 01_schema.sql          # tables, PK/FK, indexing strategy
│   ├── 02_views.sql           # window functions, CTEs (SQLite)
│   ├── 03_postgres_procedures.sql  # native partitioning + stored procedures (Postgres)
│   └── 04_business_queries.sql     # the exact requested query set
├── src/
│   ├── generate_data.py       # synthetic multi-table dataset generator
│   ├── load_db.py             # CSV -> SQLite loader + view builder
│   ├── feature_engineering.py # lag/rolling/calendar/weather features
│   ├── statistical_analysis.py# hypothesis testing, A/B test, ANOVA, CIs
│   ├── eda.py                 # seasonality, segmentation, outliers, heatmaps
│   └── train_model.py         # LightGBM + XGBoost forecasting, SHAP, insight gen
├── api/main.py             # FastAPI inference service
├── dashboard/app.py        # Streamlit interactive dashboard
├── Dockerfile.api / Dockerfile.dashboard / docker-compose.yml
└── requirements.txt
```

## Quickstart

```bash
pip install -r requirements.txt

python src/generate_data.py          # ~215K synthetic transactions
python src/load_db.py                # builds retail.db (SQLite) + views
python src/feature_engineering.py    # builds data/model_table.parquet
python src/statistical_analysis.py   # prints hypothesis-test / ANOVA / CI report
python src/eda.py                    # seasonality, segmentation, outlier report
python src/train_model.py            # trains + saves models, SHAP, business insight

uvicorn api.main:app --reload --port 8000       # forecasting API
streamlit run dashboard/app.py                   # dashboard
```

Or with Docker:
```bash
docker compose up --build
# API:       http://localhost:8000/docs
# Dashboard: http://localhost:8501
```

## 1. Advanced SQL

- **Window functions**: rolling 7/30-day revenue, `RANK()` for top products
  *within each city*, `LAG()` for month-over-month growth
- **CTEs**: multi-step cohort analysis (new vs. returning customer revenue),
  stockout detection joining inventory against historical demand
- **Views**: `vw_customer_rfm`, `vw_rolling_30d_revenue`, `vw_monthly_growth`,
  `vw_product_revenue_rank_by_city`, `vw_repeat_purchase_rate`
- **Stored procedures**: SQLite has no PL/pgSQL, so `sql/03_postgres_procedures.sql`
  contains genuine Postgres stored procedures (`refresh_daily_store_kpis()`,
  `get_customer_ltv()`, `estimate_inventory_uplift_profit()`) — runnable against
  any Postgres instance (Supabase/Neon/RDS free tier)
- **Indexing**: composite indexes documented with rationale in `01_schema.sql`
  (e.g. `(date, store_id)` as a covering index for date-range queries)
- **Partitioning**: native `PARTITION BY RANGE (date)` quarterly partitioning
  specified for Postgres, since SQLite doesn't support it natively

Run the exact requested query set directly:
```bash
sqlite3 retail.db < sql/04_business_queries.sql
```

## 2. Statistics

`src/statistical_analysis.py` answers, with real output:

- **"Did discount campaign A significantly increase sales?"** — Welch's t-test,
  treatment (promo-active days) vs. control (same categories, no promo):
  **+22.9% lift, p < 0.001, statistically significant**, with 95% CI on the
  mean difference
- **ANOVA**: daily revenue differs significantly across cities (F=643, p≈0)
- **Correlation**: revenue vs. discount, revenue vs. temperature (Pearson r + p-values)
- **Confidence intervals**: repeat purchase rate, average transaction value

## 3. EDA

`src/eda.py` produces: monthly seasonality chart, day-of-week × month revenue
heatmap, regional trend breakdown, RFM-based customer segmentation (Champions /
Loyal / Potential / At Risk / Lost), missing-value audit, and IQR-based outlier
detection — all rendered in the dashboard's EDA tab.

## 4. Feature Engineering

Store × category × day grain: lag features (1/7/14/28-day), rolling mean/std
(7-day, 28-day), calendar features (day-of-week, holiday flags, cyclical
day-of-year encoding), a 14-day pre-Diwali "festive window" flag, weather
features with a category-specific interaction term (hot-day × weather-sensitive
category), and customer RFM features.

## 5. ML Models

LightGBM and XGBoost regressors forecasting daily store-category revenue,
benchmarked against a naive "same as last week" baseline:

| Model | MAE | RMSE | MAPE |
|---|---|---|---|
| LightGBM | 16,629 | 43,186 | 23.2% |
| XGBoost | 16,198 | 43,091 | 21.3% |
| Naive (lag-7) | 26,792 | 76,954 | 26.1% |

Both models beat the naive baseline by ~35-40% on MAE. SHAP confirms
`revenue_roll_mean_28` and `revenue_roll_mean_7` dominate — sensible, since
recent demand level is the strongest predictor of near-term demand, with
festive-window and day-of-week as the next-strongest signals.

Prediction intervals (empirical residual quantiles) are served alongside
point forecasts via the API, not just point estimates — important for
inventory planning where the uncertainty band matters as much as the mean.

## 6. Business Insights

Auto-generated from the model + festive-window data, e.g.:

> Increasing inventory of 'Electronics' in Mumbai by 15% ahead of the festive
> season is projected to add ₹576,637 in incremental profit over a 30-day
> window (avg daily demand: 60 units, blended margin assumption: 30%).

This is computed programmatically in `train_model.py` (and reproducible as a
genuine Postgres function in `estimate_inventory_uplift_profit()`), not
hand-typed — swap in your real margin assumptions and it re-derives the number.

## 7. Dashboard

**Live at:** https://retail-intelligence-platform-c7otajkennyrv5d5jfow8y.streamlit.app/

Streamlit app with 6 tabs: KPIs, Forecast (model comparison + SHAP + trend
explorer), Store Performance, Product Performance, Customer Segments (RFM),
and EDA — all filterable by date range, city, and category.

## 8. Deployment

- **FastAPI**: `/predict` (single forecast with 90% prediction interval),
  `/insights/latest`, `/model/comparison`, `/health`
- **Docker**: separate images for API and dashboard, orchestrated via
  `docker-compose.yml`
- **Streamlit Community Cloud**: dashboard deployed directly from this repo
  (`dashboard/app.py`), auto-redeploys on every push to `main`
- **Cloud (API)**: designed to deploy as-is to Render or an AWS ECS/Fargate
  task using `Dockerfile.api` — point `DATABASE_URL` at a managed Postgres
  instance and swap SQLite for Postgres in `load_db.py` (schema is already
  Postgres-portable)

## Troubleshooting

### macOS: `OSError: ... Library not loaded: @rpath/libomp.dylib` when running `train_model.py`

LightGBM depends on OpenMP (`libomp`), which isn't bundled with the pip wheel on macOS —
it has to come from Homebrew. This error means either libomp isn't installed, or (on
Apple Silicon Macs with an older Homebrew setup) there's an **architecture mismatch**
between your Python and your Homebrew installation.

**Step 1 — check your setup:**
```bash
uname -m                                    # should print arm64 on Apple Silicon
python3 -c "import platform; print(platform.machine())"   # should also print arm64
which brew
file $(which brew)
```

If `brew` lives at `/usr/local/bin/brew` instead of `/opt/homebrew/bin/brew`, you're
running an Intel/Rosetta Homebrew on an Apple Silicon Mac — that's the root cause.

**Step 2 — install a native ARM Homebrew:**
```bash
arch -arm64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Step 3 — install libomp via the native brew:**
```bash
/opt/homebrew/bin/brew install libomp
```

**Step 4 — retry:**
```bash
python src/train_model.py
```

If `uname -m` and the Python check both already say `arm64` and `brew` is already at
`/opt/homebrew/bin/brew`, you likely just need:
```bash
brew install libomp
```
with no architecture juggling required — the mismatch scenario above is specific to
machines where Homebrew was originally installed before switching to (or under
emulation on) Apple Silicon.

Note: this issue is macOS-specific and doesn't affect the deployed Streamlit Cloud
app, which runs on Linux.

## Honest scope notes

This uses synthetic data (documented generation logic in `generate_data.py`,
seeded for reproducibility) rather than a scraped/licensed real dataset — it
was designed to be realistic enough that every technique here transfers
directly to real retail data, while keeping the whole pipeline fast enough to
run and iterate on end-to-end. If asked in an interview, be upfront about
this: it's a full demonstration of the pipeline, not a claim about specific
real-world retail numbers.

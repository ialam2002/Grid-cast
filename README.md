# GridCast

GridCast is a production-minded MVP for **energy load forecasting + grid operations monitoring** focused on CAISO first.

## What is implemented in this first iteration

- Bronze ingest jobs for CAISO + optional NOAA + optional EIA with ingestion metadata/audit logs.
- Silver feature pipeline with hourly normalization, lag/rolling/calendar features, and contract checks.
- Daily training pipeline with baseline (`t-24`) vs model comparison, top-driver attribution, and model registry artifacts.
- Scoring/publishing pipeline that writes gold forecast, metrics, risk events, and API cache artifacts.
- FastAPI endpoints for `next24h`, `peak stress risk`, and `top drivers` with model lineage fields.
- Airflow DAGs wired to executable Python modules.
- Terraform storage module starter for bronze/silver/gold/log buckets.

## Repo layout

- `src/gridcast` - ingestion, feature engineering, validation contracts, training, scoring, and runners
- `api/app` - FastAPI serving layer
- `airflow/dags` - orchestration DAG definitions
- `infra/terraform` - Terraform modules and environment stacks
- `schemas` - data contracts for bronze/silver/gold/ops tables
- `tests` - unit tests for core logic

## Quick start (local)

1. Install dependencies.
2. Run tests.
3. Optionally run a local training pass if you have source API credentials/config.

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## End-to-end local run (requires network for source APIs)

Environment variables:

- `GRIDCAST_REGION` (default `CAISO`)
- `GRIDCAST_NOAA_TOKEN` (optional)
- `GRIDCAST_NOAA_STATION_ID` (optional)
- `GRIDCAST_EIA_API_KEY` (optional)
- `GRIDCAST_DATA_DIR` (default `data`)
- `GRIDCAST_ARTIFACTS_DIR` (default `artifacts`)

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
$env:GRIDCAST_NOAA_TOKEN="<token>"
.\.venv\Scripts\python.exe -m gridcast.pipeline.mvp_runner --hours 168 --horizon 24
```

## Job-by-job execution

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m gridcast.pipeline.ingest_job --hours 2160
.\.venv\Scripts\python.exe -m gridcast.pipeline.silver_job
.\.venv\Scripts\python.exe -m gridcast.pipeline.train_job --horizons 1 24
.\.venv\Scripts\python.exe -m gridcast.pipeline.score_job
```

## API run

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 0.0.0.0 --port 8000
```

## Notes

- This repository now includes EIA ingestion support and schema contract files; source-specific endpoint tuning can be expanded per balancing area.
- Spark/Delta/dbt/Athena and full Terraform modules (`network`, `iam`, `compute`, `catalog`, `monitoring`, `secrets`) are the next infra increment.


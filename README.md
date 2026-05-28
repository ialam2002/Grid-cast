# GridCast

GridCast is an MVP for **energy load forecasting + grid operations monitoring** focused on CAISO first.

## What is implemented in this first iteration

- CAISO load ingestion client (real endpoint) and NOAA weather client (token-based).
- Hourly silver feature builder for lag/rolling/calendar/peak indicators.
- Model training pipeline with:
  - seasonal naive baseline (t-24)
  - gradient boosting regressor
- Evaluation metrics by horizon (`t+1h`, `t+24h`) and segment (`peak`, `offpeak`).
- FastAPI service for forecast and risk endpoints.
- Airflow DAG scaffolds for 4 core pipelines.
- Terraform starter module for S3 lakehouse buckets.

## Repo layout

- `src/gridcast` - ingestion, feature engineering, training, and runners
- `api/app` - FastAPI serving layer
- `airflow/dags` - orchestration DAG definitions
- `infra/terraform` - Terraform modules and environment stacks
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

## Local pipeline run (requires network and source credentials)

Environment variables:

- `GRIDCAST_REGION` (default `CAISO`)
- `GRIDCAST_NOAA_TOKEN` (optional but needed for NOAA API)
- `GRIDCAST_EIA_API_KEY` (reserved for next step)

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
$env:GRIDCAST_NOAA_TOKEN="<token>"
.\.venv\Scripts\python.exe -m gridcast.pipeline.mvp_runner --hours 168 --horizon 24
```

## Notes

- This MVP intentionally starts with CAISO + NOAA. EIA ingestion adapter and dbt/Athena marts are next.
- Airflow and Terraform files are scaffold-level to accelerate phase-2 productionization.


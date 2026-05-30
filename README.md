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
- `infra/athena/ddl` - generated Athena external table DDL
- `dbt` - staging and mart models for analytics
- `schemas` - data contracts for bronze/silver/gold/ops tables
- `scripts` - CI helper scripts (for example DAG import checks)
- `tests` - unit tests for core logic

## Integration fixture snapshots

Fixture snapshots for pipeline integration tests are stored in `tests/fixtures`.

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe scripts\generate_test_fixtures.py
```

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
- `GRIDCAST_STRICT_INGESTION` (default `false`; when `true`, optional source failures fail the run)

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
$env:GRIDCAST_NOAA_TOKEN="<token>"
.\.venv\Scripts\python.exe -m gridcast.pipeline.mvp_runner --hours 168 --horizon 24
```

To discover valid NOAA LCD station IDs for California:

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe -c "import os,requests; h={'token':os.environ.get('GRIDCAST_NOAA_TOKEN','')}; p={'datasetid':'LCD','locationid':'FIPS:06','limit':5}; r=requests.get('https://www.ncei.noaa.gov/cdo-web/api/v2/stations',headers=h,params=p,timeout=60); print(r.status_code); print(r.text[:800])"
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

For longer historical pulls, CAISO ingestion supports API window chunking:

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m gridcast.pipeline.ingest_job --hours 26280 --caiso-chunk-days 28 --caiso-chunk-pause-seconds 2
```

## Generate Athena DDL from schema contracts

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m gridcast.catalog.generate_athena_ddl --schema-dir schemas --output-dir infra/athena/ddl --s3-root s3://gridcast-dev-lakehouse
```

## dbt models

- `dbt/models/staging/stg_load_weather_hourly.sql` provides standardized hourly features for analytics.
- `dbt/models/marts/fct_forecast_quality.sql` computes daily MAE/RMSE/MAPE by horizon.

### dbt profile setup (Athena)

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe scripts\render_dbt_profile.py
```

Set environment variables before running dbt:

- `DBT_ATHENA_S3_STAGING_DIR`
- `AWS_REGION`
- `DBT_ATHENA_SCHEMA`
- `DBT_ATHENA_WORKGROUP`

Optional dbt dependency installation:

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe -m pip install -r requirements-dbt.txt
```

## API run

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 0.0.0.0 --port 8000
```

## Notes

- This repository now includes EIA ingestion support and schema contract files; source-specific endpoint tuning can be expanded per balancing area.
- Terraform includes `storage`, `iam`, `catalog`, `monitoring`, and `secrets` modules plus `dev`, `stage`, and `prod` environments.
- Each Terraform environment has `backend.hcl.example` and `terraform.tfvars.example` for remote state and role-assumption bootstrap.
- CI now runs unit tests, DAG import checks, Terraform fmt/validate/plan, and Athena DDL generation checks.

### Terraform remote-state bootstrap (example)

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast\infra\terraform\env\dev"
Copy-Item backend.hcl.example backend.hcl
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init -backend-config=backend.hcl
terraform plan -var-file=terraform.tfvars
```

### Easier AWS/Terraform bootstrap (recommended)

Use the helper script to generate `backend.hcl` and `terraform.tfvars` in one step:

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe scripts\bootstrap_terraform_env.py --env dev --account-id 111122223333
```

Then run Terraform for that environment:

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast\infra\terraform\env\dev"
terraform init -backend-config=backend.hcl
terraform plan -var-file=terraform.tfvars
```

To overwrite existing local files intentionally:

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe scripts\bootstrap_terraform_env.py --env dev --account-id 111122223333 --force
```


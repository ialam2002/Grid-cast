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

## Production Deployment (End-to-End)

### Prerequisites

- AWS account with appropriate IAM permissions (see `IAM Policy for Terraform` section below)
- AWS CLI configured with credentials
- Terraform >= 1.6
- API secrets stored in AWS Secrets Manager or SSM Parameter Store

### IAM Policy for Terraform

Your Terraform execution IAM user needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
	{
	  "Sid": "GridcastTerraformPermissions",
	  "Effect": "Allow",
	  "Action": [
		"sts:GetCallerIdentity",
		"s3:CreateBucket",
		"s3:DeleteBucket",
		"s3:ListBucket",
		"s3:GetBucketLocation",
		"s3:GetBucketVersioning",
		"s3:PutBucketVersioning",
		"s3:GetBucketLifecycleConfiguration",
		"s3:PutBucketLifecycleConfiguration",
		"s3:DeleteBucketLifecycle",
		"s3:GetBucketTagging",
		"s3:PutBucketTagging",
		"s3:DeleteBucketTagging",
		"s3:GetObject",
		"s3:PutObject",
		"s3:DeleteObject",
		"dynamodb:CreateTable",
		"dynamodb:DeleteTable",
		"dynamodb:DescribeTable",
		"dynamodb:GetItem",
		"dynamodb:PutItem",
		"dynamodb:DeleteItem",
		"dynamodb:UpdateItem",
		"iam:CreateRole",
		"iam:GetRole",
		"iam:DeleteRole",
		"iam:UpdateAssumeRolePolicy",
		"iam:TagRole",
		"iam:UntagRole",
		"glue:CreateDatabase",
		"glue:GetDatabase",
		"glue:GetDatabases",
		"glue:DeleteDatabase",
		"logs:CreateLogGroup",
		"logs:DeleteLogGroup",
		"logs:DescribeLogGroups",
		"logs:PutRetentionPolicy",
		"logs:DeleteRetentionPolicy",
		"logs:TagLogGroup",
		"logs:UntagLogGroup",
		"ssm:PutParameter",
		"ssm:GetParameter",
		"ssm:DeleteParameter",
		"ssm:AddTagsToResource",
		"ssm:RemoveTagsFromResource",
		"ssm:ListTagsForResource",
		"cloudwatch:PutMetricAlarm",
		"cloudwatch:DeleteAlarms",
		"cloudwatch:DescribeAlarms"
	  ],
	  "Resource": "*"
	}
  ]
}
```

### Step 1: Set AWS Budget Alerts

In AWS Console → Billing and Cost Management:

1. Create a **$1 USD budget** with email alerts at 80% and 100%.
2. Enable **Billing alerts** so you never exceed free tier.

### Step 2: Bootstrap Terraform for Dev

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe scripts\bootstrap_terraform_env.py --env dev --account-id <YOUR_12_DIGIT_ACCOUNT_ID> --region us-east-2 --force
```

This generates:
- `infra/terraform/env/dev/backend.hcl` (S3 /DynamoDB state config)
- `infra/terraform/env/dev/terraform.tfvars` (dev settings)

### Step 3: Create Remote State Infrastructure

Once and only once per account:

```powershell
$Region = "us-east-2"
$StateBucket = "gridcast-tfstate-dev"
$LockTable = "gridcast-tf-locks"

aws s3api create-bucket --bucket $StateBucket --region $Region --create-bucket-configuration LocationConstraint=$Region
aws s3api put-bucket-versioning --bucket $StateBucket --versioning-configuration Status=Enabled
aws dynamodb create-table --table-name $LockTable --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region $Region
```

### Step 4: Deploy Dev Infrastructure

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast\infra\terraform\env\dev"
terraform init -backend-config=backend.hcl
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### Step 5: Set API Secrets in SSM Parameter Store

```powershell
aws ssm put-parameter --name "/gridcast/dev/eia-api-key" --type "SecureString" --value "<YOUR_EIA_KEY>" --overwrite --region us-east-2
aws ssm put-parameter --name "/gridcast/dev/noaa-token" --type "SecureString" --value "<YOUR_NOAA_TOKEN>" --overwrite --region us-east-2
```

### Step 6: Run Cloud-Enabled Pipeline

Environment variables for cloud operation:

```powershell
$env:GRIDCAST_ENVIRONMENT = "dev"
$env:GRIDCAST_AWS_REGION = "us-east-2"
$env:GRIDCAST_S3_DATA_BUCKET = "gridcast-dev-bronze"
```

Then run the pipeline (it will fetch secrets from SSM automatically):

```powershell
cd "C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast"
.\.venv\Scripts\python.exe -m gridcast.pipeline.ingest_job --hours 168
.\.venv\Scripts\python.exe -m gridcast.pipeline.silver_job
.\.venv\Scripts\python.exe -m gridcast.pipeline.train_job --horizons 1 24
.\.venv\Scripts\python.exe -m gridcast.pipeline.score_job
```

### Step 7: Verify Glue Catalog

Check that your data was registered in Glue:

```powershell
aws glue get-databases --catalog-id <ACCOUNT_ID> --region us-east-2
```

You should see `gridcast_dev_bronze`, `gridcast_dev_silver`, and `gridcast_dev_gold`.

### Stage & Production Deployments

For stage and prod, repeat steps 2–5 with `--env stage` or `--env prod`:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_terraform_env.py --env stage --account-id <ACCOUNT_ID> --region us-east-2
.\.venv\Scripts\python.exe scripts\bootstrap_terraform_env.py --env prod --account-id <ACCOUNT_ID> --region us-east-2
```

Then bootstrap state:

```powershell
aws s3api create-bucket --bucket gridcast-tfstate-stage --region us-east-2 --create-bucket-configuration LocationConstraint=us-east-2
aws dynamodb create-table --table-name gridcast-tf-locks --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region us-east-2
```

Deploy each environment:

```powershell
terraform -chdir="C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast\infra\terraform\env\stage" init -backend-config=backend.hcl
terraform -chdir="C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast\infra\terraform\env\stage" apply -var-file=terraform.tfvars
```

### Cleanup

To tear down a deployed environment:

```powershell
terraform -chdir="C:\Users\Iftekhar Alam\PycharmProjects\Grid-cast\infra\terraform\env\dev" destroy -var-file=terraform.tfvars
```

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


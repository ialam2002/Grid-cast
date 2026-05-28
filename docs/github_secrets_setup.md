# GitHub Secrets and Variables for GridCast CI/CD
#
# Required GitHub Actions secrets (Settings → Secrets and variables → Actions → Secrets):
#
# ─── AWS OIDC deploy roles (one per env) ─────────────────────────────────────────
# GRIDCAST_DEV_DEPLOY_ROLE_ARN       arn:aws:iam::<dev-account-id>:role/gridcast-dev-github-deploy
# GRIDCAST_STAGE_DEPLOY_ROLE_ARN     arn:aws:iam::<stage-account-id>:role/gridcast-stage-github-deploy
# GRIDCAST_PROD_DEPLOY_ROLE_ARN      arn:aws:iam::<prod-account-id>:role/gridcast-prod-github-deploy
#
# ─── Terraform remote state ──────────────────────────────────────────────────────
# GRIDCAST_TF_STATE_BUCKET_DEV       gridcast-tfstate-dev
# GRIDCAST_TF_STATE_BUCKET_STAGE     gridcast-tfstate-stage
# GRIDCAST_TF_STATE_BUCKET_PROD      gridcast-tfstate-prod
# GRIDCAST_TF_LOCK_TABLE             gridcast-tf-locks          (shared DynamoDB table)
#
# ─── Data lake S3 bucket names ───────────────────────────────────────────────────
# GRIDCAST_DATA_BUCKET_DEV           gridcast-dev-lakehouse
# GRIDCAST_DATA_BUCKET_STAGE         gridcast-stage-lakehouse
# GRIDCAST_DATA_BUCKET_PROD          gridcast-prod-lakehouse
#
# ─── dbt Athena staging buckets ──────────────────────────────────────────────────
# GRIDCAST_DBT_STAGING_BUCKET_DEV    gridcast-dev-dbt-staging
# GRIDCAST_DBT_STAGING_BUCKET_STAGE  gridcast-stage-dbt-staging
# GRIDCAST_DBT_STAGING_BUCKET_PROD   gridcast-prod-dbt-staging
#
# ─── Source API credentials (stored in AWS Secrets Manager; also used in Airflow) ─
# GRIDCAST_NOAA_TOKEN                <noaa api token>
# GRIDCAST_EIA_API_KEY               <eia api key>
#
# ─── GitHub Repository Variables (Settings → Variables) ─────────────────────────
# AWS_REGION                         us-west-2
#
# ─── GitHub Environments to configure ───────────────────────────────────────────
# Environment: dev
#   → No approval gate; auto-deploys after CI passes.
#
# Environment: stage
#   → Require reviewers: <your-team-name or individual GitHub users>
#   → Required status checks: deploy-dev
#
# Environment: prod
#   → Require reviewers: <your-team-name or individual GitHub users>
#   → Required status checks: deploy-stage
#   → Optional: deployment branch rules to restrict to main/master only
#
# ─── AWS OIDC IAM trust policy (add to each deploy role's trust document) ────────
#
# {
#   "Version": "2012-10-17",
#   "Statement": [{
#     "Effect": "Allow",
#     "Principal": { "Federated": "arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com" },
#     "Action": "sts:AssumeRoleWithWebIdentity",
#     "Condition": {
#       "StringEquals": {
#         "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
#       },
#       "StringLike": {
#         "token.actions.githubusercontent.com:sub": "repo:<your-github-org>/Grid-cast:*"
#       }
#     }
#   }]
# }


terraform {
  required_version = ">= 1.6.0"
  backend "s3" {
    use_lockfile = true
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  dynamic "assume_role" {
    for_each = var.assume_role_arn == "" ? [] : [1]
    content {
      role_arn = var.assume_role_arn
    }
  }
}

locals {
  project     = "gridcast"
  environment = "dev"
  tags = {
    project = local.project
    env     = local.environment
  }
}

# ── Free-tier cost guard settings for dev ─────────────────────────────────────
# S3 free tier: 5 GB storage, 20K GET, 2K PUT (12-month).
# Versioning is suspended so every pipeline run does not silently double storage.
# Objects expire after 90 days to auto-purge stale dev data.
module "storage" {
  source      = "../../modules/storage"
  project     = local.project
  environment = local.environment
  tags        = local.tags

  enable_versioning                  = false # Suspended — avoid version-multiplied storage
  lifecycle_expiration_days          = 90    # Auto-delete dev objects after 90 days
  noncurrent_version_expiration_days = 7     # Fast cleanup if versioning is ever re-enabled
}

module "iam" {
  source      = "../../modules/iam"
  project     = local.project
  environment = local.environment
  tags        = local.tags
}

module "catalog" {
  source      = "../../modules/catalog"
  project     = local.project
  environment = local.environment
  tags        = local.tags
}

# CloudWatch free tier: 5 GB log ingestion/archive, 10 alarms.
# 7-day retention keeps log archive lean; alarm is disabled to reserve free quota for prod.
module "monitoring" {
  source      = "../../modules/monitoring"
  project     = local.project
  environment = local.environment
  tags        = local.tags

  log_retention_days = 7     # Lean retention for dev
  enable_alarm       = false # Reserve free alarm quota for prod
}

# SSM Parameter Store standard SecureString is always free.
# (Replaces Secrets Manager which costs $0.40/secret/month.)
module "secrets" {
  source      = "../../modules/secrets"
  project     = local.project
  environment = local.environment
  tags        = local.tags
}

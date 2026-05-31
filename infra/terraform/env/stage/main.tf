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
  environment = "stage"
  tags = {
    project = local.project
    env     = local.environment
  }
}

module "storage" {
  source      = "../../modules/storage"
  project     = local.project
  environment = local.environment
  tags        = local.tags

  enable_versioning                  = true # Enable versioning for pre-prod validation
  noncurrent_version_expiration_days = 30   # Keep old versions for 30 days then purge
  lifecycle_expiration_days          = 180  # Expire stage data after 6 months
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

module "monitoring" {
  source      = "../../modules/monitoring"
  project     = local.project
  environment = local.environment
  tags        = local.tags

  log_retention_days = 14    # 2-week retention for stage
  enable_alarm       = false # Only enable alarms in prod
}

module "secrets" {
  source      = "../../modules/secrets"
  project     = local.project
  environment = local.environment
  tags        = local.tags
}

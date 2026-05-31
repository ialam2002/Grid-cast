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
  environment = "prod"
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

  enable_versioning                  = true # Full versioning for production data integrity
  noncurrent_version_expiration_days = 90   # Retain old versions for 90 days
  lifecycle_expiration_days          = 0    # Never auto-expire production data
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

  log_retention_days = 30   # 30-day retention for prod (within 5 GB free CW log tier)
  enable_alarm       = true # Enable latency alarm for production observability
}

module "secrets" {
  source      = "../../modules/secrets"
  project     = local.project
  environment = local.environment
  tags        = local.tags
}

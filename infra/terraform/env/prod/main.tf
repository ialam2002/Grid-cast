terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
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
}

module "secrets" {
  source      = "../../modules/secrets"
  project     = local.project
  environment = local.environment
  tags        = local.tags
}


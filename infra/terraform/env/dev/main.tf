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

module "storage" {
  source      = "../../modules/storage"
  project     = "gridcast"
  environment = "dev"
  tags = {
    project = "gridcast"
    env     = "dev"
  }
}


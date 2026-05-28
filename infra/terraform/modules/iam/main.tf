locals {
  role_name_prefix = "${var.project}-${var.environment}"
}

resource "aws_iam_role" "airflow" {
  name = "${local.role_name_prefix}-airflow-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "airflow.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role" "ecs_api" {
  name = "${local.role_name_prefix}-ecs-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}


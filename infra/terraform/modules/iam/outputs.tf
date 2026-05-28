output "airflow_role_arn" {
  value = aws_iam_role.airflow.arn
}

output "ecs_api_role_arn" {
  value = aws_iam_role.ecs_api.arn
}


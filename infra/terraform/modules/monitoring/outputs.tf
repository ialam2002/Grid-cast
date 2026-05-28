output "log_groups" {
  value = {
    pipeline = aws_cloudwatch_log_group.pipeline.name
    api      = aws_cloudwatch_log_group.api.name
  }
}


output "log_groups" {
  value = {
    pipeline = aws_cloudwatch_log_group.pipeline.name
    api      = aws_cloudwatch_log_group.api.name
  }
}

output "alarm_name" {
  value       = var.enable_alarm ? aws_cloudwatch_metric_alarm.api_latency[0].alarm_name : null
  description = "CloudWatch alarm name, or null when enable_alarm = false"
}

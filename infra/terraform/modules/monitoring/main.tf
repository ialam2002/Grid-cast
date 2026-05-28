resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/gridcast/${var.environment}/pipeline"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/gridcast/${var.environment}/api"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "${var.project}-${var.environment}-api-latency-p95"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "p95"
  threshold           = var.api_latency_alarm_threshold_ms
  alarm_description   = "GridCast API p95 latency above threshold"
  treat_missing_data  = "notBreaching"
}


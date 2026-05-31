variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "api_latency_alarm_threshold_ms" {
  type    = number
  default = 500
}

variable "tags" {
  type    = map(string)
  default = {}
}

# ── Free-tier cost controls ────────────────────────────────────────────────────
variable "log_retention_days" {
  type        = number
  default     = 7
  description = "CloudWatch log retention in days. The free tier includes 5 GB ingestion and archive; keeping retention short reduces costs once the free tier expires. Recommended: 7 for dev, 30 for stage/prod."
}

variable "enable_alarm" {
  type        = bool
  default     = false
  description = "Create the API latency CloudWatch alarm. The free tier includes 10 alarms; disable in dev to save them for production."
}

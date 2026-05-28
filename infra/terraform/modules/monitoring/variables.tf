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


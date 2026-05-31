variable "project" {
  type        = string
  description = "Project name prefix"
}

variable "environment" {
  type        = string
  description = "Environment name (dev/stage/prod)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Common resource tags"
}

# ── Free-tier cost controls ────────────────────────────────────────────────────
variable "enable_versioning" {
  type        = bool
  default     = false
  description = "Enable S3 object versioning. Disable in dev to avoid storing multiple versions that inflate storage beyond the 5 GB free tier."
}

variable "noncurrent_version_expiration_days" {
  type        = number
  default     = 30
  description = "Days before noncurrent object versions are permanently deleted. Only applies when enable_versioning = true."
}

variable "lifecycle_expiration_days" {
  type        = number
  default     = 0
  description = "Days before current objects expire and are deleted (0 = never). Set to e.g. 90 in dev to auto-purge old data and stay within the 5 GB free tier."
}

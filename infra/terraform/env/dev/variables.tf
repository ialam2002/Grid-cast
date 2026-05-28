variable "aws_region" {
  type        = string
  description = "AWS region for the environment"
  default     = "us-west-2"
}

variable "assume_role_arn" {
  type        = string
  description = "Optional role ARN used by Terraform execution identity"
  default     = ""
}

variable "state_bucket" {
  type        = string
  description = "S3 bucket for Terraform remote state"
  default     = ""
}

variable "state_lock_table" {
  type        = string
  description = "DynamoDB table for Terraform state locking"
  default     = ""
}

variable "state_key_prefix" {
  type        = string
  description = "Key prefix for Terraform state objects"
  default     = "gridcast"
}


# SSM Parameter Store standard SecureString parameters are always free
# (up to 10,000 API calls/month, 4 KB per value, default aws/ssm KMS key — no extra KMS charges).
# Secrets Manager costs $0.40 per secret/month and is NOT part of the AWS Free Tier.

resource "aws_ssm_parameter" "noaa_token" {
  name        = "/${var.project}/${var.environment}/noaa-token"
  type        = "SecureString"
  value       = "PLACEHOLDER" # Set the real value via AWS Console or CI/CD pipeline
  description = "NOAA API token for GridCast"
  tags        = var.tags

  lifecycle {
    ignore_changes = [value] # Prevent Terraform from overwriting manually-set secrets
  }
}

resource "aws_ssm_parameter" "eia_api_key" {
  name        = "/${var.project}/${var.environment}/eia-api-key"
  type        = "SecureString"
  value       = "PLACEHOLDER" # Set the real value via AWS Console or CI/CD pipeline
  description = "EIA API key for GridCast"
  tags        = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

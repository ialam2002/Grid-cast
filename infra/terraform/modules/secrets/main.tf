resource "aws_secretsmanager_secret" "noaa_token" {
  name        = "${var.project}/${var.environment}/noaa-token"
  description = "NOAA API token for GridCast"
  tags        = var.tags
}

resource "aws_secretsmanager_secret" "eia_api_key" {
  name        = "${var.project}/${var.environment}/eia-api-key"
  description = "EIA API key for GridCast"
  tags        = var.tags
}


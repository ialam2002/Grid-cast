output "secret_arns" {
  value = {
    noaa = aws_secretsmanager_secret.noaa_token.arn
    eia  = aws_secretsmanager_secret.eia_api_key.arn
  }
}


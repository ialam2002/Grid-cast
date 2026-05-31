output "parameter_names" {
  value = {
    noaa = aws_ssm_parameter.noaa_token.name
    eia  = aws_ssm_parameter.eia_api_key.name
  }
  description = "SSM Parameter Store names for GridCast API secrets (fetch with aws ssm get-parameter --with-decryption)"
}

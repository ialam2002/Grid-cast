output "database_names" {
  value = [
    aws_glue_catalog_database.bronze.name,
    aws_glue_catalog_database.silver.name,
    aws_glue_catalog_database.gold.name,
  ]
}


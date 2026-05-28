locals {
  bucket_names = [
    "${var.project}-${var.environment}-bronze",
    "${var.project}-${var.environment}-silver",
    "${var.project}-${var.environment}-gold",
    "${var.project}-${var.environment}-logs",
  ]
}

resource "aws_s3_bucket" "lake" {
  for_each = toset(local.bucket_names)
  bucket   = each.value

  tags = merge(var.tags, {
    Name = each.value
  })
}

resource "aws_s3_bucket_versioning" "lake" {
  for_each = aws_s3_bucket.lake
  bucket   = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}


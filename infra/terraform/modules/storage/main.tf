locals {
  bucket_names = [
    "${var.project}-${var.environment}-bronze",
    "${var.project}-${var.environment}-silver",
    "${var.project}-${var.environment}-gold",
    "${var.project}-${var.environment}-logs",
  ]

  # Enable lifecycle config when either expiration or versioning cleanup is needed
  enable_lifecycle = var.lifecycle_expiration_days > 0 || var.enable_versioning
}

resource "aws_s3_bucket" "lake" {
  for_each = toset(local.bucket_names)
  bucket   = each.value

  tags = merge(var.tags, {
    Name = each.value
  })
}

# Versioning is SUSPENDED by default to avoid accumulating multiple object
# versions that can quickly exceed the 5 GB S3 free-tier storage limit.
resource "aws_s3_bucket_versioning" "lake" {
  for_each = aws_s3_bucket.lake
  bucket   = each.value.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Lifecycle rules keep storage within free-tier limits:
#   • expire current objects after N days (dev cost guard)
#   • clean up old versions quickly when versioning is on
#   • abort stuck multipart uploads (prevents hidden accumulation)
resource "aws_s3_bucket_lifecycle_configuration" "lake" {
  for_each = local.enable_lifecycle ? aws_s3_bucket.lake : {}
  bucket   = aws_s3_bucket.lake[each.key].id

  rule {
    id     = "free-tier-cost-control"
    status = "Enabled"

    filter {}

    dynamic "expiration" {
      for_each = var.lifecycle_expiration_days > 0 ? [1] : []
      content {
        days = var.lifecycle_expiration_days
      }
    }

    dynamic "noncurrent_version_expiration" {
      for_each = var.enable_versioning ? [1] : []
      content {
        noncurrent_days = var.noncurrent_version_expiration_days
      }
    }

    # Always abort incomplete multipart uploads to avoid stealth storage charges
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

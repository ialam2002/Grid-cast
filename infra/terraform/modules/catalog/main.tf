resource "aws_glue_catalog_database" "bronze" {
  name = "${var.project}_${var.environment}_bronze"
}

resource "aws_glue_catalog_database" "silver" {
  name = "${var.project}_${var.environment}_silver"
}

resource "aws_glue_catalog_database" "gold" {
  name = "${var.project}_${var.environment}_gold"
}


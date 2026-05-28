from pathlib import Path

from gridcast.catalog.ddl_generator import generate_ddl_bundle, infer_athena_type


def test_infer_athena_type_uses_hints() -> None:
    assert infer_athena_type("timestamp_utc") == "timestamp"
    assert infer_athena_type("prediction_mw") == "double"
    assert infer_athena_type("unknown_col") == "string"


def test_generate_ddl_bundle_from_schema_dir() -> None:
    bundle = generate_ddl_bundle(Path("schemas"), s3_root="s3://gridcast-test")
    assert "gold.forecast_hourly.sql" in bundle
    assert "CREATE EXTERNAL TABLE IF NOT EXISTS `gold`.`forecast_hourly`" in bundle["gold.forecast_hourly.sql"]
    assert "LOCATION 's3://gridcast-test/gold/forecast_hourly/'" in bundle["gold.forecast_hourly.sql"]


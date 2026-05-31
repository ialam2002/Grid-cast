CREATE EXTERNAL TABLE IF NOT EXISTS `gold`.`forecast_hourly` (
  `timestamp_utc` timestamp,
  `target_mw` double,
  `prediction_mw` double
)
PARTITIONED BY (
  `horizon_hours` int
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/gold/forecast_hourly/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

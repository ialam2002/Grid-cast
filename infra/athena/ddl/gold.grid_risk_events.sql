CREATE EXTERNAL TABLE IF NOT EXISTS `gold`.`grid_risk_events` (
  `timestamp_utc` timestamp,
  `target_mw` double,
  `prediction_mw` double,
  `abs_error` double
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/gold/grid_risk_events/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

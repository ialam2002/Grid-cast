CREATE EXTERNAL TABLE IF NOT EXISTS `gold`.`forecast_metrics_daily` (
  `run_ts_utc` timestamp,
  `horizon_hours` int,
  `mae` string,
  `rmse` string,
  `mape` string,
  `p90_ae` string
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/gold/forecast_metrics_daily/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

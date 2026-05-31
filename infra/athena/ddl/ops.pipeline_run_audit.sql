CREATE EXTERNAL TABLE IF NOT EXISTS `ops`.`pipeline_run_audit` (
  `job_name` string,
  `status` string,
  `run_ts_utc` timestamp
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/ops/pipeline_run_audit/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

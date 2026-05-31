CREATE EXTERNAL TABLE IF NOT EXISTS `bronze`.`caiso_load_raw` (
  `timestamp_utc` timestamp,
  `load_mw` double
)
PARTITIONED BY (
  `region` string
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/bronze/caiso_load_raw/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

CREATE EXTERNAL TABLE IF NOT EXISTS `bronze`.`eia_region_load_raw` (
  `timestamp_utc` timestamp,
  `demand_mw` double
)
PARTITIONED BY (
  `region` string
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/bronze/eia_region_load_raw/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

CREATE EXTERNAL TABLE IF NOT EXISTS `silver`.`load_weather_hourly` (
  `timestamp_utc` timestamp,
  `load_mw` double,
  `lag_1` double,
  `lag_24` double,
  `lag_168` double,
  `roll_mean_24` double,
  `roll_std_24` double,
  `is_peak_hour` int
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/silver/load_weather_hourly/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

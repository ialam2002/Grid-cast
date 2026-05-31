CREATE EXTERNAL TABLE IF NOT EXISTS `bronze`.`noaa_weather_raw` (
  `timestamp_utc` timestamp
)
STORED AS PARQUET
LOCATION 's3://gridcast-dev-lakehouse/bronze/noaa_weather_raw/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

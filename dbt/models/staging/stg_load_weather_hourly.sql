-- Staging view: standardise all column names and types once at ingestion boundary.
-- Downstream models should never touch the bronze source directly.
select
  cast(timestamp_utc  as timestamp) as timestamp_utc,
  cast(load_mw        as double)    as load_mw,
  cast(lag_1          as double)    as lag_1,
  cast(lag_24         as double)    as lag_24,
  cast(lag_168        as double)    as lag_168,
  cast(roll_mean_24   as double)    as roll_mean_24,
  cast(roll_std_24    as double)    as roll_std_24,
  cast(hour           as int)       as hour,
  cast(day_of_week    as int)       as day_of_week,
  cast(month          as int)       as month,
  cast(is_weekend     as int)       as is_weekend,
  cast(is_peak_hour   as int)       as is_peak_hour
from {{ source('silver', 'load_weather_hourly') }}
where load_mw is not null


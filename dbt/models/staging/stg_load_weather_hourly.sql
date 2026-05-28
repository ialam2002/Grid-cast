select
  timestamp_utc,
  load_mw,
  lag_1,
  lag_24,
  lag_168,
  roll_mean_24,
  roll_std_24,
  hour,
  day_of_week,
  month,
  is_weekend,
  is_peak_hour
from {{ source('silver', 'load_weather_hourly') }}


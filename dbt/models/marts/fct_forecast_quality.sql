with hourly as (
  select
    timestamp_utc,
    horizon_hours,
    target_mw,
    prediction_mw,
    abs(target_mw - prediction_mw) as absolute_error,
    case when target_mw = 0 then null else abs(target_mw - prediction_mw) / target_mw end as ape,
    date(timestamp_utc) as forecast_date
  from {{ source('gold', 'forecast_hourly') }}
)
select
  forecast_date,
  horizon_hours,
  avg(absolute_error) as mae,
  sqrt(avg(power(absolute_error, 2))) as rmse,
  avg(ape) * 100 as mape
from hourly
group by 1, 2


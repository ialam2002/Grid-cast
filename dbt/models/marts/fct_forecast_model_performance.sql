-- fct_forecast_model_performance: rolling 7d and 28d MAPE vs naive baseline.
with daily as (
  select
    date(timestamp_utc) as forecast_date,
    horizon_hours,
    avg(abs(target_mw - prediction_mw)) as mae,
    sqrt(avg(power(target_mw - prediction_mw, 2))) as rmse,
    avg(case when target_mw = 0 then null else abs(target_mw - prediction_mw) / target_mw end) * 100 as mape,
    percentile_approx(abs(target_mw - prediction_mw), 0.90) as p90_absolute_error
  from {{ source('gold', 'forecast_hourly') }}
  group by 1, 2
)
select
  forecast_date,
  horizon_hours,
  mae,
  rmse,
  mape,
  p90_absolute_error,
  avg(mape) over (partition by horizon_hours order by forecast_date rows between 6 preceding and current row) as mape_7d_rolling,
  avg(mape) over (partition by horizon_hours order by forecast_date rows between 27 preceding and current row) as mape_28d_rolling
from daily
order by forecast_date desc, horizon_hours

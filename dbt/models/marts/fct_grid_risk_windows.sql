-- fct_grid_risk_windows: peak-risk windows from last 48h of forecasts.
select
  timestamp_utc,
  target_mw,
  prediction_mw,
  abs(target_mw - prediction_mw) as absolute_error,
  case
    when target_mw = 0 then null
    else abs(target_mw - prediction_mw) / target_mw
  end as ape,
  case
    when abs(target_mw - prediction_mw) / nullif(target_mw, 0) > 0.10 then ''HIGH''
    when abs(target_mw - prediction_mw) / nullif(target_mw, 0) > 0.05 then ''MEDIUM''
    else ''LOW''
  end as risk_level
from {{ source(''gold'', ''forecast_hourly'') }}
where timestamp_utc >= current_timestamp - interval ''48'' hour
order by absolute_error desc

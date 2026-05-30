from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from gridcast.features.build_features import build_hourly_features, make_supervised
from gridcast.modeling.train import evaluate, get_feature_columns, train_gradient_boosting


def test_train_gradient_boosting_returns_metrics() -> None:
    ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    base = pd.DataFrame(
        {
            "timestamp_utc": [ts0 + timedelta(hours=i) for i in range(400)],
            "region": ["CAISO"] * 400,
            "load_mw": [20000 + (i % 24) * 30 + (i % 7) * 15 for i in range(400)],
        }
    )

    feature_df = build_hourly_features(base)
    supervised = make_supervised(feature_df, horizon_hours=24)
    result = train_gradient_boosting(supervised)

    assert "mape" in result.metrics
    assert "smape" in result.metrics
    assert "wmape" in result.metrics
    assert len(result.predictions) > 0


def test_evaluate_handles_near_zero_targets_stably() -> None:
    y_true = np.array([0.0, 0.2, 10.0, 1000.0])
    y_pred = np.array([1.0, 0.1, 8.0, 900.0])

    metrics = evaluate(y_true, y_pred)

    assert metrics["mape"] < 100.0
    assert metrics["smape"] < 100.0
    assert metrics["wmape"] < 100.0


def test_get_feature_columns_includes_weather_numeric_columns() -> None:
    df = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2026-01-01", periods=4, freq="h", tz="UTC"),
            "load_mw": [1.0, 2.0, 3.0, 4.0],
            "target_mw": [2.0, 3.0, 4.0, 5.0],
            "hour": [0, 1, 2, 3],
            "day_of_week": [4, 4, 4, 4],
            "month": [1, 1, 1, 1],
            "is_weekend": [0, 0, 0, 0],
            "is_peak_hour": [0, 0, 0, 0],
            "lag_1": [1.0, 1.1, 1.2, 1.3],
            "lag_24": [1.0, 1.0, 1.0, 1.0],
            "lag_168": [1.0, 1.0, 1.0, 1.0],
            "roll_mean_24": [1.0, 1.1, 1.2, 1.3],
            "roll_std_24": [0.1, 0.1, 0.1, 0.1],
            "hourlydrybulbtemperature": [60.0, 61.0, 62.0, 63.0],
        }
    )

    cols = get_feature_columns(df)
    assert "hourlydrybulbtemperature" in cols



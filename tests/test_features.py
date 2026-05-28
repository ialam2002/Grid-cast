from datetime import datetime, timedelta, timezone

import pandas as pd

from gridcast.features.build_features import build_hourly_features, make_supervised


def test_build_hourly_features_creates_required_columns() -> None:
    ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [{"timestamp_utc": ts0 + timedelta(hours=i), "region": "CAISO", "load_mw": 10000 + i} for i in range(200)]
    df = pd.DataFrame(rows)

    out = build_hourly_features(df)

    for col in ["lag_1", "lag_24", "lag_168", "roll_mean_24", "hour", "is_peak_hour"]:
        assert col in out.columns


def test_make_supervised_drops_trailing_target_nulls() -> None:
    ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    df = pd.DataFrame(
        {
            "timestamp_utc": [ts0 + timedelta(hours=i) for i in range(30)],
            "load_mw": [100 + i for i in range(30)],
        }
    )
    out = make_supervised(df, horizon_hours=24)
    assert "target_mw" in out.columns
    assert len(out) == 6


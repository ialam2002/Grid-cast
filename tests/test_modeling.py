from datetime import datetime, timedelta, timezone

import pandas as pd

from gridcast.features.build_features import build_hourly_features, make_supervised
from gridcast.modeling.train import train_gradient_boosting


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
    assert len(result.predictions) > 0


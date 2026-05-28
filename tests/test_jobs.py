import json
from datetime import datetime, timedelta, timezone

import pandas as pd

from gridcast.features.build_features import build_hourly_features
from gridcast.pipeline.jobs import score_and_publish_forecasts, train_and_evaluate_models


def test_train_and_publish_writes_registry_and_cache(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    silver_dir = data_dir / "silver"
    silver_dir.mkdir(parents=True)
    artifacts_dir = tmp_path / "artifacts"

    monkeypatch.setenv("GRIDCAST_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GRIDCAST_ARTIFACTS_DIR", str(artifacts_dir))

    ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    load_df = pd.DataFrame(
        {
            "timestamp_utc": [ts0 + timedelta(hours=i) for i in range(500)],
            "region": ["CAISO"] * 500,
            "load_mw": [18000 + (i % 24) * 40 + (i % 7) * 20 for i in range(500)],
        }
    )
    silver_df = build_hourly_features(load_df)
    silver_df.to_parquet(silver_dir / "load_weather_hourly.parquet", index=False)

    registry = train_and_evaluate_models(horizons=[24])
    assert "24" in registry
    assert registry["24"]["model_version"]

    payload = score_and_publish_forecasts()
    assert (artifacts_dir / "api_cache.json").exists()
    assert "peak_stress_index" in payload

    cache = json.loads((artifacts_dir / "api_cache.json").read_text(encoding="utf-8"))
    assert "top_drivers" in cache
    assert "model_version" in cache


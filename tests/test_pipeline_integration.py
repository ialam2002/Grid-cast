from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from gridcast.pipeline import jobs


def test_end_to_end_pipeline_with_snapshot_fixtures(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setenv("GRIDCAST_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GRIDCAST_ARTIFACTS_DIR", str(artifacts_dir))
    monkeypatch.setenv("GRIDCAST_NOAA_TOKEN", "test-token")
    monkeypatch.setenv("GRIDCAST_NOAA_STATION_ID", "TEST-STATION")

    fixture_dir = Path("tests") / "fixtures"
    load_fixture = pd.read_csv(fixture_dir / "load_hourly_snapshot.csv")
    load_fixture["timestamp_utc"] = pd.to_datetime(load_fixture["timestamp_utc"], utc=True)

    weather_fixture = pd.read_csv(fixture_dir / "weather_hourly_snapshot.csv")
    weather_fixture["timestamp_utc"] = pd.to_datetime(weather_fixture["timestamp_utc"], utc=True)

    def fake_caiso_fetch(start_utc, end_utc):
        return load_fixture.copy()

    def fake_noaa_fetch(station_id, start_date, end_date, token):
        long_rows = []
        for _, row in weather_fixture.iterrows():
            long_rows.append({"timestamp_utc": row["timestamp_utc"], "datatype": "temperature", "value": row["temperature"]})
            long_rows.append({"timestamp_utc": row["timestamp_utc"], "datatype": "humidity", "value": row["humidity"]})
            long_rows.append({"timestamp_utc": row["timestamp_utc"], "datatype": "wind_speed", "value": row["wind_speed"]})
        return pd.DataFrame(long_rows)

    monkeypatch.setattr(jobs, "fetch_caiso_load", fake_caiso_fetch)
    monkeypatch.setattr(jobs, "fetch_noaa_hourly", fake_noaa_fetch)

    ingest_payload = jobs.ingest_hourly_grid_data(hours=500)
    assert ingest_payload["caiso_rows"] == 500

    silver_payload = jobs.build_silver_features()
    assert silver_payload["silver_rows"] >= 500

    registry = jobs.train_and_evaluate_models(horizons=[24])
    assert "24" in registry
    assert registry["24"]["champion"] in {"hist_gradient_boosting", "seasonal_naive_t24"}

    publish_payload = jobs.score_and_publish_forecasts()
    assert publish_payload["peak_stress_index"] >= 0.0

    api_cache = json.loads((artifacts_dir / "api_cache.json").read_text(encoding="utf-8"))
    assert len(api_cache["next24h_forecast"]) == 24
    assert len(api_cache["risk"]["risk_windows"]) == 3
    assert len(api_cache["top_drivers"]) >= 1


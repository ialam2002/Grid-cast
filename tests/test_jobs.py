import json
from datetime import datetime, timedelta, timezone

import pandas as pd

from gridcast.features.build_features import build_hourly_features
from gridcast.pipeline.jobs import ingest_hourly_grid_data, score_and_publish_forecasts, train_and_evaluate_models


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


def test_ingest_splits_large_caiso_windows(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    artifacts_dir = tmp_path / "artifacts"
    data_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)

    monkeypatch.setenv("GRIDCAST_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GRIDCAST_ARTIFACTS_DIR", str(artifacts_dir))
    monkeypatch.delenv("GRIDCAST_EIA_API_KEY", raising=False)
    monkeypatch.delenv("GRIDCAST_NOAA_TOKEN", raising=False)
    monkeypatch.delenv("GRIDCAST_NOAA_STATION_ID", raising=False)

    fixed_now = datetime(2026, 5, 1, tzinfo=timezone.utc)
    monkeypatch.setattr("gridcast.pipeline.jobs._utc_now", lambda: fixed_now)

    call_ranges: list[tuple[datetime, datetime]] = []

    def _fake_fetch(start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
        call_ranges.append((start_utc, end_utc))
        times = pd.date_range(start_utc, end_utc - timedelta(hours=1), freq="h", tz="UTC")
        return pd.DataFrame(
            {
                "timestamp_utc": times,
                "region": ["CAISO"] * len(times),
                "load_mw": [20000.0] * len(times),
            }
        )

    monkeypatch.setattr("gridcast.pipeline.jobs.fetch_caiso_load", _fake_fetch)

    payload = ingest_hourly_grid_data(hours=24 * 40, caiso_chunk_days=10, caiso_chunk_pause_seconds=0.0)

    assert payload["caiso_chunk_count"] == 4
    assert payload["caiso_chunk_pause_seconds"] == 0.0
    assert len(call_ranges) == 4
    assert (data_dir / "bronze" / "caiso_load_raw.parquet").exists()


def test_ingest_non_strict_records_optional_source_warning(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    artifacts_dir = tmp_path / "artifacts"
    data_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)

    monkeypatch.setenv("GRIDCAST_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GRIDCAST_ARTIFACTS_DIR", str(artifacts_dir))
    monkeypatch.setenv("GRIDCAST_STRICT_INGESTION", "false")
    monkeypatch.setenv("GRIDCAST_NOAA_TOKEN", "dummy")
    monkeypatch.setenv("GRIDCAST_NOAA_STATION_ID", "dummy")
    monkeypatch.delenv("GRIDCAST_EIA_API_KEY", raising=False)

    fixed_now = datetime(2026, 5, 1, tzinfo=timezone.utc)
    monkeypatch.setattr("gridcast.pipeline.jobs._utc_now", lambda: fixed_now)

    def _fake_caiso(start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
        times = pd.date_range(start_utc, end_utc - timedelta(hours=1), freq="h", tz="UTC")
        return pd.DataFrame({"timestamp_utc": times, "region": ["CAISO"] * len(times), "load_mw": [20000.0] * len(times)})

    monkeypatch.setattr("gridcast.pipeline.jobs.fetch_caiso_load", _fake_caiso)
    monkeypatch.setattr("gridcast.pipeline.jobs.fetch_noaa_hourly", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("noaa down")))

    payload = ingest_hourly_grid_data(hours=72, caiso_chunk_days=28, caiso_chunk_pause_seconds=0.0)

    assert "warnings" in payload
    assert any("NOAA ingestion skipped" in w for w in payload["warnings"])



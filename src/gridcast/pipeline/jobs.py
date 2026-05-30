from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

import joblib
import pandas as pd

from gridcast.config import get_settings
from gridcast.data.sources.caiso import fetch_caiso_load
from gridcast.data.sources.eia import fetch_eia_region_load
from gridcast.data.sources.noaa import fetch_noaa_hourly, pivot_noaa_observations
from gridcast.features.build_features import build_hourly_features, make_supervised
from gridcast.modeling.train import segment_metrics, train_gradient_boosting
from gridcast.utils.artifacts import build_model_version, resolve_commit_hash, write_json
from gridcast.utils.contracts import validate_null_thresholds, validate_required_columns


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _schema_hash(df: pd.DataFrame) -> str:
    schema = [{"name": col, "dtype": str(dtype)} for col, dtype in df.dtypes.items()]
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()


def _append_audit(data_dir: Path, job_name: str, status: str, detail: dict) -> None:
    audit_dir = data_dir / "ops"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "pipeline_run_audit.jsonl"
    record = {
        "job_name": job_name,
        "status": status,
        "run_ts_utc": _utc_now().isoformat(),
        "detail": detail,
    }
    with audit_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def _fetch_caiso_load_chunked(
    start_utc: datetime,
    end_utc: datetime,
    chunk_days: int = 28,
    pause_seconds: float = 0.0,
) -> tuple[pd.DataFrame, int]:
    """Fetch CAISO load in bounded windows to avoid OASIS date-range limits."""
    if chunk_days <= 0:
        raise ValueError("chunk_days must be positive")

    frames: list[pd.DataFrame] = []
    window_start = start_utc
    chunk_count = 0

    while window_start < end_utc:
        window_end = min(window_start + timedelta(days=chunk_days), end_utc)
        frames.append(fetch_caiso_load(start_utc=window_start, end_utc=window_end))
        chunk_count += 1
        window_start = window_end
        if pause_seconds > 0 and window_start < end_utc:
            # Gentle pacing lowers the chance of CAISO 429s during long backfills.
            time.sleep(pause_seconds)

    if not frames:
        return pd.DataFrame(columns=["timestamp_utc", "region", "load_mw"]), chunk_count

    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["timestamp_utc", "region"]).sort_values("timestamp_utc").reset_index(drop=True)
    return out, chunk_count


def ingest_hourly_grid_data(
    hours: int = 24 * 90,
    caiso_chunk_days: int = 28,
    caiso_chunk_pause_seconds: float = 0.0,
) -> dict:
    settings = get_settings()
    data_dir = settings.data_dir
    bronze_dir = data_dir / "bronze"
    bronze_dir.mkdir(parents=True, exist_ok=True)

    end_utc = _utc_now().replace(minute=0, second=0, microsecond=0)
    start_utc = end_utc - timedelta(hours=hours)

    caiso_df, caiso_chunk_count = _fetch_caiso_load_chunked(
        start_utc=start_utc,
        end_utc=end_utc,
        chunk_days=caiso_chunk_days,
        pause_seconds=caiso_chunk_pause_seconds,
    )
    validate_required_columns(caiso_df, ["timestamp_utc", "load_mw"], "bronze.caiso_load_raw")
    caiso_path = bronze_dir / "caiso_load_raw.parquet"
    caiso_df.to_parquet(caiso_path, index=False)

    payload: dict[str, object] = {
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
        "caiso_chunk_days": caiso_chunk_days,
        "caiso_chunk_pause_seconds": caiso_chunk_pause_seconds,
        "caiso_chunk_count": caiso_chunk_count,
        "caiso_rows": len(caiso_df),
        "caiso_schema_hash": _schema_hash(caiso_df),
    }
    warnings: list[str] = []

    if settings.eia_api_key:
        try:
            eia_df = fetch_eia_region_load(start_utc=start_utc, end_utc=end_utc, api_key=settings.eia_api_key)
            eia_path = bronze_dir / "eia_region_load_raw.parquet"
            eia_df.to_parquet(eia_path, index=False)
            payload["eia_rows"] = len(eia_df)
            payload["eia_schema_hash"] = _schema_hash(eia_df)
        except Exception as exc:  # noqa: BLE001 - tracked in audit payload
            message = f"EIA ingestion skipped: {exc}"
            if settings.strict_ingestion:
                raise
            warnings.append(message)

    if settings.noaa_token and settings.noaa_station_id:
        try:
            noaa_long = fetch_noaa_hourly(
                station_id=settings.noaa_station_id,
                start_date=start_utc,
                end_date=end_utc,
                token=settings.noaa_token,
            )
            noaa_wide = pivot_noaa_observations(noaa_long)
            noaa_path = bronze_dir / "noaa_weather_raw.parquet"
            noaa_wide.to_parquet(noaa_path, index=False)
            payload["noaa_rows"] = len(noaa_wide)
            payload["noaa_schema_hash"] = _schema_hash(noaa_wide)
        except Exception as exc:  # noqa: BLE001 - tracked in audit payload
            message = f"NOAA ingestion skipped: {exc}"
            if settings.strict_ingestion:
                raise
            warnings.append(message)

    if warnings:
        payload["warnings"] = warnings

    _append_audit(data_dir, "ingest_hourly_grid_data", "success", payload)
    return payload


def build_silver_features() -> dict:
    settings = get_settings()
    data_dir = settings.data_dir
    bronze_dir = data_dir / "bronze"
    silver_dir = data_dir / "silver"
    silver_dir.mkdir(parents=True, exist_ok=True)

    caiso_path = bronze_dir / "caiso_load_raw.parquet"
    if not caiso_path.exists():
        raise FileNotFoundError(f"Missing bronze input: {caiso_path}")

    load_df = pd.read_parquet(caiso_path)
    weather_path = bronze_dir / "noaa_weather_raw.parquet"
    weather_df = pd.read_parquet(weather_path) if weather_path.exists() else None

    silver_df = build_hourly_features(load_df=load_df, weather_df=weather_df)
    validate_required_columns(
        silver_df,
        ["timestamp_utc", "load_mw", "lag_24", "roll_mean_24", "is_peak_hour"],
        "silver.load_weather_hourly",
    )
    contract_result = validate_null_thresholds(
        silver_df,
        {"load_mw": 0.0, "lag_24": 0.1, "roll_mean_24": 0.05},
        "silver.load_weather_hourly",
    )

    out_path = silver_dir / "load_weather_hourly.parquet"
    silver_df.to_parquet(out_path, index=False)

    payload = {
        "silver_rows": len(silver_df),
        "silver_schema_hash": _schema_hash(silver_df),
        "contract": contract_result.__dict__,
    }
    _append_audit(data_dir, "build_silver_features", "success", payload)
    return payload


def train_and_evaluate_models(horizons: list[int] | None = None) -> dict:
    settings = get_settings()
    data_dir = settings.data_dir
    artifacts_dir = settings.artifacts_dir
    silver_path = data_dir / "silver" / "load_weather_hourly.parquet"
    if not silver_path.exists():
        raise FileNotFoundError(f"Missing silver input: {silver_path}")

    silver_df = pd.read_parquet(silver_path)
    horizons = horizons or [1, 24]

    model_dir = artifacts_dir / "models"
    metrics_dir = artifacts_dir / "metrics"
    registry_dir = artifacts_dir / "model_registry"
    predictions_dir = artifacts_dir / "predictions"
    for d in [model_dir, metrics_dir, registry_dir, predictions_dir]:
        d.mkdir(parents=True, exist_ok=True)

    registry: dict[str, dict] = {}
    commit_hash = resolve_commit_hash()

    for horizon in horizons:
        supervised = make_supervised(silver_df, horizon_hours=horizon)
        result = train_gradient_boosting(supervised)

        model_version = build_model_version(horizon)
        model_path = model_dir / f"gbr_{model_version}.joblib"
        joblib.dump(result.model, model_path)

        pred_path = predictions_dir / f"predictions_h{horizon}.parquet"
        result.predictions.assign(horizon_hours=horizon).to_parquet(pred_path, index=False)

        model_wins = result.metrics["mape"] <= result.baseline_metrics["mape"]
        metric_payload = {
            "horizon_hours": horizon,
            "model_name": "hist_gradient_boosting",
            "model_version": model_version,
            "metrics": result.metrics,
            "baseline_metrics": result.baseline_metrics,
            "segment_metrics": segment_metrics(result.predictions),
            "champion": "hist_gradient_boosting" if model_wins else "seasonal_naive_t24",
            "top_drivers": result.top_drivers,
            "data_snapshot": {
                "source_path": str(silver_path),
                "row_count": int(len(silver_df)),
                "min_timestamp": str(pd.to_datetime(silver_df["timestamp_utc"]).min()),
                "max_timestamp": str(pd.to_datetime(silver_df["timestamp_utc"]).max()),
            },
            "commit_hash": commit_hash,
            "created_at_utc": _utc_now().isoformat(),
            "prediction_path": str(pred_path),
            "model_path": str(model_path),
        }
        write_json(metrics_dir / f"metrics_h{horizon}.json", metric_payload)
        registry[str(horizon)] = metric_payload

    write_json(registry_dir / "champion.json", registry)
    _append_audit(data_dir, "train_and_evaluate_models", "success", {"horizons": horizons, "registry": str(registry_dir / 'champion.json')})
    return registry


def score_and_publish_forecasts() -> dict:
    settings = get_settings()
    data_dir = settings.data_dir
    artifacts_dir = settings.artifacts_dir

    registry_path = artifacts_dir / "model_registry" / "champion.json"
    if not registry_path.exists():
        raise FileNotFoundError(f"Missing model registry: {registry_path}")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    h24 = registry.get("24")
    if not h24:
        raise ValueError("Champion registry missing 24-hour horizon entry")

    pred_path = Path(h24["prediction_path"])
    if not pred_path.exists():
        raise FileNotFoundError(f"Missing prediction artifact: {pred_path}")

    forecast_df = pd.read_parquet(pred_path).sort_values("timestamp_utc").tail(24)
    forecast_df["abs_error"] = (forecast_df["target_mw"] - forecast_df["prediction_mw"]).abs()

    risk_windows = forecast_df.sort_values("abs_error", ascending=False).head(3)
    peak_stress_index = float((risk_windows["abs_error"].mean() / forecast_df["target_mw"].mean()) * 100.0)

    gold_dir = data_dir / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)

    forecast_hourly_path = gold_dir / "forecast_hourly.parquet"
    metrics_daily_path = gold_dir / "forecast_metrics_daily.parquet"
    risk_events_path = gold_dir / "grid_risk_events.parquet"

    forecast_df.to_parquet(forecast_hourly_path, index=False)
    pd.DataFrame([h24["metrics"] | {"horizon_hours": 24, "run_ts_utc": _utc_now().isoformat()}]).to_parquet(
        metrics_daily_path,
        index=False,
    )
    risk_windows[["timestamp_utc", "target_mw", "prediction_mw", "abs_error"]].to_parquet(risk_events_path, index=False)

    api_cache = {
        "next24h_forecast": forecast_df.drop(columns=["abs_error"]).to_dict(orient="records"),
        "risk": {
            "peak_stress_index": peak_stress_index,
            "risk_windows": risk_windows[["timestamp_utc", "target_mw", "prediction_mw", "abs_error"]].to_dict(orient="records"),
        },
        "top_drivers": h24["top_drivers"],
        "model_version": h24["model_version"],
        "commit_hash": h24["commit_hash"],
    }
    write_json(artifacts_dir / "api_cache.json", api_cache)

    payload = {
        "forecast_path": str(forecast_hourly_path),
        "metrics_path": str(metrics_daily_path),
        "risk_path": str(risk_events_path),
        "api_cache": str(artifacts_dir / "api_cache.json"),
        "peak_stress_index": peak_stress_index,
    }
    _append_audit(data_dir, "score_and_publish_forecasts", "success", payload)
    return payload


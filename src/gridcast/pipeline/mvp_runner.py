from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gridcast.data.sources.caiso import fetch_caiso_load
from gridcast.features.build_features import build_hourly_features, make_supervised
from gridcast.modeling.train import segment_metrics, train_gradient_boosting


def run(hours: int, horizon: int, output_dir: Path) -> dict:
    end_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start_utc = end_utc - timedelta(hours=hours)

    load_df = fetch_caiso_load(start_utc=start_utc, end_utc=end_utc)
    feature_df = build_hourly_features(load_df)
    supervised = make_supervised(feature_df, horizon_hours=horizon)

    result = train_gradient_boosting(supervised)
    seg = segment_metrics(result.predictions)

    output_dir.mkdir(parents=True, exist_ok=True)
    pred_path = output_dir / "forecast_predictions.parquet"
    metric_path = output_dir / "metrics.json"

    result.predictions.to_parquet(pred_path, index=False)
    metrics_payload = {"overall": result.metrics, "segments": seg, "horizon_hours": horizon}
    metric_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    return {"predictions": str(pred_path), "metrics": str(metric_path), **metrics_payload}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GridCast MVP pipeline")
    parser.add_argument("--hours", type=int, default=24 * 90, help="Historical hours to pull")
    parser.add_argument("--horizon", type=int, default=24, help="Forecast horizon in hours")
    parser.add_argument("--output", default="artifacts", help="Output artifact directory")
    args = parser.parse_args()

    payload = run(hours=args.hours, horizon=args.horizon, output_dir=Path(args.output))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()


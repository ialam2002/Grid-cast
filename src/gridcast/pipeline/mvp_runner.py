from __future__ import annotations

import argparse
import json
from pathlib import Path

from gridcast.config import get_settings
from gridcast.pipeline.jobs import (
    build_silver_features,
    ingest_hourly_grid_data,
    score_and_publish_forecasts,
    train_and_evaluate_models,
)


def run(hours: int, horizon: int, output_dir: Path) -> dict:
    settings = get_settings()
    ingest = ingest_hourly_grid_data(hours=hours)
    silver = build_silver_features()
    registry = train_and_evaluate_models(horizons=[1, horizon])
    publish = score_and_publish_forecasts()

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / "run_bundle.json"
    payload = {
        "ingest": ingest,
        "silver": silver,
        "registry": registry,
        "publish": publish,
        "artifacts_dir": str(settings.artifacts_dir),
        "data_dir": str(settings.data_dir),
    }
    bundle_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {"bundle": str(bundle_path), **payload}


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


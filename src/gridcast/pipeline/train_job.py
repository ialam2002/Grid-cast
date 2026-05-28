from __future__ import annotations

import argparse
import json

from gridcast.pipeline.jobs import train_and_evaluate_models


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate forecasting models")
    parser.add_argument("--horizons", nargs="*", type=int, default=[1, 24], help="Forecast horizons")
    args = parser.parse_args()

    payload = train_and_evaluate_models(horizons=args.horizons)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()


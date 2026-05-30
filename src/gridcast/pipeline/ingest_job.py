from __future__ import annotations

import argparse
import json

from gridcast.pipeline.jobs import ingest_hourly_grid_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest hourly grid data into bronze layer")
    parser.add_argument("--hours", type=int, default=24 * 90, help="Lookback horizon in hours")
    parser.add_argument(
        "--caiso-chunk-days",
        type=int,
        default=28,
        help="Chunk size in days for CAISO API windows (protects multi-month backfills)",
    )
    parser.add_argument(
        "--caiso-chunk-pause-seconds",
        type=float,
        default=1.0,
        help="Pause between chunk calls to reduce CAISO API throttling during long backfills",
    )
    args = parser.parse_args()

    payload = ingest_hourly_grid_data(
        hours=args.hours,
        caiso_chunk_days=args.caiso_chunk_days,
        caiso_chunk_pause_seconds=args.caiso_chunk_pause_seconds,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()


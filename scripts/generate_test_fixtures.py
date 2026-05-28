from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


def main() -> None:
    fixture_dir = Path("tests") / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    load_rows = []
    weather_rows = []
    for i in range(500):
        ts = ts0 + timedelta(hours=i)
        hour = ts.hour
        dow = ts.weekday()

        base = 20000
        diurnal = 1500 if 16 <= hour <= 20 else 600
        weekly = 350 if dow < 5 else -250
        trend = i * 0.8

        load_rows.append(
            {
                "timestamp_utc": ts.isoformat(),
                "region": "CAISO",
                "load_mw": round(base + diurnal + weekly + trend, 2),
            }
        )

        weather_rows.append(
            {
                "timestamp_utc": ts.isoformat(),
                "temperature": round(58 + 18 * (hour / 23.0), 2),
                "humidity": round(65 - 15 * (hour / 23.0), 2),
                "wind_speed": round(5 + (i % 10) * 0.4, 2),
            }
        )

    pd.DataFrame(load_rows).to_csv(fixture_dir / "load_hourly_snapshot.csv", index=False)
    pd.DataFrame(weather_rows).to_csv(fixture_dir / "weather_hourly_snapshot.csv", index=False)
    print(f"Wrote fixtures to {fixture_dir}")


if __name__ == "__main__":
    main()


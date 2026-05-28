from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

NOAA_API_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"


def fetch_noaa_hourly(
    station_id: str,
    start_date: datetime,
    end_date: datetime,
    token: str,
) -> pd.DataFrame:
    """Fetch NOAA hourly observations from CDO API.

    This requires a NOAA token and station with hourly-compatible datasets.
    """
    headers = {"token": token}
    params = {
        "datasetid": "LCD",
        "stationid": station_id,
        "startdate": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "enddate": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "units": "standard",
        "limit": 1000,
    }
    response = requests.get(NOAA_API_URL, headers=headers, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("results", [])
    if not rows:
        return pd.DataFrame(columns=["timestamp_utc", "datatype", "value"])

    df = pd.DataFrame(rows)
    df = df.rename(columns={"date": "timestamp_utc", "datatype": "datatype", "value": "value"})
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    return df[["timestamp_utc", "datatype", "value"]]


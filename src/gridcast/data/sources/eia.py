from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

EIA_REGION_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"


def parse_eia_region_payload(payload: dict, default_region: str = "CAISO") -> pd.DataFrame:
    rows = payload.get("response", {}).get("data", [])
    if not rows:
        return pd.DataFrame(columns=["timestamp_utc", "region", "demand_mw"])

    df = pd.DataFrame(rows)
    value_col = "value" if "value" in df.columns else "demand"
    if value_col not in df.columns:
        raise ValueError(f"Unexpected EIA schema keys: {list(df.columns)}")

    period_col = "period" if "period" in df.columns else "timestamp"
    respondent_col = "respondent" if "respondent" in df.columns else "region"

    out = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(df[period_col], utc=True, errors="coerce"),
            "region": df.get(respondent_col, default_region),
            "demand_mw": pd.to_numeric(df[value_col], errors="coerce"),
        }
    )
    out = out.dropna(subset=["timestamp_utc", "demand_mw"]).sort_values("timestamp_utc")
    return out.reset_index(drop=True)


def fetch_eia_region_load(
    start_utc: datetime,
    end_utc: datetime,
    api_key: str,
    respondent: str = "CISO",
) -> pd.DataFrame:
    params = {
        "api_key": api_key,
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": respondent,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "start": start_utc.strftime("%Y-%m-%dT%H"),
        "end": end_utc.strftime("%Y-%m-%dT%H"),
        "offset": 0,
        "length": 5000,
    }

    response = requests.get(EIA_REGION_URL, params=params, timeout=60)
    response.raise_for_status()
    return parse_eia_region_payload(response.json(), default_region=respondent)


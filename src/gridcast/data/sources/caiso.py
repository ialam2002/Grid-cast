from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import time
from zipfile import ZipFile

import pandas as pd
import requests

CAISO_OASIS_URL = "http://oasis.caiso.com/oasisapi/SingleZip"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _fmt_caiso_timestamp(dt: datetime) -> str:
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime("%Y%m%dT%H:%M-0000")


def _get_caiso_with_backoff(params: dict, timeout: int = 60, max_attempts: int = 5) -> requests.Response:
    last_response: requests.Response | None = None
    for attempt in range(1, max_attempts + 1):
        response = requests.get(CAISO_OASIS_URL, params=params, timeout=timeout)
        if response.status_code not in RETRYABLE_STATUS_CODES:
            response.raise_for_status()
            return response

        last_response = response
        if attempt < max_attempts:
            # Exponential backoff keeps multi-chunk backfills from hammering OASIS.
            sleep_seconds = min(2 ** (attempt - 1), 30)
            time.sleep(sleep_seconds)

    if last_response is not None:
        last_response.raise_for_status()
    raise RuntimeError("CAISO request failed without receiving a response")


def fetch_caiso_load(start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
    """Fetch CAISO hourly load data from OASIS and normalize key fields."""
    params = {
        "resultformat": 6,
        "queryname": "SLD_FCST",
        "version": 1,
        "market_run_id": "ACTUAL",
        "startdatetime": _fmt_caiso_timestamp(start_utc),
        "enddatetime": _fmt_caiso_timestamp(end_utc),
    }
    response = _get_caiso_with_backoff(params=params, timeout=60)

    with ZipFile(BytesIO(response.content)) as zf:
        csv_members = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not csv_members:
            raise ValueError("CAISO response did not include a CSV payload")
        with zf.open(csv_members[0]) as fh:
            df = pd.read_csv(fh)

    cols = {"INTERVALSTARTTIME_GMT": "timestamp_utc", "TAC_AREA_NAME": "region", "MW": "load_mw"}
    available = [c for c in cols if c in df.columns]
    if len(available) < 2:
        raise ValueError(f"Unexpected CAISO schema: {list(df.columns)}")

    out = df.rename(columns=cols)
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], utc=True)
    if "region" not in out.columns:
        out["region"] = "CAISO"
    out = out[["timestamp_utc", "region", "load_mw"]].dropna(subset=["timestamp_utc", "load_mw"])
    out["load_mw"] = pd.to_numeric(out["load_mw"], errors="coerce")
    out = out.dropna(subset=["load_mw"]).sort_values("timestamp_utc")
    return out.reset_index(drop=True)


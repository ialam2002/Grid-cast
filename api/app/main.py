from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException

app = FastAPI(title="GridCast API", version="0.1.0")

ARTIFACTS_DIR = Path("artifacts")
PRED_FILE = ARTIFACTS_DIR / "forecast_predictions.parquet"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/forecast/next24h")
def next_24h_forecast() -> list[dict]:
    if not PRED_FILE.exists():
        raise HTTPException(status_code=404, detail="Forecast artifact not found")
    df = pd.read_parquet(PRED_FILE).sort_values("timestamp_utc").head(24)
    return df.to_dict(orient="records")


@app.get("/risk/peak-stress")
def peak_stress() -> dict:
    if not PRED_FILE.exists():
        raise HTTPException(status_code=404, detail="Forecast artifact not found")

    df = pd.read_parquet(PRED_FILE)
    if df.empty:
        return {"peak_stress_index": 0.0, "risk_windows": []}

    df = df.copy()
    df["abs_error"] = (df["target_mw"] - df["prediction_mw"]).abs()
    risk = df.sort_values("abs_error", ascending=False).head(3)
    peak_stress_index = float((risk["abs_error"].mean() / df["target_mw"].mean()) * 100.0)

    return {
        "peak_stress_index": peak_stress_index,
        "risk_windows": risk[["timestamp_utc", "target_mw", "prediction_mw", "abs_error"]].to_dict(orient="records"),
    }


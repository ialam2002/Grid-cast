from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="GridCast API", version="0.1.0")

ARTIFACTS_DIR = Path("artifacts")
API_CACHE_FILE = ARTIFACTS_DIR / "api_cache.json"


def _load_cache() -> dict:
    if not API_CACHE_FILE.exists():
        raise HTTPException(status_code=404, detail="API cache artifact not found")
    return json.loads(API_CACHE_FILE.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/forecast/next24h")
def next_24h_forecast() -> list[dict]:
    cache = _load_cache()
    return cache.get("next24h_forecast", [])


@app.get("/risk/peak-stress")
def peak_stress() -> dict:
    cache = _load_cache()
    return cache.get("risk", {"peak_stress_index": 0.0, "risk_windows": []})


@app.get("/drivers/top")
def top_drivers() -> dict:
    cache = _load_cache()
    return {
        "top_drivers": cache.get("top_drivers", []),
        "model_version": cache.get("model_version", "unknown"),
        "commit_hash": cache.get("commit_hash", "unknown"),
    }




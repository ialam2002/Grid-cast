from __future__ import annotations

import pandas as pd


def build_hourly_features(load_df: pd.DataFrame, weather_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Create silver-level hourly features from load and optional weather."""
    df = load_df.copy()
    if "timestamp_utc" not in df.columns or "load_mw" not in df.columns:
        raise ValueError("load_df must include timestamp_utc and load_mw")

    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df = df.sort_values("timestamp_utc").reset_index(drop=True)

    if weather_df is not None and not weather_df.empty:
        wx = weather_df.copy()
        wx["timestamp_utc"] = pd.to_datetime(wx["timestamp_utc"], utc=True)
        numeric_weather = [c for c in wx.columns if c not in {"timestamp_utc"}]
        wx = wx.groupby("timestamp_utc", as_index=False)[numeric_weather].mean(numeric_only=True)
        df = df.merge(wx, on="timestamp_utc", how="left")

    df["hour"] = df["timestamp_utc"].dt.hour
    df["day_of_week"] = df["timestamp_utc"].dt.dayofweek
    df["month"] = df["timestamp_utc"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_peak_hour"] = df["hour"].isin([16, 17, 18, 19, 20]).astype(int)

    for lag in [1, 24, 168]:
        df[f"lag_{lag}"] = df["load_mw"].shift(lag)

    df["roll_mean_24"] = df["load_mw"].rolling(window=24, min_periods=1).mean().shift(1)
    df["roll_std_24"] = df["load_mw"].rolling(window=24, min_periods=2).std().shift(1)

    return df


def make_supervised(df: pd.DataFrame, horizon_hours: int) -> pd.DataFrame:
    out = df.copy()
    out["target_mw"] = out["load_mw"].shift(-horizon_hours)
    return out.dropna(subset=["target_mw"])


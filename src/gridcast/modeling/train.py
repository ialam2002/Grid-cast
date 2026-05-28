from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "month",
    "is_weekend",
    "is_peak_hour",
    "lag_1",
    "lag_24",
    "lag_168",
    "roll_mean_24",
    "roll_std_24",
]


@dataclass
class TrainResult:
    model: HistGradientBoostingRegressor
    predictions: pd.DataFrame
    metrics: dict[str, float]


def seasonal_naive_predict(df: pd.DataFrame, horizon_hours: int) -> np.ndarray:
    return df["load_mw"].shift(24).to_numpy()[: len(df) - horizon_hours]


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    yt = y_true[mask]
    yp = y_pred[mask]

    mae = mean_absolute_error(yt, yp)
    rmse = np.sqrt(mean_squared_error(yt, yp))
    mape = np.mean(np.abs((yt - yp) / np.clip(np.abs(yt), 1e-6, None))) * 100.0
    p90_ae = np.percentile(np.abs(yt - yp), 90)
    return {"mae": float(mae), "rmse": float(rmse), "mape": float(mape), "p90_ae": float(p90_ae)}


def train_gradient_boosting(df_supervised: pd.DataFrame, split_ratio: float = 0.8) -> TrainResult:
    model_df = df_supervised.dropna(subset=FEATURE_COLUMNS + ["target_mw"]).copy()
    split_idx = int(len(model_df) * split_ratio)

    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]

    model = HistGradientBoostingRegressor(random_state=42)
    model.fit(train_df[FEATURE_COLUMNS], train_df["target_mw"])

    pred = model.predict(test_df[FEATURE_COLUMNS])
    metrics = evaluate(test_df["target_mw"].to_numpy(), pred)

    predictions = test_df[["timestamp_utc", "target_mw", "is_peak_hour"]].copy()
    predictions["prediction_mw"] = pred
    return TrainResult(model=model, predictions=predictions, metrics=metrics)


def segment_metrics(predictions: pd.DataFrame) -> dict[str, dict[str, float]]:
    out = {}
    for label, seg_df in {
        "peak": predictions[predictions["is_peak_hour"] == 1],
        "offpeak": predictions[predictions["is_peak_hour"] == 0],
    }.items():
        if seg_df.empty:
            out[label] = {"mae": np.nan, "rmse": np.nan, "mape": np.nan, "p90_ae": np.nan}
        else:
            out[label] = evaluate(seg_df["target_mw"].to_numpy(), seg_df["prediction_mw"].to_numpy())
    return out


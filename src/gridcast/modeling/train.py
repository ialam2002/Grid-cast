from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error

BASE_FEATURE_COLUMNS = [
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


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    core = [c for c in BASE_FEATURE_COLUMNS if c in df.columns]
    excluded = set(core + ["timestamp_utc", "target_mw", "load_mw", "region"])
    weather_like = [
        c for c in df.columns if c not in excluded and pd.api.types.is_numeric_dtype(df[c])
    ]
    return core + sorted(weather_like)


@dataclass
class TrainResult:
    model: HistGradientBoostingRegressor
    predictions: pd.DataFrame
    metrics: dict[str, float]
    baseline_metrics: dict[str, float]
    top_drivers: list[dict[str, float]]


def seasonal_naive_predict(df: pd.DataFrame, horizon_hours: int) -> np.ndarray:
    if "lag_24" in df.columns:
        return df["lag_24"].to_numpy()
    return df["load_mw"].shift(24).to_numpy()


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    yt = y_true[mask]
    yp = y_pred[mask]

    if len(yt) == 0:
        return {
            "mae": np.nan,
            "rmse": np.nan,
            "mape": np.nan,
            "smape": np.nan,
            "wmape": np.nan,
            "p90_ae": np.nan,
        }

    mae = mean_absolute_error(yt, yp)
    rmse = np.sqrt(mean_squared_error(yt, yp))
    abs_error = np.abs(yt - yp)
    denom_floor = max(1000.0, float(np.nanpercentile(np.abs(yt), 5)))
    mape = np.mean(abs_error / np.clip(np.abs(yt), denom_floor, None)) * 100.0
    smape = np.mean((2.0 * abs_error) / np.clip(np.abs(yt) + np.abs(yp), denom_floor, None)) * 100.0
    wmape = (np.sum(abs_error) / np.clip(np.sum(np.abs(yt)), denom_floor, None)) * 100.0
    p90_ae = np.percentile(np.abs(yt - yp), 90)
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape),
        "smape": float(smape),
        "wmape": float(wmape),
        "p90_ae": float(p90_ae),
    }


def train_gradient_boosting(df_supervised: pd.DataFrame, split_ratio: float = 0.8) -> TrainResult:
    feature_columns = get_feature_columns(df_supervised)
    model_df = df_supervised.dropna(subset=feature_columns + ["target_mw"]).copy()
    split_idx = int(len(model_df) * split_ratio)
    if split_idx <= 0 or split_idx >= len(model_df):
        raise ValueError("Not enough rows to perform time-based train/test split")

    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]

    model = HistGradientBoostingRegressor(random_state=42)
    model.fit(train_df[feature_columns], train_df["target_mw"])

    pred = model.predict(test_df[feature_columns])
    metrics = evaluate(test_df["target_mw"].to_numpy(), pred)
    baseline_pred = seasonal_naive_predict(test_df, horizon_hours=24)
    baseline_metrics = evaluate(test_df["target_mw"].to_numpy(), baseline_pred)

    importances = permutation_importance(
        model,
        test_df[feature_columns],
        test_df["target_mw"],
        n_repeats=5,
        random_state=42,
        scoring="neg_mean_absolute_error",
    )
    top_idx = np.argsort(importances.importances_mean)[::-1][:5]
    top_drivers = [
        {
            "feature": feature_columns[idx],
            "importance": float(importances.importances_mean[idx]),
        }
        for idx in top_idx
    ]

    predictions = test_df[["timestamp_utc", "target_mw", "is_peak_hour"]].copy()
    predictions["prediction_mw"] = pred
    predictions["baseline_prediction_mw"] = baseline_pred
    return TrainResult(
        model=model,
        predictions=predictions,
        metrics=metrics,
        baseline_metrics=baseline_metrics,
        top_drivers=top_drivers,
    )


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


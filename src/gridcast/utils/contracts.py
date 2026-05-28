from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ContractResult:
    table_name: str
    row_count: int
    null_ratio: dict[str, float]


def validate_required_columns(df: pd.DataFrame, required_columns: list[str], table_name: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{table_name} missing required columns: {missing}")


def validate_null_thresholds(
    df: pd.DataFrame,
    thresholds: dict[str, float],
    table_name: str,
) -> ContractResult:
    null_ratio: dict[str, float] = {}
    for column, threshold in thresholds.items():
        ratio = float(df[column].isna().mean()) if len(df) > 0 else 1.0
        null_ratio[column] = ratio
        if ratio > threshold:
            raise ValueError(
                f"{table_name} column '{column}' null ratio {ratio:.4f} exceeds threshold {threshold:.4f}"
            )
    return ContractResult(table_name=table_name, row_count=len(df), null_ratio=null_ratio)


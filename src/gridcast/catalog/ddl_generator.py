from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class TableSpec:
    database: str
    table: str
    required_columns: list[str]
    partition_keys: list[str]


TYPE_HINTS: dict[str, str] = {
    "timestamp_utc": "timestamp",
    "run_ts_utc": "timestamp",
    "date": "date",
    "region": "string",
    "horizon_hours": "int",
    "is_peak_hour": "int",
    "is_weekend": "int",
    "hour": "int",
    "day_of_week": "int",
    "month": "int",
}


def infer_athena_type(column_name: str) -> str:
    if column_name in TYPE_HINTS:
        return TYPE_HINTS[column_name]
    if column_name.endswith("_mw") or column_name.endswith("_error"):
        return "double"
    if column_name.startswith("lag_") or column_name.startswith("roll_"):
        return "double"
    return "string"


def parse_schema_file(path: Path) -> list[TableSpec]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    tables = payload.get("tables", {})
    specs: list[TableSpec] = []
    for full_name, table_def in tables.items():
        database, table = full_name.split(".", 1)
        specs.append(
            TableSpec(
                database=database,
                table=table,
                required_columns=list(table_def.get("required_columns", [])),
                partition_keys=list(table_def.get("partition_keys", [])),
            )
        )
    return specs


def render_create_table_sql(spec: TableSpec, s3_root: str) -> str:
    column_defs: list[str] = []
    partition_defs: list[str] = []

    for col in spec.required_columns:
        dtype = infer_athena_type(col)
        if col in spec.partition_keys:
            partition_defs.append(f"  `{col}` {dtype}")
        else:
            column_defs.append(f"  `{col}` {dtype}")

    if not column_defs:
        column_defs.append("  `record_payload` string")

    partition_block = ""
    if partition_defs:
        partition_block = "\nPARTITIONED BY (\n" + ",\n".join(partition_defs) + "\n)"

    location = f"{s3_root.rstrip('/')}/{spec.database}/{spec.table}/"
    return (
        f"CREATE EXTERNAL TABLE IF NOT EXISTS `{spec.database}`.`{spec.table}` (\n"
        + ",\n".join(column_defs)
        + "\n)"
        + partition_block
        + "\nSTORED AS PARQUET\n"
        + f"LOCATION '{location}'\n"
        + "TBLPROPERTIES ('parquet.compress'='SNAPPY');\n"
    )


def generate_ddl_bundle(schema_dir: Path, s3_root: str) -> dict[str, str]:
    output: dict[str, str] = {}
    for path in sorted(schema_dir.glob("*.yml")):
        for spec in parse_schema_file(path):
            key = f"{spec.database}.{spec.table}.sql"
            output[key] = render_create_table_sql(spec, s3_root=s3_root)
    return output


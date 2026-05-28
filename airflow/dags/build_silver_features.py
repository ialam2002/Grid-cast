from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def build_silver() -> None:
    print("Run Spark transform, schema checks, and write silver table")


with DAG(
    dag_id="build_silver_features",
    start_date=datetime(2026, 1, 1),
    schedule="15 * * * *",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=10)},
    tags=["gridcast", "silver"],
):
    build_task = PythonOperator(task_id="spark_transform_and_contracts", python_callable=build_silver)


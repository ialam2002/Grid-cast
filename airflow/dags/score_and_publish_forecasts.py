from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def score_publish_notify() -> None:
    print("Score next horizons, compute risk indicators, publish gold + API cache")


with DAG(
    dag_id="score_and_publish_forecasts",
    start_date=datetime(2026, 1, 1),
    schedule="5 * * * *",
    catchup=False,
    tags=["gridcast", "serving"],
):
    score_task = PythonOperator(task_id="score_publish_report", python_callable=score_publish_notify)


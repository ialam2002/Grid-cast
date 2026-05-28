from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def build_silver() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "src")
    subprocess.run([sys.executable, "-m", "gridcast.pipeline.silver_job"], check=True, env=env)


with DAG(
    dag_id="build_silver_features",
    start_date=datetime(2026, 1, 1),
    schedule="15 * * * *",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=10)},
    tags=["gridcast", "silver"],
):
    build_task = PythonOperator(task_id="spark_transform_and_contracts", python_callable=build_silver)


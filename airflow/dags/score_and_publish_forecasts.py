from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def score_publish_notify() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "src")
    subprocess.run([sys.executable, "-m", "gridcast.pipeline.score_job"], check=True, env=env)


with DAG(
    dag_id="score_and_publish_forecasts",
    start_date=datetime(2026, 1, 1),
    schedule="5 * * * *",
    catchup=False,
    tags=["gridcast", "serving"],
):
    score_task = PythonOperator(task_id="score_publish_report", python_callable=score_publish_notify)


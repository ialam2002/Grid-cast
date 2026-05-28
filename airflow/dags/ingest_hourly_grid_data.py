from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def pull_and_land_sources() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "src")
    subprocess.run(
        [sys.executable, "-m", "gridcast.pipeline.ingest_job", "--hours", "2160"],
        check=True,
        env=env,
    )


with DAG(
    dag_id="ingest_hourly_grid_data",
    start_date=datetime(2026, 1, 1),
    schedule="0 * * * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["gridcast", "ingest"],
):
    ingest_task = PythonOperator(task_id="pull_validate_land", python_callable=pull_and_land_sources)


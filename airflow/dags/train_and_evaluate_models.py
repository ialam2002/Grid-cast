from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def train_models() -> None:
    print("Train candidate models and register champion by horizon metrics")


with DAG(
    dag_id="train_and_evaluate_models",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    tags=["gridcast", "modeling"],
):
    train_task = PythonOperator(task_id="train_compare_register", python_callable=train_models)


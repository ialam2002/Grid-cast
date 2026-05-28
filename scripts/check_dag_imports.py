from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


class _DummyDAG:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _DummyPythonOperator:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs


def _install_airflow_stubs() -> None:
    airflow = types.ModuleType("airflow")
    airflow.DAG = _DummyDAG

    operators = types.ModuleType("airflow.operators")
    operators_python = types.ModuleType("airflow.operators.python")
    operators_python.PythonOperator = _DummyPythonOperator

    sys.modules["airflow"] = airflow
    sys.modules["airflow.operators"] = operators
    sys.modules["airflow.operators.python"] = operators_python


def _import_module(path: Path) -> None:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load DAG module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


def main() -> None:
    _install_airflow_stubs()

    dag_dir = Path("airflow") / "dags"
    py_files = sorted(dag_dir.glob("*.py"))
    if not py_files:
        raise RuntimeError("No DAG files found")

    for path in py_files:
        _import_module(path)
        print(f"Imported DAG module: {path}")


if __name__ == "__main__":
    main()


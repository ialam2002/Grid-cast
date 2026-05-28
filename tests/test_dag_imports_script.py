from pathlib import Path
import subprocess
import sys


def test_dag_import_script_runs() -> None:
    script = Path("scripts") / "check_dag_imports.py"
    result = subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True)
    assert "Imported DAG module" in result.stdout


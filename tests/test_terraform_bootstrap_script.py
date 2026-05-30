from pathlib import Path

import pytest

from scripts.bootstrap_terraform_env import write_terraform_env_files


def test_write_terraform_env_files_creates_expected_outputs(tmp_path: Path) -> None:
    backend_path, tfvars_path = write_terraform_env_files(
        repo_root=tmp_path,
        project="gridcast",
        env="dev",
        account_id="111122223333",
        region="us-west-2",
        lock_table="gridcast-tf-locks",
        force=False,
    )

    assert backend_path.exists()
    assert tfvars_path.exists()

    backend = backend_path.read_text(encoding="utf-8")
    tfvars = tfvars_path.read_text(encoding="utf-8")
    assert 'bucket         = "gridcast-tfstate-dev"' in backend
    assert 'assume_role_arn  = "arn:aws:iam::111122223333:role/gridcast-dev-terraform"' in tfvars


def test_write_terraform_env_files_requires_force_for_existing_files(tmp_path: Path) -> None:
    write_terraform_env_files(
        repo_root=tmp_path,
        project="gridcast",
        env="stage",
        account_id="111122223333",
        region="us-west-2",
        lock_table="gridcast-tf-locks",
        force=False,
    )

    with pytest.raises(FileExistsError):
        write_terraform_env_files(
            repo_root=tmp_path,
            project="gridcast",
            env="stage",
            account_id="111122223333",
            region="us-west-2",
            lock_table="gridcast-tf-locks",
            force=False,
        )


from __future__ import annotations

import argparse
from pathlib import Path


VALID_ENVS = {"dev", "stage", "prod"}


def build_backend_hcl(*, project: str, env: str, region: str, lock_table: str) -> str:
    return (
        f'bucket         = "{project}-tfstate-{env}"\n'
        f'key            = "{project}/{env}/terraform.tfstate"\n'
        f'region         = "{region}"\n'
        "encrypt        = true\n"
        "use_lockfile   = true\n"
    )


def build_tfvars(*, project: str, env: str, account_id: str, region: str, lock_table: str, assume_role_arn: str) -> str:
    return (
        f'aws_region       = "{region}"\n'
        f'assume_role_arn  = "{assume_role_arn}"\n'
        f'state_bucket     = "{project}-tfstate-{env}"\n'
        f'state_lock_table = "{lock_table}"\n'
        f'state_key_prefix = "{project}"\n'
    )


def write_terraform_env_files(
    *,
    repo_root: Path,
    project: str,
    env: str,
    account_id: str,
    region: str,
    lock_table: str,
    assume_role_arn: str,
    force: bool,
) -> tuple[Path, Path]:
    env_dir = repo_root / "infra" / "terraform" / "env" / env
    env_dir.mkdir(parents=True, exist_ok=True)

    backend_path = env_dir / "backend.hcl"
    tfvars_path = env_dir / "terraform.tfvars"

    if not force and (backend_path.exists() or tfvars_path.exists()):
        raise FileExistsError(
            "Terraform env files already exist. Use --force to overwrite existing backend.hcl/terraform.tfvars."
        )

    backend_path.write_text(
        build_backend_hcl(project=project, env=env, region=region, lock_table=lock_table),
        encoding="utf-8",
    )
    tfvars_path.write_text(
        build_tfvars(
            project=project,
            env=env,
            account_id=account_id,
            region=region,
            lock_table=lock_table,
            assume_role_arn=assume_role_arn,
        ),
        encoding="utf-8",
    )
    return backend_path, tfvars_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap Terraform backend.hcl and terraform.tfvars for one GridCast environment")
    parser.add_argument("--env", required=True, choices=sorted(VALID_ENVS), help="Environment name")
    parser.add_argument("--account-id", required=True, help="AWS account ID for the environment")
    parser.add_argument("--region", default="us-east-2", help="AWS region")
    parser.add_argument("--project", default="gridcast", help="Project slug used in bucket/key names")
    parser.add_argument("--lock-table", default="gridcast-tf-locks", help="DynamoDB lock table for Terraform state")
    parser.add_argument(
        "--assume-role-arn",
        default="",
        help="Optional IAM role ARN for Terraform to assume. Leave empty when running directly as your configured IAM user.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backend_path, tfvars_path = write_terraform_env_files(
        repo_root=Path(args.repo_root).resolve(),
        project=args.project,
        env=args.env,
        account_id=args.account_id,
        region=args.region,
        lock_table=args.lock_table,
        assume_role_arn=args.assume_role_arn,
        force=args.force,
    )

    print(f"Wrote {backend_path}")
    print(f"Wrote {tfvars_path}")


if __name__ == "__main__":
    main()


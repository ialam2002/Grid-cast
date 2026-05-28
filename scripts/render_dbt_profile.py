from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    # Resolve correct source template: profiles.yml.example ships in VCS,
    # profiles.yml is git-ignored and generated at runtime.
    source_path = Path("dbt") / "profiles" / "profiles.yml.example"
    target_path = Path("dbt") / "profiles" / "profiles.yml"

    if not source_path.exists():
        raise FileNotFoundError(f"Profile template not found: {source_path}")

    if target_path.exists() and os.getenv("GRIDCAST_OVERWRITE_DBT_PROFILE", "false").lower() != "true":
        print(f"Skipping write: {target_path} already exists. Set GRIDCAST_OVERWRITE_DBT_PROFILE=true to force.")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {target_path}")


if __name__ == "__main__":
    main()


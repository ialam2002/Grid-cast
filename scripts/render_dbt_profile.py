from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    source_path = Path("dbt") / "profiles" / "profiles.yml.example"
    target_path = Path("dbt") / "profiles" / "profiles.yml"

    if target_path.exists() and os.getenv("GRIDCAST_OVERWRITE_DBT_PROFILE", "false").lower() != "true":
        print(f"Skipping write because {target_path} already exists")
        return

    target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {target_path}")


if __name__ == "__main__":
    main()


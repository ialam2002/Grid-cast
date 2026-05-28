from __future__ import annotations

import argparse
from pathlib import Path

from gridcast.catalog.ddl_generator import generate_ddl_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Athena DDL files from schema contracts")
    parser.add_argument("--schema-dir", default="schemas", help="Path to schema yaml directory")
    parser.add_argument("--output-dir", default="infra/athena/ddl", help="Output directory for SQL files")
    parser.add_argument(
        "--s3-root",
        default="s3://gridcast-dev-lakehouse",
        help="S3 root where table data is stored",
    )
    args = parser.parse_args()

    schema_dir = Path(args.schema_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ddl_bundle = generate_ddl_bundle(schema_dir=schema_dir, s3_root=args.s3_root)
    for file_name, sql in ddl_bundle.items():
        (output_dir / file_name).write_text(sql, encoding="utf-8")

    print(f"Generated {len(ddl_bundle)} Athena DDL files in {output_dir}")


if __name__ == "__main__":
    main()


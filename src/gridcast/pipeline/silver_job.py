from __future__ import annotations

import json

from gridcast.pipeline.jobs import build_silver_features


def main() -> None:
    payload = build_silver_features()
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()


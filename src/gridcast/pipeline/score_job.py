from __future__ import annotations

import json

from gridcast.pipeline.jobs import score_and_publish_forecasts


def main() -> None:
    payload = score_and_publish_forecasts()
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()


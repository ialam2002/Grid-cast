from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    region: str
    noaa_token: str | None
    eia_api_key: str | None
    noaa_station_id: str | None
    data_dir: Path
    artifacts_dir: Path
    strict_ingestion: bool


def get_settings() -> Settings:
    return Settings(
        region=os.getenv("GRIDCAST_REGION", "CAISO"),
        noaa_token=os.getenv("GRIDCAST_NOAA_TOKEN"),
        eia_api_key=os.getenv("GRIDCAST_EIA_API_KEY"),
        noaa_station_id=os.getenv("GRIDCAST_NOAA_STATION_ID"),
        data_dir=Path(os.getenv("GRIDCAST_DATA_DIR", "data")),
        artifacts_dir=Path(os.getenv("GRIDCAST_ARTIFACTS_DIR", "artifacts")),
        strict_ingestion=os.getenv("GRIDCAST_STRICT_INGESTION", "true").lower() == "true",
    )


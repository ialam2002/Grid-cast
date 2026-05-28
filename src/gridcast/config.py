from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    region: str = os.getenv("GRIDCAST_REGION", "CAISO")
    noaa_token: str | None = os.getenv("GRIDCAST_NOAA_TOKEN")
    eia_api_key: str | None = os.getenv("GRIDCAST_EIA_API_KEY")


def get_settings() -> Settings:
    return Settings()


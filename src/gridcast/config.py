from dataclasses import dataclass
import os
from pathlib import Path


def _get_secret_from_ssm(parameter_name: str, region: str = "us-east-2") -> str | None:
    """Fetch a secret from AWS SSM Parameter Store. Returns None if not found or boto3 unavailable."""
    try:
        import boto3
        client = boto3.client("ssm", region_name=region)
        response = client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except Exception:
        # boto3 not available, not in AWS, or parameter not found
        return None


def _get_from_env_or_ssm(env_var: str, ssm_param: str | None = None, environment: str = "dev") -> str | None:
    """
    Try to get a secret from environment first, then SSM Parameter Store.
    
    Args:
        env_var: Environment variable name (e.g., "GRIDCAST_EIA_API_KEY")
        ssm_param: SSM parameter name (e.g., "eia-api-key"). If None, will use env_var as-is.
        environment: AWS environment (dev/stage/prod) for SSM path
    
    Returns:
        Secret value or None if not found
    """
    # Try local environment first (for dev)
    value = os.getenv(env_var)
    if value:
        return value
    
    # Try SSM Parameter Store (for cloud)
    if ssm_param:
        param_name = f"/gridcast/{environment}/{ssm_param}"
        ssm_value = _get_secret_from_ssm(param_name)
        if ssm_value:
            return ssm_value
    
    return None


@dataclass(frozen=True)
class Settings:
    region: str
    noaa_token: str | None
    eia_api_key: str | None
    noaa_station_id: str | None
    data_dir: Path
    artifacts_dir: Path
    strict_ingestion: bool
    aws_region: str  # AWS region for cloud operations
    s3_data_bucket: str | None  # Optional S3 bucket for data storage (e.g., gridcast-dev-bronze)


def get_settings() -> Settings:
    environment = os.getenv("GRIDCAST_ENVIRONMENT", "dev")
    aws_region = os.getenv("GRIDCAST_AWS_REGION", "us-east-2")
    
    return Settings(
        region=os.getenv("GRIDCAST_REGION", "CAISO"),
        noaa_token=_get_from_env_or_ssm("GRIDCAST_NOAA_TOKEN", "noaa-token", environment),
        eia_api_key=_get_from_env_or_ssm("GRIDCAST_EIA_API_KEY", "eia-api-key", environment),
        noaa_station_id=os.getenv("GRIDCAST_NOAA_STATION_ID"),
        data_dir=Path(os.getenv("GRIDCAST_DATA_DIR", "data")),
        artifacts_dir=Path(os.getenv("GRIDCAST_ARTIFACTS_DIR", "artifacts")),
        strict_ingestion=os.getenv("GRIDCAST_STRICT_INGESTION", "false").lower() == "true",
        aws_region=aws_region,
        s3_data_bucket=os.getenv("GRIDCAST_S3_DATA_BUCKET"),
    )


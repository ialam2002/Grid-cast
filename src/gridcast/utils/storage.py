"""Cloud storage abstraction for GridCast data pipeline."""
from __future__ import annotations

from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def write_parquet_to_s3(df, s3_path: str, region: str = "us-east-2") -> bool:
    """
    Write a pandas DataFrame to S3 as parquet.
    
    Args:
        df: pandas DataFrame to write
        s3_path: S3 path in format "s3://bucket-name/prefix/file.parquet"
        region: AWS region for S3
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import pyarrow.parquet as pq
        import pyarrow as pa
        import boto3
        
        # Parse S3 path
        if not s3_path.startswith("s3://"):
            logger.error(f"Invalid S3 path: {s3_path}")
            return False
        
        parts = s3_path[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        # Convert to Arrow table and write to S3
        table = pa.Table.from_pandas(df)
        bytes_buffer = pa.BufferOutputStream()
        pq.write_table(table, bytes_buffer)
        
        # Upload to S3
        s3_client = boto3.client("s3", region_name=region)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=bytes_buffer.getvalue().to_pybytes(),
            ContentType="application/octet-stream",
        )
        
        logger.info(f"Successfully wrote {len(df)} rows to {s3_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write to S3 {s3_path}: {e}")
        return False


def read_parquet_from_s3(s3_path: str, region: str = "us-east-2"):
    """
    Read a parquet file from S3 into a pandas DataFrame.
    
    Args:
        s3_path: S3 path in format "s3://bucket-name/prefix/file.parquet"
        region: AWS region for S3
    
    Returns:
        pandas DataFrame or None if read failed
    """
    try:
        import pandas as pd
        
        df = pd.read_parquet(s3_path)
        logger.info(f"Successfully read {len(df)} rows from {s3_path}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to read from S3 {s3_path}: {e}")
        return None


def ensure_local_dir(path: Path) -> Path:
    """Ensure a local directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path


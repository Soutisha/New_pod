import os
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET = os.getenv("S3_BUCKET")

# Lazily initialise the client so missing creds don't crash on import
_s3_client = None


def _get_s3():
    """Return a cached boto3 S3 client, or raise a clear error if creds are missing."""
    global _s3_client
    if _s3_client is None:
        if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, BUCKET]):
            raise RuntimeError(
                "S3 is not configured. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, "
                "AWS_REGION, and S3_BUCKET in your .env file."
            )
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
        )
    return _s3_client


def upload_file(local_path: str, s3_key: str) -> bool:
    """Upload a local file to S3. Returns True on success, False on failure."""
    try:
        _get_s3().upload_file(Filename=local_path, Bucket=BUCKET, Key=s3_key)
        print(f"✅ S3 upload OK: {s3_key}")
        return True
    except Exception as e:
        print(f"⚠️  S3 upload_file failed for {s3_key}: {e}")
        return False


def upload_text(content: str, s3_key: str) -> bool:
    """Upload a text string to S3. Returns True on success, False on failure."""
    try:
        _get_s3().put_object(Bucket=BUCKET, Key=s3_key, Body=content.encode("utf-8"))
        print(f"✅ S3 upload OK: {s3_key}")
        return True
    except Exception as e:
        print(f"⚠️  S3 upload_text failed for {s3_key}: {e}")
        return False


def download_text(s3_key: str) -> str:
    """Download text from S3. Returns empty string on failure."""
    try:
        obj = _get_s3().get_object(Bucket=BUCKET, Key=s3_key)
        return obj["Body"].read().decode("utf-8")
    except Exception as e:
        print(f"⚠️  S3 download_text failed for {s3_key}: {e}")
        return ""


def list_files(prefix: str) -> list:
    """List S3 keys under a prefix. Returns empty list on failure."""
    try:
        resp = _get_s3().list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        if "Contents" not in resp:
            return []
        return [item["Key"] for item in resp["Contents"]]
    except Exception as e:
        print(f"⚠️  S3 list_files failed for prefix '{prefix}': {e}")
        return []
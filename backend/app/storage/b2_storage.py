"""Backblaze B2 via its S3-compatible API (free 10 GB, no card at signup per Backblaze)."""
from functools import wraps
from urllib.parse import urlparse

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from ..config import Config
from .interface import ObjectNotFound, ProviderError, StorageProvider


def _region(endpoint: str) -> str:
    parts = (urlparse(endpoint).hostname or "").split(".")  # s3.us-west-004.backblazeb2.com
    return parts[1] if len(parts) > 2 and parts[0] == "s3" else "us-west-004"


def _translate(fn):
    @wraps(fn)
    def wrapper(self, *a, **kw):
        try:
            return fn(self, *a, **kw)
        except ProviderError:
            raise
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                raise ObjectNotFound("File not found in Backblaze B2.") from e
            if code in ("InvalidAccessKeyId", "SignatureDoesNotMatch", "AccessDenied", "403", "InvalidAccessKey"):
                raise ProviderError("Backblaze B2 rejected the credentials or permissions.") from e
            raise ProviderError("Backblaze B2 returned an error.") from e
        except (BotoCoreError, OSError) as e:
            raise ProviderError("Backblaze B2 is unreachable or timed out.") from e

    return wrapper


class B2Storage(StorageProvider):
    name, label = "b2", "Backblaze B2"

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not (Config.B2_ENDPOINT_URL and Config.B2_KEY_ID and Config.B2_APPLICATION_KEY and Config.B2_BUCKET_NAME):
                raise ProviderError("Backblaze B2 credentials are not configured.")
            self._client = boto3.client(
                "s3",
                endpoint_url=Config.B2_ENDPOINT_URL,
                region_name=_region(Config.B2_ENDPOINT_URL),
                aws_access_key_id=Config.B2_KEY_ID,
                aws_secret_access_key=Config.B2_APPLICATION_KEY,
                config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"},
                                  connect_timeout=5, read_timeout=30, retries={"max_attempts": 3, "mode": "standard"}),
            )
        return self._client

    @_translate
    def upload(self, key, data, content_type):
        self.client.put_object(Bucket=Config.B2_BUCKET_NAME, Key=key, Body=data, ContentType=content_type)

    @_translate
    def download(self, key):
        return self.client.get_object(Bucket=Config.B2_BUCKET_NAME, Key=key)["Body"].read()

    @_translate
    def delete(self, key):
        self.client.delete_object(Bucket=Config.B2_BUCKET_NAME, Key=key)

    @_translate
    def exists(self, key):
        try:
            self.client.head_object(Bucket=Config.B2_BUCKET_NAME, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    @_translate
    def get_metadata(self, key):
        h = self.client.head_object(Bucket=Config.B2_BUCKET_NAME, Key=key)
        return {"size": h["ContentLength"], "etag": h["ETag"].strip('"'), "last_modified": h["LastModified"],
                "content_type": h.get("ContentType")}

    def health(self):
        try:
            self.client.head_bucket(Bucket=Config.B2_BUCKET_NAME)
            return True
        except Exception:
            return False

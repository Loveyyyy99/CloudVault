import os


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


class Config:
    # Free-tier safety limits
    MAX_FILE_SIZE = _int("MAX_FILE_SIZE", 25 * 1024 * 1024)
    MAX_TOTAL_STORAGE = _int("MAX_TOTAL_STORAGE", 1024 * 1024 * 1024)
    MAX_DAILY_UPLOADS = _int("MAX_DAILY_UPLOADS", 20)
    ALLOWED_EXTENSIONS = {
        e.strip().lower()
        for e in os.getenv(
            "ALLOWED_EXTENSIONS",
            "pdf,txt,md,csv,json,zip,png,jpg,jpeg,gif,docx,xlsx,pptx,pt,pkl,ipynb",
        ).split(",")
    }
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]

    # Provider 1: Backblaze B2 (S3-compatible API)
    B2_ENDPOINT_URL = os.getenv("B2_ENDPOINT_URL")  # e.g. https://s3.us-west-004.backblazeb2.com
    B2_KEY_ID = os.getenv("B2_KEY_ID")
    B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
    B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")

    # Provider 2: Supabase Storage (private bucket, accessed with the service-role key — backend only)
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "cloudvault")

    SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

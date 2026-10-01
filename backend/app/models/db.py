from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from ..config import Config


@contextmanager
def cursor():
    """Short-lived connection per operation (works with Supabase's pooler and serverless hosts)."""
    conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor, connect_timeout=8)
    try:
        with conn:  # commits on success, rolls back on error
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()

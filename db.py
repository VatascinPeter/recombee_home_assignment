import os
from psycopg2 import pool
from contextlib import contextmanager


conn_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=16,
    dsn=os.environ["DATABASE_URL"]
)

@contextmanager
def get_cursor():
    """Context manager for getting a cursor to a PostgreSQL database"""
    conn = conn_pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn_pool.putconn(conn)

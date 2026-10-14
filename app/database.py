from contextlib import contextmanager
from pathlib import Path
import pymysql
from pymysql.cursors import DictCursor


@contextmanager
def connection(settings):
    conn = pymysql.connect(
        host=settings.mysql_host, port=settings.mysql_port,
        user=settings.mysql_user, password=settings.mysql_password,
        database=settings.mysql_database, charset="utf8mb4",
        cursorclass=DictCursor, autocommit=False,
        connect_timeout=5, read_timeout=30, write_timeout=30,
    )
    try:
        yield conn
    finally:
        conn.close()


def initialize(settings):
    schema = (Path(__file__).resolve().parents[1] / "sql/schema.sql").read_text()
    with connection(settings) as conn:
        with conn.cursor() as cur:
            for statement in schema.split(";"):
                if statement.strip():
                    cur.execute(statement)
        conn.commit()


class MySQLRepository:
    def __init__(self, settings):
        self.settings = settings

    def candidates(self, name, limit=50):
        # Name and alias lookup both retain place IDs and all homonyms.
        sql = """SELECT p.*,
          CASE WHEN p.name = %s THEN 'name' ELSE 'alias' END AS matched_by
          FROM places p
          WHERE p.name = %s OR EXISTS (
            SELECT 1 FROM place_aliases a WHERE a.place_id = p.id AND a.alias = %s)
          ORDER BY p.id LIMIT %s"""
        with connection(self.settings) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name, name, name, limit + 1))
                rows = list(cur.fetchall())
        return rows[:limit], len(rows) > limit

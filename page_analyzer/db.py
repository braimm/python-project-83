import psycopg2
from psycopg2 import extras
from psycopg2.extensions import connection
import datetime
from typing import Callable
from .exceptions import Custom_exception_db
from typing import Any, Optional, NamedTuple


def catch_exceptions_psycopg2(func: Callable) -> Callable:
    def wrapper(*args, **kwargs) -> Callable | None:
        try:
            return func(*args, **kwargs)
        except psycopg2.DatabaseError:
            raise Custom_exception_db
    return wrapper


@catch_exceptions_psycopg2
def connect_db(db_url: str) -> connection:
    connection = psycopg2.connect(db_url)
    return connection


@catch_exceptions_psycopg2
def get_urls_list(conn: connection) -> list[dict]:
    with conn.cursor(cursor_factory=extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                id,
                name
            FROM urls
            ORDER BY urls.id DESC;
        """)
        urls = cur.fetchall()

        cur.execute("""
                SELECT
                    url_id,
                    MAX(created_at),
                    status_code
                FROM url_checks
                GROUP BY url_id, status_code;
        """)
        checks = cur.fetchall()

        urls_with_checks: list = []
        check_found: extras.DictRow | dict= {}
        for url in urls:
            for check in checks:
                if url['id'] == check['url_id']:
                    check_found = check
            if check_found:
                urls_with_checks += {**url, **check_found},
                check_found = {}
            else:
                urls_with_checks += {**url},
    return urls_with_checks


@catch_exceptions_psycopg2
def get_url_info(id: int, conn: connection) -> \
                tuple[Optional[NamedTuple], list[NamedTuple]]:

    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cur.fetchone()
        cur.execute("""
            SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;
        """, (id,))

        checks = cur.fetchall()
    return url, checks


@catch_exceptions_psycopg2
def get_url_by_name(url: str, conn: connection) -> \
                Optional[NamedTuple]:

    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE name = %s;", (url,))
        result = cur.fetchone()
    return result


@catch_exceptions_psycopg2
def add_url(url: str, conn: connection) -> int | None:
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        date = datetime.datetime.now().date()
        cur.execute("""
            INSERT INTO urls (name, created_at)
            VALUES (%s, %s) RETURNING id;
        """, (url, date))

        record = cur.fetchone()
    return record.id if record else None


@catch_exceptions_psycopg2
def get_url_by_id(id: int, conn: connection) -> NamedTuple | None:
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cur.fetchone()
    return url


@catch_exceptions_psycopg2
def add_url_check(
                    id: int,
                    data_check:
                    tuple[str, str, str, int],
                    conn: connection) -> None:

    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        h1, title, descr, status_code = data_check
        date = datetime.datetime.now().date()
        cur.execute("""
            INSERT INTO url_checks
            (url_id, status_code, h1, title, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (id, status_code, h1, title, descr, date))

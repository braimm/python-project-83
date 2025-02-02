import psycopg2
from psycopg2 import extras
import datetime
from .html import get_page_info


def connect_db(db_url):
    connection = psycopg2.connect(db_url)
    return connection


def get_urls_list(conn):
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("""
            SELECT
                urls.id,
                urls.name,
                MAX(url_checks.created_at),
                url_checks.status_code
            FROM urls
            LEFT JOIN url_checks ON urls.id = url_checks.url_id
            GROUP BY urls.id, urls.name, url_checks.status_code
            ORDER BY urls.id DESC;
        """)

        urls = cur.fetchall()
    return urls


def get_url_info(id, conn):
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cur.fetchone()
        cur.execute("""
            SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;
        """, (id,))

        checks = cur.fetchall()
    return url, checks


def get_url_by_name(url, conn):
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE name = %s;", (url,))
        result = cur.fetchone()
    return result


def add_url(url, conn):
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        record = get_url_by_name(url, conn)
        if record is None:
            date = datetime.datetime.now().date()
            cur.execute("""
                INSERT INTO urls (name, created_at)
                VALUES (%s, %s) RETURNING id;
            """, (url, date))

            id = cur.fetchone()[0]
            status = "added"
        else:
            status = "exists"
            id = record[0]
    return status, id


def get_url_by_id(id, conn):
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cur.fetchone()
    return url


def add_url_check(id, conn):
    with connect_db() as conn:
        with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
            url = get_url_by_id(id, conn)
            h1, title, descr, status_code = get_page_info(url)
            date = datetime.datetime.now().date()
            cur.execute("""
                INSERT INTO url_checks
                (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (id, status_code, h1, title, descr, date))

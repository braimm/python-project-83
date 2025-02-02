import psycopg2
from psycopg2 import extras
import datetime
from .html import get_page_info


def connect_db(db_url):
    connection = psycopg2.connect(db_url)
    return connection


def get_urls_list(conn):
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

        urls_with_checks = []
        check_found = {}
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
        date = datetime.datetime.now().date()
        cur.execute("""
            INSERT INTO urls (name, created_at)
            VALUES (%s, %s) RETURNING id;
        """, (url, date))

        id = cur.fetchone()[0]
    return id


def get_url_by_id(id, conn):
    with conn.cursor(cursor_factory=extras.NamedTupleCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cur.fetchone()
    return url


def add_url_check(id, conn):
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

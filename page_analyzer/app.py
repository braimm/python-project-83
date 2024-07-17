from flask import Flask, render_template
from flask import request, url_for, redirect, flash, get_flashed_messages
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import extras
import validators
from urllib import parse
import datetime
from bs4 import BeautifulSoup
import requests


app = Flask(__name__)
load_dotenv(override=True)
app.secret_key = os.getenv('SECRET_KEY')


def connect_db():
    DATABASE_URL = os.getenv('DATABASE_URL')
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor(cursor_factory=extras.NamedTupleCursor)
    return connection, cursor


def show_page_errors_db():
    errors = 'Ошибка при работе с базой данных'
    return render_template('errors.html', errors=errors)


def close_connection_db(cursor, connection):
    cursor.close()
    connection.close()


def validate_url(url):
    if validators.url(url) is not True:
        flash('Некорректный URL', 'danger')
        return True
    if len(url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return True
    return False


def get_norm_url(url):
    result = parse.urlparse(url)
    return f'{result.scheme}://{result.netloc}'


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_list():
    try:
        connection, cursor = connect_db()
        cursor.execute("""
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
        urls = cursor.fetchall()
    except Exception:
        show_page_errors_db()
    finally:
        close_connection_db(cursor, connection)

    return render_template('urls.html', urls=urls)


@app.post('/urls')
def add_url():
    url = request.form.get('url')
    errors = validate_url(url)
    if errors:
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', url=url, messages=messages), 422
    url = get_norm_url(url)
    date = datetime.datetime.now().date()
    try:
        connection, cursor = connect_db()
        cursor.execute("SELECT * FROM urls WHERE name = %s;", (url,))
        record = cursor.fetchone()
        if record is None:
            cursor.execute("""
                INSERT INTO urls (name, created_at)
                VALUES (%s, %s) RETURNING id;
            """, (url, date))
            id = cursor.fetchone()[0]
            connection.commit()
            flash('Страница успешно добавлена', 'success')
        else:
            flash('Страница уже существует', 'info')
            id = record[0]
    except Exception:
        show_page_errors_db()
    finally:
        close_connection_db(cursor, connection)
    return redirect(url_for('url_page', id=id), 302)


@app.route('/urls/<id>')
def url_page(id):
    try:
        connection, cursor = connect_db()
        cursor.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cursor.fetchone()
        cursor.execute("""
            SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;
        """, (id,))
        checks = cursor.fetchall()
    except Exception:
        show_page_errors_db()
    finally:
        close_connection_db(cursor, connection)
    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html',
                           messages=messages,
                           url=url,
                           checks=checks)


@app.post('/urls/<id>/checks')
def url_check(id):
    date = datetime.datetime.now().date()
    try:
        connection, cursor = connect_db()
        cursor.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cursor.fetchone()

        response = requests.get(url.name, timeout=2)
        response.raise_for_status()
        status_code = response.status_code

        content = response.text
        soup = BeautifulSoup(content, 'html.parser')

        h1 = soup.h1.text if soup.h1 else ''
        title = soup.title.text if soup.title.text else ''
        descr = soup.find(
            "meta", attrs={'name': 'description'}).get('content', '')

        cursor.execute("""
            INSERT INTO url_checks
            (url_id, status_code, h1, title, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (id, status_code, h1, title, descr, date))
        connection.commit()
        flash('Страница успешно проверена', 'success')

    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_page', id=id), 302)
    except Exception:
        show_page_errors_db()
    finally:
        close_connection_db(cursor, connection)
    return redirect(url_for('url_page', id=id), 302)

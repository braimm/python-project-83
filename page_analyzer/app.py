from flask import Flask, render_template, request, url_for, redirect, flash, get_flashed_messages
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
#app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.secret_key = "secret_key"

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
def urls():
    DATABASE_URL = 'postgresql://dbuser:pass123@localhost:5432/pa_db'         
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=extras.NamedTupleCursor)
    #cursor.execute("SELECT * FROM urls")
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
    print(urls)
    return render_template('urls.html', urls=urls)


@app.post('/urls')
def add_urls():
    load_dotenv()
    #DATABASE_URL = 'postgresql://postgres:pass123@localhost:5432/pa_db'
    DATABASE_URL = 'postgresql://dbuser:pass123@localhost:5432/pa_db'
    #DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    url = request.form.get('url')
    errors = validate_url(url)
    if errors:
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', url=url, messages=messages)
    url = get_norm_url(url)
    date = datetime.datetime.now().date()
    cursor = conn.cursor(cursor_factory=extras.NamedTupleCursor)
    cursor.execute("SELECT * FROM urls WHERE name = %s;", (url,))
    record = cursor.fetchone()
    if record is None:
        cursor.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;", (url, date))
        id = cursor.fetchone()[0]
        conn.commit()
        flash('Страница успешно добавлена', 'success')
    else:
        flash('Страница уже существует', 'info')
        id = record[0]
    cursor.close()
    conn.close()    
    return redirect(url_for('url', id=id))


@app.route('/urls/<id>')
def url(id):
    load_dotenv()
    #DATABASE_URL = 'postgresql://postgres:pass123@localhost:5432/pa_db'
    DATABASE_URL = 'postgresql://dbuser:pass123@localhost:5432/pa_db'
    #DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=extras.NamedTupleCursor)
    cursor.execute("SELECT * FROM urls WHERE id = %s;", (id,))
    url = cursor.fetchone()
    cursor.execute("SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;", (id,))
    checks = cursor.fetchall()
    print(checks)
    messages = get_flashed_messages(with_categories=True)
    conn.commit()
    cursor.close()
    conn.close()
    return render_template('url.html', messages=messages, url=url, checks=checks)


@app.post('/urls/<id>/checks')
def url_check(id):
    load_dotenv()
    #DATABASE_URL = 'postgresql://postgres:pass123@localhost:5432/pa_db'
    DATABASE_URL = 'postgresql://dbuser:pass123@localhost:5432/pa_db'
    #DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=extras.NamedTupleCursor)
    date = datetime.datetime.now().date()
    cursor.execute("INSERT INTO url_checks (url_id, created_at) VALUES (%s, %s) RETURNING id;", (id, date))
    #id_check = cursor.fetchone()[0]
    conn.commit()
    flash('Страница успешно проверена', 'success')
    cursor.close()
    conn.close()

    #flash('Произошла ошибка при проверке', 'danger')
    return redirect(url_for('url', id=id), 302)


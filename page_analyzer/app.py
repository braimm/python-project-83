from flask import Flask, render_template, request, url_for, redirect, flash, get_flashed_messages
from dotenv import load_dotenv
import os
import psycopg2
import validators
from urllib import parse
import datetime


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
    return render_template('urls.html')


@app.post('/urls')
def add_urls():
    load_dotenv()
    DATABASE_URL = 'postgresql://postgres:pass123@localhost:5432/pa_db'
    #DATABASE_URL = 'postgresql://dbuser:pass123@localhost:5432/pa_db'
    #DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    print(conn)
    url = request.form.get('url')
    errors = validate_url(url)
    if errors:
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', url=url, messages=messages)
    url = get_norm_url(url)
    date = datetime.datetime.now().date()
    cursor = conn.cursor()
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
    DATABASE_URL = 'postgresql://postgres:pass123@localhost:5432/pa_db'
    #DATABASE_URL = 'postgresql://dbuser:pass123@localhost:5432/pa_db'
    #DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM urls WHERE id = %s;", (id,))
    url = cursor.fetchone()
    messages = get_flashed_messages(with_categories=True)
    conn.commit()
    cursor.close()
    conn.close()
    return render_template('url.html', messages=messages, url=url)
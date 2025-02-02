from flask import Flask, render_template
from flask import request, url_for, redirect, flash, get_flashed_messages
from dotenv import load_dotenv
import os
from .db import get_urls_list, connect_db, get_url_info, add_url, add_url_check
from .html import show_page_errors_db
from .validators import validate_url, get_norm_url
import requests


app = Flask(__name__)
load_dotenv(override=True)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_list():
    try:
        with connect_db(DATABASE_URL) as conn:
            urls = get_urls_list(conn)
    except Exception:
        show_page_errors_db()
    return render_template('urls.html', urls=urls)


@app.post('/urls')
def adding_url():
    url = request.form.get('url')
    errors = validate_url(url)
    if errors:
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', url=url, messages=messages), 422

    url = get_norm_url(url)

    try:
        with connect_db(DATABASE_URL) as conn:
            status, id = add_url(url, conn)
            match status:
                case 'added':
                    flash('Страница успешно добавлена', 'success')
                case 'exists':
                    flash('Страница уже существует', 'info')
    except Exception:
        show_page_errors_db()
    return redirect(url_for('url_page', id=id), 302)


@app.get('/urls/<id>')
def url_page(id):
    try:
        with connect_db(DATABASE_URL) as conn:
            url, checks = get_url_info(id, conn)
    except Exception:
        show_page_errors_db()
    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html',
                           messages=messages,
                           url=url,
                           checks=checks)


@app.post('/urls/<id>/checks')
def url_check(id):
    try:
        with connect_db(DATABASE_URL) as conn:
            add_url_check(id, conn)
            flash('Страница успешно проверена', 'success')
    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_page', id=id), 302)
    except Exception:
        show_page_errors_db()
    return redirect(url_for('url_page', id=id), 302)

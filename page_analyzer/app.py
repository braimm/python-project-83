from flask import Flask, render_template
from flask import request, url_for, redirect, flash, get_flashed_messages
from werkzeug.wrappers.response import Response
from dotenv import load_dotenv
import os
from .db import get_url_info, add_url, add_url_check
from .db import get_urls_list, connect_db, get_url_by_name, get_url_by_id
from .html import get_data_check
from .validators import get_errors_validate_url, get_norm_url, prepare_write_db
from .exceptions import Custom_exception_db
from typing import Union
# import logging


app = Flask(__name__)
load_dotenv(override=True)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
# logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="w",
#                     format="%(asctime)s %(levelname)s %(message)s")


@app.get('/')
def index() -> str:
    return render_template('index.html')


@app.get('/errors')
def errors_page() -> str:
    messages = get_flashed_messages(with_categories=True)
    return render_template('errors.html', messages=messages)


@app.get('/urls')
def urls_list() -> Union[str, Response]:
    try:
        with connect_db(DATABASE_URL) as conn:
            urls = get_urls_list(conn)
    except Custom_exception_db:
        flash('Произошла ошибка', 'danger')
        return redirect(url_for('errors'), 302)
    return render_template('urls.html', urls=urls)


@app.post('/urls')
def adding_url() -> Union[str, Response] | Union[tuple[str, int], Response]:
    # url = request.form.get('url')
    # if url is not None:
    #     errors = get_errors_validate_url(url)
    # if errors or url is None:
    #     match errors:
    #         case 'bad_url':
    #             flash('Некорректный URL', 'danger')
    #         case 'long_url':
    #             flash('URL превышает 255 символов', 'danger')
    #         case _:
    #             pass
    #     messages = get_flashed_messages(with_categories=True)
    #     return render_template('index.html', url=url, messages=messages), 422
    url = request.form.get('url')
    errors = get_errors_validate_url(url)
    if errors:
        match errors:
            case 'bad_url':
                flash('Некорректный URL', 'danger')
            case 'long_url':
                flash('URL превышает 255 символов', 'danger')
            case _:
                pass
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', url=url, messages=messages), 422
    url = get_norm_url(url)

    try:
        with connect_db(DATABASE_URL) as conn:
            record = get_url_by_name(url, conn)
            if record:
                id = record.id
                flash('Страница уже существует', 'info')
            else:
                record = add_url(url, conn)
                if record.id is None:
                    raise Custom_exception_db
                flash('Страница успешно добавлена', 'success')
    except Custom_exception_db:
        flash('Произошла ошибка', 'danger')
        return redirect(url_for('errors'), 302)
    return redirect(url_for('url_page', id=id), 302)


@app.get('/urls/<id>')
def url_page(id: int) -> Union[str, Response]:
    try:
        with connect_db(DATABASE_URL) as conn:
            url, checks = get_url_info(id, conn)
        messages = get_flashed_messages(with_categories=True)
    except Custom_exception_db:
        flash('Произошла ошибка', 'danger')
        return redirect(url_for('errors'), 302)
    return render_template('url.html',
                           messages=messages,
                           url=url,
                           checks=checks)


@app.post('/urls/<id>/checks')
def url_check(id: int) -> Union[str, Response]:
    try:
        with connect_db(DATABASE_URL) as conn:
            url = get_url_by_id(id, conn)
            data_check = get_data_check(url)
            if data_check is None:
                flash('Произошла ошибка при проверке', 'danger')
                return redirect(url_for('url_page', id=id), 302)
            data_check = prepare_write_db(data_check)
            add_url_check(id, data_check, conn)
            flash('Страница успешно проверена', 'success')
    except Custom_exception_db:
        flash('Произошла ошибка', 'danger')
        return redirect(url_for('errors'), 302)
    return redirect(url_for('url_page', id=id), 302)

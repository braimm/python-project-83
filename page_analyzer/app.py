from flask import Flask, render_template, request, url_for, redirect, flash, get_flashed_messages
from dotenv import load_dotenv
import os
import psycopg2
import validators.url
import urllib.parse
import datetime



load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


app = Flask(__name__)
#app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.secret_key = "secret_key"


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls():
    return render_template('urls.html')


@app.post('/urls')
def add_urls():
    url  = request.form.get('url')
    errors = validators.url(url)
    flash('This is a message', 'success')
    return redirect(url_for('url', id=1))


@app.route('/urls/<id>')
def url(id):
    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html', messages=messages)
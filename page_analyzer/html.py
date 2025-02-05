from flask import render_template
import requests
from bs4 import BeautifulSoup


def show_page_errors_db():
    errors = 'Ошибка при работе с базой данных'
    return render_template('errors.html', errors=errors)


def get_data_check(url):
    page_requested = requests.get(url.name, timeout=2)
    page_requested.raise_for_status()
    status_code = page_requested.status_code

    content = page_requested.text
    soup = BeautifulSoup(content, 'html.parser')

    h1 = soup.h1.text if soup.h1 else ''
    title = soup.title.text if soup.title.text else ''
    descr = soup.find(
        "meta", attrs={'name': 'description'}).get('content', '')
    return (h1, title, descr, status_code)

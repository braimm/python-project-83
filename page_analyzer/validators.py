import validators
from flask import flash
from urllib import parse


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

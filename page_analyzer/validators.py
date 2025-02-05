import validators
from urllib import parse


def get_errors_validate_url(url):
    if validators.url(url) is not True:
        return 'bad_url'
    if len(url) > 255:
        return 'long_url'
    return None


def get_norm_url(url):
    result = parse.urlparse(url)
    return f'{result.scheme}://{result.netloc}'

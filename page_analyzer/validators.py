import validators
from urllib import parse


def get_errors_validate_url(url: str) -> str | None:
    if validators.url(url) is not True:
        return 'bad_url'
    if len(url) > 255:
        return 'long_url'
    return None


def get_norm_url(url: str) -> str:
    result = parse.urlparse(url)
    return f'{result.scheme}://{result.netloc}'


def prepare_write_db(data_check: tuple[str, str, str, int]) -> \
                    tuple[str, str, str, int]:

    h1, title, descr, status_code = data_check
    h1 = str(h1)[:255]
    title = str(title)[:255]
    descr = str(descr)[:255]
    status_code = int(status_code)
    return (h1, title, descr, status_code)

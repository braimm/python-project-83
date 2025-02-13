import requests
from bs4 import BeautifulSoup, Tag
from .my_types import Url_record_NTuple


def get_data_check(url: Url_record_NTuple) -> tuple[str, str, str, int] | None:
    try:
        page_requested = requests.get(url.name, timeout=2)
        page_requested.raise_for_status()
        status_code = page_requested.status_code

        content = page_requested.text
        soup = BeautifulSoup(content, 'html.parser')

        h1 = soup.h1.text if soup.h1 else ''
        title = soup.title.text if soup.title else ''

        descr = soup.find("meta", attrs={"name": "description"})
        descr_content = descr.get('content', '') \
            if descr and type(descr) is Tag else ''

        descr_result = str(descr_content)
    except (requests.RequestException, ValueError):
        return None
    return (h1, title, descr_result, status_code)

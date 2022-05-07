from typing import Union
from urllib.parse import urlunparse, urlparse

from yarl import URL


def clean_url(url: Union[str, URL]) -> str:
    return urlunparse(urlparse(str(url)))
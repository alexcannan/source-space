from dataclasses import dataclass
import hashlib
from typing import Union
from urllib.parse import urlunparse, urlparse

from bson import ObjectId
from yarl import URL


@dataclass
class Article:
    url: str
    title: str
    text: str
    authors: list[str]
    links: list[str]

    @property
    def mongoId(self) -> ObjectId:
        return ObjectId()

    @property
    def urlHash(self) -> str:
        return hashlib.sha256(self.url.encode('utf-8')).hexdigest()

    @property
    def textHash(self) -> str:
        return hashlib.sha512(self.text.encode('utf-8')).hexdigest()

    @property
    def hits(self) -> int:
        return -1

    @property
    def allParents(self) -> set['Article']:
        return set()

    @property
    def allChildren(self) -> set['Article']:
        return set()

    def to_mongo_dict(self) -> dict:
        return {
            'url': self.url,
            'urlHash': self.urlHash,
            'title': self.title,
            'text': self.text,
            'textHash': self.textHash,
            'authors': self.authors,
            'links': self.links,
            'hits': self.hits,
        }

    @classmethod
    def fromUrl(url: str) -> 'Article':
        pass


def clean_url(url: Union[str, URL]) -> str:
    """ parse article urls, remove query strings and fragments """
    _parsed = urlparse(str(url))
    _parsed = _parsed._replace(query='', fragment='')
    return urlunparse(_parsed)

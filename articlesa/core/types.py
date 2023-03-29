from dataclasses import dataclass, field
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
        if hasattr(self, '_id'):
            return self._id
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

    @staticmethod
    def get_fields() -> list[str]:
        return ['url', 'title', 'text', 'authors', 'links']

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
    def from_mongo_dict(cls, data: dict) -> 'Article':
        c = cls(
            url=data['url'],
            title=data['title'],
            text=data['text'],
            authors=data['authors'],
            links=data['links'],
        )
        c._id = data['_id']
        return c


@dataclass
class SourceNode(Article):
    depth: int
    status: str = '🐲'
    transientId: str = ObjectId()

    @classmethod
    def from_db_article(cls, dbarticle: dict, depth: int) -> 'SourceNode':
        article = Article.from_mongo_dict(dbarticle)
        return cls(
            url=article.url,
            title=article.title,
            text=article.text,
            authors=article.authors,
            links=article.links,
            depth=depth,
        )


@dataclass
class Link:
    source: SourceNode
    target: SourceNode
    internal: bool


@dataclass
class SourceTree:
    root: SourceNode
    nodes: list[SourceNode] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)

    def __post_init__(self):
        self.nodes.append(self.root)

    def compose_mermaid(self):
        return f"""hi"""


def clean_url(url: Union[str, URL]) -> str:
    """ parse article urls, remove query strings and fragments """
    _parsed = urlparse(str(url))
    _parsed = _parsed._replace(query='', fragment='')
    return urlunparse(_parsed)

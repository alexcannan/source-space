from collections import defaultdict
from dataclasses import dataclass, field
import hashlib
from textwrap import indent
from typing import Union
from urllib.parse import urlunparse, urlparse

from bson import ObjectId
from yarl import URL


class Blacklist:
    def __init__(self):
        with open('blacklist.txt') as f:
            self.blacklist = [line.strip() for line in f.readlines()]

    def __contains__(self, url: str) -> bool:
        X = urlparse(url).netloc.split(".")
        for badurl in self.blacklist:
            A = badurl.split(".")
            for i in range(len(X) - len(A) + 1):
                if A == X[i:i+len(A)]:
                    return True
        return False


blacklist = Blacklist()


@dataclass(kw_only=True)
class Article:
    url: str
    title: str
    authors: list[str]
    links: list[str]
    text: str = ''

    @property
    def mongoId(self) -> ObjectId:
        if hasattr(self, '_id'):
            return self._id
        return ObjectId()

    @property
    def domain(self) -> str:
        return urlparse(self.url).netloc

    @property
    def urlHash(self) -> str:
        return hashlib.sha256(self.url.encode('utf-8')).hexdigest()

    @property
    def textHash(self) -> str:
        if not self.text:
            raise ValueError("text not set")
        return hashlib.sha512(self.text.encode('utf-8')).hexdigest()

    @property
    def hits(self) -> int:
        return -1

    def make_links(self) -> list['Link']:
        linklist = []
        for target in self.links:
            if target not in blacklist:
                if target.startswith('/'):
                    target = urlunparse(urlparse(self.url)._replace(path=target))
                    internal = True
                else:
                    internal = False
                linklist.append(Link(source=self.url, target=target, internal=internal))
        return linklist

    def make_children(self) -> list['Article']:
        return [Article(url=link.target, title='', authors=[]) for link in self.make_links()]

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
    parsed: bool = False
    status: str = '🐲'
    transientId: str = ObjectId()

    def make_mermaid(self) -> str:
        """ generates a string to place inside mermaid node representing this SourceNode """
        content = "\n".join([
            self.title,
            f'<a href="{self.url}">{self.domain}</a>',
            self.status,
            self.hits
        ])
        return f'{self.transientId}[{content}]'

    @classmethod
    def from_article(cls, article: Article, depth: int) -> 'SourceNode':
        return cls(
            url=article.url,
            title=article.title,
            text=article.text,
            authors=article.authors,
            links=article.links,
            depth=depth,
        )

    @classmethod
    def from_db_article(cls, dbarticle: dict, depth: int) -> 'SourceNode':
        article = Article.from_mongo_dict(dbarticle)
        return cls.from_article(article, depth)


@dataclass
class Link:
    source: SourceNode
    target: SourceNode
    internal: bool
    transientId: str = ObjectId()

    def make_mermaid(self) -> str:
        """ generates a string to place inside mermaid link representing this Link """
        return f'{self.source.transientId} --> {self.target.transientId}'


@dataclass
class SourceTree:
    root: SourceNode
    nodes: list[SourceNode] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)

    def __post_init__(self):
        self.nodes.append(self.root)

    def add_node(self, node: SourceNode):
        self.nodes.append(node)

    def add_link(self, link: Link):
        self.links.append(link)

    def update_node(self, node: SourceNode):
        # update Article information but leave SourceNode information
        for i, n in enumerate(self.nodes):
            if n.url == node.url:
                depth, parsed, status, transientId = n.depth, n.parsed, n.status, n.transientId
                self.nodes[i] = node
                self.nodes[i].depth = depth
                self.nodes[i].parsed = parsed
                self.nodes[i].status = status
                self.nodes[i].transientId = transientId
                return
        raise ValueError(f"node {node.url} not found")

    def is_complete(self, depth: int) -> bool:
        return all(node.depth >= depth or node.parsed for node in self.nodes)

    def nodes_in_progress(self) -> list[SourceNode]:
        return [node for node in self.nodes if not node.parsed]

    def compose_mermaid(self):
        indentation = '  '
        depth_dict = defaultdict(list)
        for node in self.nodes:
            depth_dict[node.depth].append(node)
        subgraphs = []
        for depth, nodes in depth_dict.items():
            subgraphs.append("\n".join(
                f'subgraph TD {depth}',
                indent("\n".join(node.make_mermaid() for node in nodes), indentation),
                'end'
            ))
        return "\n".join(
            'graph LR',
            indent("\n".join(subgraphs), indentation),
            indent("\n".join(link.make_mermaid() for link in self.links), indentation),
            'end'
        )


def clean_url(url: Union[str, URL]) -> str:
    """ parse article urls, remove query strings and fragments """
    _parsed = urlparse(str(url))
    _parsed = _parsed._replace(query='', fragment='')
    return urlunparse(_parsed)

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from textwrap import indent
from typing import Optional, Union
from urllib.parse import urlunparse, urlparse

from bson import ObjectId
from yarl import URL

from articlesa.logger import logger


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
    published: Optional[str] = None
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
        return [Article(url=link.target, title='', authors=[], links=[]) for link in self.make_links()]

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
    status: str = 'cool dragon'
    transientId: str = None

    def __post_init__(self):
        self.transientId = str(ObjectId())

    def make_mermaid(self) -> str:
        """ generates a string to place inside mermaid node representing this SourceNode """
        content = "<br/>".join([
            '"'+self.title+'"',
            f"<a href='{self.url}'>{self.domain}</a>",
            self.status,
            f'hits: {self.hits}',
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
    source: SourceNode | str
    target: SourceNode | str
    internal: bool
    transientId: str = ObjectId()

    def make_mermaid(self, urlmap: dict[str, ObjectId]) -> str:
        """ generates a string to place inside mermaid link representing this Link """
        _from = urlmap[self.source] if isinstance(self.source, str) else self.source.transientId
        _to = urlmap[self.target] if isinstance(self.target, str) else self.target.transientId
        return f'{_from} -{".-" if self.internal else "-"}> {_to}'


@dataclass
class SourceTree:
    root: SourceNode
    nodes: list[SourceNode] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)

    def __post_init__(self):
        self.nodes.append(self.root)

    @property
    def node_urls(self) -> set:
        return {node.url for node in self.nodes}

    def add_node(self, node: SourceNode):
        if node.url not in self.node_urls:
            self.nodes.append(node)

    def add_link(self, link: Link):
        self.links.append(link)

    def update_node(self, node: SourceNode):
        # update Article information but leave SourceNode information
        for i, n in enumerate(self.nodes):
            if n.url == node.url:
                parsed, status, transientId = n.parsed, n.status, n.transientId
                self.nodes[i] = node
                self.nodes[i].parsed = parsed
                self.nodes[i].status = status
                self.nodes[i].transientId = transientId
                return
        raise ValueError(f"node {node.url} not found")

    def is_complete(self, depth: int) -> bool:
        return all(node.depth >= depth or node.parsed for node in self.nodes)

    def nodes_in_progress(self) -> list[SourceNode]:
        return [node for node in self.nodes if not node.parsed]

    def compose_mermaid(self, escape: bool=False):
        indentation = ' ' * 2
        depth_dict: dict[int, list[SourceNode]] = defaultdict(list)
        for node in self.nodes:
            depth_dict[node.depth].append(node)
        subgraphs = []
        for depth, nodes in depth_dict.items():
            subgraphs.append("\n".join([
                f'subgraph TD {depth}',
                indent("\n".join(node.make_mermaid() for node in nodes), indentation),
                'end'
            ]))
        url_to_transient_map = {node.url: node.transientId for node in self.nodes}
        content = "\n".join([
            'graph LR',
            indent("\n".join(subgraphs), indentation),
            indent("\n".join(link.make_mermaid(urlmap=url_to_transient_map) for link in self.links), indentation),
        ])
        # for testing
        with open('mermaid.txt', 'w') as f:
            f.write(content)
        if escape:
            content = content.replace('\n', '<br>').replace('`', "'")
            stripped = (c for c in content if 0 < ord(c) < 127)
            return ''.join(stripped)
        else:
            return content


def clean_url(url: Union[str, URL]) -> str:
    """ parse article urls, remove query strings and fragments """
    _parsed = urlparse(str(url))
    _parsed = _parsed._replace(query='', fragment='')
    return urlunparse(_parsed)

from datetime import datetime
from enum import Enum
import hashlib
from typing import Any, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, validator
from yarl import URL



def clean_url(url: Union[str, URL]) -> str:
    """ parse article urls, remove query strings and fragments """
    _parsed = urlparse(str(url))
    _parsed = _parsed._replace(query='', fragment='')
    return _parsed.geturl()


def relative_to_absolute_url(relative_url: str, base_url: str) -> str:
    """ given a relative url and a base url, return an absolute url """
    assert relative_url.startswith('/')
    return urlparse(base_url)._replace(path=relative_url, query='', fragment='').geturl()


def url_to_hash(url: str) -> str:
    """ build hash unique to url """
    return hashlib.md5(url.encode()).hexdigest()


def read_blacklist() -> set:
    """ blacklist of netlocs to ignore """
    with open('blacklist.txt', 'r') as f:
        blacklist = set()
        for line in f:
            if (sline := line.strip()):
                blacklist.add(sline)
        return blacklist


class ParsedArticle(BaseModel):
    """ object returned from parse worker, to be stored in redis """
    url: str
    title: str
    text: str
    authors: list
    links: list
    published: str
    parsedAtUtc: datetime


class StreamEvent(Enum):
    """ SSE event types """
    STREAM_BEGIN = "stream_begin"
    NODE_PROCESSING = "node_processing"
    NODE_RENDER = "node_render"
    NODE_FAILURE = "node_failure"
    STREAM_END = "stream_end"


class SSE(BaseModel):
    """
    :param str data: The data field for the message.
    :param str id: The event ID to set the EventSource object's last
        event ID value to.
    :param str event: The event's type. If this is specified, an event will
        be dispatched on the browser to the listener for the specified
        event name; the web site would use addEventListener() to listen
        for named events. The default event type is "message".
    :param int retry: The reconnection time. If the connection to the server is
        lost, the browser will wait for the specified time before attempting to
        reconnect. This must be an integer, specifying the reconnection time in
        milliseconds. If a non-integer value is specified, the field is ignored.
    """
    data: Optional[dict]
    id: str
    event: str  # expects StreamEvent value
    retry: int = 15000  # ms

    @validator('event')
    def event_must_be_valid(cls, v):
        assert v in [e.value for e in StreamEvent]
        return v
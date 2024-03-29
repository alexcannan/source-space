"""Types and common functions for the articlesa worker."""
from datetime import datetime
from enum import Enum
import hashlib
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, validator
from yarl import URL


def clean_url(url: Union[str, URL]) -> str:
    """Parse article urls, remove query strings and fragments."""
    _parsed = urlparse(str(url))
    _parsed = _parsed._replace(query="", fragment="")
    return _parsed.geturl()


def relative_to_absolute_url(relative_url: str, base_url: str) -> str:
    """Given a relative url and a base url, return an absolute url."""
    assert relative_url.startswith("/")
    return (
        urlparse(base_url)._replace(path=relative_url, query="", fragment="").geturl()
    )


def url_to_hash(url: str) -> str:
    """Build hash unique to url."""
    return hashlib.md5(url.encode()).hexdigest()  # noqa: S324


class HostBlacklist:
    """Blacklist object, used to filter links."""
    blacklist_file: Path = Path("blacklist.txt")

    def _read_blacklist(self: "HostBlacklist") -> set:
        """Blacklist of netlocs to ignore."""
        with self.blacklist_file.open("r") as f:
            blacklist = set()
            for line in f:
                if sline := line.strip():
                    blacklist.add(sline)
            return blacklist

    def __init__(self: "HostBlacklist") -> None:
        """Initialize blacklist."""
        self.blacklist = self._read_blacklist()

    def __contains__(self: "HostBlacklist", host: str) -> bool:
        """
        Check if host is in blacklist.

        The netloc in the blacklist may be a subset of the host.
        For example, we want to block any subdomains of
        amazon.com, like smile.amazon.com.
        """
        if host in self.blacklist:
            return True
        for blacklisted_host in self.blacklist:
            if host.endswith(blacklisted_host):
                return True
        return False


class PlaceholderArticle(BaseModel):
    """Objects for when a source is found but it's still processing."""
    urlhash: str
    depth: int
    parent: Optional[str]


class ParseFailure(BaseModel):
    """Object returned from parse worker when parse failed."""
    message: str
    status: Optional[int] = None
    urlhash: Optional[str] = None


class ParsedArticle(BaseModel):
    """Object returned from parse worker, to be stored to & retrieved from redis."""
    url: str
    title: str
    text: Optional[str]
    authors: list[str]
    links: list[str]
    published: Union[str, datetime, None]  # isoformat
    parsedAtUtc: datetime
    urlhash: Optional[str] = None
    depth: Optional[int] = None

    @property
    def publisherNetLoc(self) -> str:
        """Return the publisher's netloc."""
        return urlparse(self.url).netloc


class StreamEvent(Enum):
    """SSE event types."""
    STREAM_BEGIN = "stream_begin"
    NODE_PROCESSING = "node_processing"
    NODE_RENDER = "node_render"
    NODE_FAILURE = "node_failure"
    STREAM_END = "stream_end"


class SSE(BaseModel):
    """
    Object to represent a Server-Sent Event.

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
    data: str
    id: str
    event: str  # expects StreamEvent value
    retry: int = 15000  # ms

    @validator("event")
    def event_must_be_valid(cls: "SSE", v: str) -> str:
        """Validate that event is a valid StreamEvent."""
        assert v in [e.value for e in StreamEvent]
        return v

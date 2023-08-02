"""
articlesa.serve.gateway module.

gateway implements backend functionality for the client. This mainly includes
sending server-sent events to the client while an article is being processed.
"""

import asyncio
from datetime import datetime
import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from articlesa.logger import logger
from articlesa.neo import Neo4JArticleDriver, ArticleNotFound
from articlesa.types import (
    ParsedArticle,
    StreamEvent,
    SSE,
    clean_url,
    url_to_hash,
    PlaceholderArticle,
    ParseFailure,
)
from articlesa.worker.parse import parse_article


router = APIRouter()


class SafeEncoder(json.JSONEncoder):
    """SafeEncoder encodes datetime objects as strings."""
    def default(self, z):  # noqa
        if isinstance(z, datetime):
            return str(z)
        else:
            return super().default(z)


def build_event(data: Optional[dict], id: str, event: StreamEvent) -> SSE:
    """build_event builds a server-sent event from data."""
    if not data:
        data = dict()
    return SSE(data=json.dumps(data, cls=SafeEncoder), id=id, event=event.value)


async def retrieve_article(url: str, neodriver: Neo4JArticleDriver) -> dict:
    """
    Retrieve article from db or through celery; intended to be wrapped in asyncio.Task.

    Tries neo.Neo4jArticleDriver.get_article first, then falls back to celery.
    """
    try:
        parsed_article = await neodriver.get_article(url)
        return parsed_article.dict()
    except ArticleNotFound:
        task = parse_article.delay(url)
        article_dict = task.get()
        try:
            await neodriver.put_article(ParsedArticle(**article_dict))
        except Exception as e:
            logger.opt(exception=e).error(f"error putting article {url} into db")
        return article_dict


async def _article_stream(
    article_url: str, max_depth: int, neodriver: Neo4JArticleDriver
) -> AsyncGenerator[SSE, None]:
    """
    Generate server-sent events to signal article parsing progress.

    article_url: url of article to parse
    max_depth: maximum depth to parse to
    """
    tasks = set()

    async def _begin_processing_task(
        url: str, depth: int, parent: Optional[str]
    ) -> AsyncGenerator[SSE, None]:
        """Submit task to celery, create placholder node."""
        placeholder_node = PlaceholderArticle(
            urlhash=url_to_hash(url), depth=depth, parent=parent
        )
        task = asyncio.create_task(retrieve_article(url, neodriver))
        task.set_name(f"{depth}/{url}")
        tasks.add(task)
        yield build_event(
            data=placeholder_node.dict(),
            id=task.get_name(),
            event=StreamEvent.NODE_PROCESSING,
        )

    async def _process_completed_task(task: asyncio.Task) -> AsyncGenerator[SSE, None]:
        depth, url = task.get_name().split("/", maxsplit=1)
        try:
            task.exception()  # raise exception if there is one
            data = ParsedArticle.parse_obj(task.result())
            data.urlhash = url_to_hash(url)
            data.depth = int(depth)
            # only pass in fields relevant for rendering
            del data.text
            yield build_event(
                data=data.dict(), id=task.get_name(), event=StreamEvent.NODE_RENDER
            )
            # if max depth has not been reached, also submit children
            if data.depth < max_depth:
                for link in data.links:
                    async for event in _begin_processing_task(
                        link, data.depth + 1, parent=data.urlhash
                    ):
                        yield event
        except Exception as e:
            logger.opt(exception=e).error(f"error in task {task.get_name()}")
            failure = ParseFailure(
                message=f"got {e.__class__.__name__}",
                status=420,
                urlhash=url_to_hash(url),
            )
            yield build_event(
                data=failure.dict(), id=task.get_name(), event=StreamEvent.NODE_FAILURE
            )

    yield build_event(data=None, id="begin", event=StreamEvent.STREAM_BEGIN)

    async for event in _begin_processing_task(
        article_url, 0, None
    ):  # start processing the root node
        yield event

    while tasks:
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            async for event in _process_completed_task(task):
                yield event

    yield build_event(data=None, id="done", event=StreamEvent.STREAM_END)


async def _event_formatter(
    sse_generator: AsyncGenerator[SSE, None]
) -> AsyncGenerator[dict, None]:
    """Format server-sent events as dictionaries."""
    async for event in sse_generator:
        yield event.dict()


@router.get("/a/{article_url:path}")
async def article_stream(
    request: Request, article_url: str, depth: int = 3
) -> EventSourceResponse:
    """Begin server-sent event stream for article parsing."""
    article_url = clean_url(article_url)
    logger.info(f"hello from article stream for {article_url}")
    async with Neo4JArticleDriver() as neodriver:
        return EventSourceResponse(
            _event_formatter(_article_stream(article_url, max_depth=depth, neodriver=neodriver))
        )

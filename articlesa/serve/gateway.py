"""
articlesa.serve.gateway module.

gateway implements backend functionality for the client. This mainly includes
sending server-sent events to the client while an article is being processed.
"""

import asyncio
from datetime import datetime
import json
from typing import AsyncGenerator, Optional
from arq import ArqRedis
from arq.jobs import JobStatus

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
from articlesa.worker import create_pool


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


async def retrieve_article(url: str,
                           arqpool: ArqRedis,
                           neodriver: Neo4JArticleDriver,
                           parent_url: Optional[str] = None,
                           ) -> dict:
    """
    Retrieve article from db or through arq; intended to be wrapped in asyncio.Task.

    Tries neo.Neo4jArticleDriver.get_article first, then falls back to arq enqueueing.

    If a parent_url is passed, neo4j will create a relationship between the parent
    and the child article.
    """
    try:
        parsed_article = await neodriver.get_article(url)
        return parsed_article.model_dump()
    except ArticleNotFound:
        pass
    job = await arqpool.enqueue_job("parse_article", url)
    while await job.status() != JobStatus.complete:
        await asyncio.sleep(0.1)
    article_dict = await job.result()
    try:
        await neodriver.put_article(ParsedArticle(**article_dict), parent_url=parent_url)
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
    arqpool = await create_pool()

    async def _begin_processing_task(
        url: str, depth: int, parent: Optional[str]
    ) -> AsyncGenerator[SSE, None]:
        """Submit task to celery, create placholder node."""
        placeholder_node = PlaceholderArticle(
            urlhash=url_to_hash(url), depth=depth, parent=parent
        )
        task = asyncio.create_task(retrieve_article(url, arqpool, neodriver, parent_url=parent))
        task.set_name(f"{depth}/{url}")
        tasks.add(task)
        yield build_event(
            data=placeholder_node.model_dump(),
            id=task.get_name(),
            event=StreamEvent.NODE_PROCESSING,
        )

    async def _process_completed_task(task: asyncio.Task) -> AsyncGenerator[SSE, None]:
        depth, url = task.get_name().split("/", maxsplit=1)
        try:
            task.exception()  # raise exception if there is one
            data = ParsedArticle.model_validate(task.result())
            data.urlhash = url_to_hash(url)
            data.depth = int(depth)
            # only pass in fields relevant for rendering
            del data.text
            yield build_event(
                data=data.model_dump(), id=task.get_name(), event=StreamEvent.NODE_RENDER
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
                data=failure.model_dump(), id=task.get_name(), event=StreamEvent.NODE_FAILURE
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
        yield event.model_dump()


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

"""articlesa.serve.gateway module.

gateway implements backend functionality for the client. This mainly includes
sending server-sent events to the client while an article is being processed.
"""

import asyncio
from datetime import datetime
import json
import random
from typing import AsyncGenerator, Optional
import uuid

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from articlesa.logger import logger
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


def build_event(data: Optional[dict], id: str, event: StreamEvent) -> SSE:
    """build_event builds a server-sent event from data."""
    if not data:
        data = dict()
    return SSE(data=json.dumps(data), id=id, event=event.value).dict()


# FOR TESTING
words = ["taco", "shelf", "gator", "iberia", "mongoose", "filthy"]
netlocs = [
    "facebook.com",
    "tacobell.biz",
    "lissajous.space",
    "zencastr.com",
    "hackernews.dev",
    "source.space",
]
netlocs = [f"https://{netloc}" for netloc in netlocs]  # so <a>.hostname works


def generate_hash() -> str:
    """Return a random hash for testing."""
    return str(uuid.uuid4())


# END FOR TESTING


async def _add_url_task(url: str) -> dict:
    """Create and wait for celery task; intended to be wrapped in asyncio.Task."""
    # TODO(alex): create task output interface for type checking
    task = parse_article.delay(url)
    return task.get()
    # random_links = list(random.sample(netlocs, random.randint(1,5)))
    # random_links = [rl+f"/{generate_hash()}" for rl in random_links]
    # if random.random() > 0.9:
    #     raise ValueError("error doing things")
    # data = ParsedArticle(url=url,
    #                         title=" ".join(random.sample(words, 3)).title(),
    #                         authors=[],
    #                         text="yo?",
    #                         links=random_links,
    #                         published="",
    #                         parsedAtUtc=datetime.utcnow())
    # await asyncio.sleep(random.normalvariate(0.5, 0.1))
    # return data.dict()


async def _article_stream(
    article_url: str, max_depth: int
) -> AsyncGenerator[SSE, None]:
    """Generate server-sent events to signal article parsing progress.

    article_url: url of article to parse
    max_depth: maximum depth to parse to
    """
    tasks = set()

    async def _begin_processing_task(
        url: str, depth: int, parent: Optional[str]
    ) -> SSE:
        """Submit task to celery, create placholder node."""
        placeholder_node = PlaceholderArticle(
            urlhash=url_to_hash(url), depth=depth, parent=parent
        )
        task = asyncio.create_task(_add_url_task(url))
        task.set_name(f"{depth}/{url}")
        tasks.add(task)
        yield build_event(
            data=placeholder_node.json(),
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
                data=data.json(), id=task.get_name(), event=StreamEvent.NODE_RENDER
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
            data = ParseFailure(
                message=f"got {e.__class__.__name__}",
                status=420,
                urlhash=url_to_hash(url),
            )
            yield build_event(
                data=data.json(), id=task.get_name(), event=StreamEvent.NODE_FAILURE
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


@router.get("/a/{article_url:path}")
async def article_stream(
    request: Request, article_url: str, depth: int = 3
) -> EventSourceResponse:
    """Begin server-sent event stream for article parsing."""
    article_url = clean_url(article_url)
    logger.info(f"hello from article stream for {article_url}")
    return EventSourceResponse(_article_stream(article_url, max_depth=depth))

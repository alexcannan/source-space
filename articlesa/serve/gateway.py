"""
gateway implements backend functionality for the client. This mainly includes
sending server-sent events to the client while an article is being processed.
"""

import asyncio
import random

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from articlesa.logger import logger
from articlesa.types import ParsedArticle, StreamEvent, SSE
from articlesa.worker.parse import parse_article


router = APIRouter()


async def _article_stream(article_url: str, depth: int):
    """
    generator function for article parsing; yields SSE
    """
    tasks = set()
    n_tasks = 0

    async def _add_url_task(url: str, depth: int):
        task = parse_article.delay(url)
        return task.get()

    yield SSE(data="begin", id="begin", event=StreamEvent.STREAM_BEGIN).dict()
    task = asyncio.create_task(_add_url_task(article_url, depth))
    task.set_name(f"{n_tasks}/{0}/{article_url}")  # i/depth/url
    tasks.add(task)
    n_tasks += 1
    yield SSE(data=None, id=task.get_name(), event=StreamEvent.NODE_PROCESSING).dict()

    while tasks:
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            try:
                task.exception()  # raise exception if there is one
                _, depth, _ = task.get_name().split('/', maxsplit=2)
                data = ParsedArticle.parse_obj(task.result()).dict()
                # TODO: only pass in fields relevant for rendering
                del data['text']
                yield SSE(data={**data, "depth": depth}, id=task.get_name(), event=StreamEvent.NODE_RENDER).dict()
            except Exception as e:
                yield SSE(data=e, id=task.get_name(), event=StreamEvent.NODE_FAILURE).dict()

    yield SSE(data="done", id="done", event=StreamEvent.STREAM_END).dict()


@router.get("/a/{article_url:path}")
async def article_stream(request: Request, article_url: str, depth: int=2):
    """
    begins server-sent event stream for article parsing
    """
    logger.info(f"hello from article stream for {article_url}")
    return EventSourceResponse(_article_stream(article_url, depth))

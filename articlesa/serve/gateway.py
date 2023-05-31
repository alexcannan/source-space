"""
gateway implements backend functionality for the client. This mainly includes
sending server-sent events to the client while an article is being processed.
"""

import asyncio
import random

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from articlesa.logger import logger
from articlesa.types import StreamEvent, SSE


router = APIRouter()


async def _test_task():
    await asyncio.sleep(random.normalvariate(5, 1))
    return {"secret_message": f"hello world {random.randint(0, 100)}"}


async def _article_stream(article_url: str, depth: int):
    """
    generator function for article parsing
    """
    stream_tasks = set()
    yield SSE(data="begin", id="begin", event=StreamEvent.STREAM_BEGIN).dict()
    for i in range(10):
        task = asyncio.create_task(_test_task())
        stream_tasks.add(task)
        task.add_done_callback(lambda x: logger.info(f"task {x} done"))
        yield SSE(data=None, id=task.get_name(), event=StreamEvent.NODE_PROCESSING).dict()
    while stream_tasks:
        done, pending = await asyncio.wait(stream_tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            yield SSE(data=task.result(), id=task.get_name(), event=StreamEvent.NODE_RENDER).dict()
            stream_tasks.remove(task)
    yield SSE(data="done", id="done", event=StreamEvent.STREAM_END).dict()


@router.get("/a/{article_url:path}")
async def article_stream(request: Request, article_url: str, depth: int=2):
    """
    begins server-sent event stream for article parsing
    """
    logger.info(f"hello from article stream for {article_url}")
    return EventSourceResponse(_article_stream(article_url, depth))

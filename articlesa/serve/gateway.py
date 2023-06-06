"""
gateway implements backend functionality for the client. This mainly includes
sending server-sent events to the client while an article is being processed.
"""

import asyncio
from datetime import datetime
import json
import random
from typing import Optional

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from articlesa.logger import logger
from articlesa.types import ParsedArticle, StreamEvent, SSE, clean_url, url_to_hash, PlaceholderArticle, ParseFailure
from articlesa.worker.parse import parse_article


router = APIRouter()


def build_event(data: Optional[dict], id: str, event: StreamEvent):
    if not data:
        data = dict()
    return SSE(data=json.dumps(data), id=id, event=event.value).dict()


async def _article_stream(article_url: str, depth: int):
    """
    generator function for article parsing; yields SSE
    """
    tasks = set()
    n_tasks = 0

    async def _add_url_task(url: str, depth: int):
        task = parse_article.delay(url)
        return task.get()

    yield build_event(data=None, id="begin", event=StreamEvent.STREAM_BEGIN)
    task = asyncio.create_task(_add_url_task(article_url, depth))
    task.set_name(f"{n_tasks}/{0}/{article_url}")  # i/depth/url
    tasks.add(task)
    n_tasks += 1
    placeholder_node = PlaceholderArticle(urlhash=url_to_hash(article_url), depth=0, parent=None)
    yield build_event(data=placeholder_node.json(),
                      id=task.get_name(),
                      event=StreamEvent.NODE_PROCESSING)

    while tasks:
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            try:
                task.exception()  # raise exception if there is one
                _, depth, _ = task.get_name().split('/', maxsplit=2)
                data = ParsedArticle.parse_obj(task.result())
                data.urlhash = url_to_hash(data.url)
                data.depth = int(depth)
                # TODO: only pass in fields relevant for rendering
                del data.text
                yield build_event(data=data.json(),
                                  id=task.get_name(),
                                  event=StreamEvent.NODE_RENDER)
            except Exception as e:
                logger.opt(exception=e).error(f"error in task {task.get_name()}")
                yield build_event(data={"error": f"{e.__class__.__name__} {e}"},
                                  id=task.get_name(),
                                  event=StreamEvent.NODE_FAILURE)

    yield build_event(data=None, id="done", event=StreamEvent.STREAM_END)


async def _fake_article_stream(depth=3):
    """ send fake but believeable events for testing SSE+UI """
    import uuid

    def generate_hash():
        return str(uuid.uuid4())

    words = ["taco", "shelf", "gator", "iberia", "mongoose", "filthy"]
    netlocs = ["facebook.com", "tacobell.biz", "lissajous.space", "zencastr.com"]

    yield build_event(data=None, id="begin", event=StreamEvent.STREAM_BEGIN)

    placeholder_node = PlaceholderArticle(urlhash=generate_hash(), depth=0, parent=None)
    yield build_event(data=placeholder_node.json(),
                      id=generate_hash(),
                      event=StreamEvent.NODE_PROCESSING)

    _, depth, _url = (None, 0, "fake.url")
    data = ParsedArticle(url=random.choice(netlocs),
                        title=" ".join(random.sample(words, 3)).title(),
                        authors=[],
                        text="yo?",
                        links=[generate_hash() for n in range(random.randint(1,5))],
                        published="",
                        parsedAtUtc=datetime.utcnow())
    data.urlhash = placeholder_node.urlhash
    data.depth = int(depth)
    root_hash = data.urlhash

    yield build_event(data=data.json(),
                    id="render1",
                    event=StreamEvent.NODE_RENDER)

    for linkhash in data.links:
        placeholder_node = PlaceholderArticle(urlhash=linkhash, depth=1, parent=root_hash)
        yield build_event(data=placeholder_node.json(),
                        id=generate_hash(),
                        event=StreamEvent.NODE_PROCESSING)

        _, depth, _url = (None, placeholder_node.depth, "fake.url")
        if random.random() < 0.9:
            data = ParsedArticle(url=random.choice(netlocs),
                                title=" ".join(random.sample(words, 3)).title(),
                                authors=[],
                                text="yooo",
                                links=[generate_hash() for n in range(random.randint(1,5))],
                                published="",
                                parsedAtUtc=datetime.utcnow())
            data.urlhash = placeholder_node.urlhash
            data.depth = int(depth)

            yield build_event(data=data.json(),
                            id=generate_hash(),
                            event=StreamEvent.NODE_RENDER)
        else:
            data = ParseFailure(message="hi there",
                                status=random.randint(300, 499))
            data.urlhash = placeholder_node.urlhash
            yield build_event(data=data.json(),
                              id=generate_hash(),
                              event=StreamEvent.NODE_FAILURE)

    yield build_event(data=None, id="done", event=StreamEvent.STREAM_END)


@router.get("/a/{article_url:path}")
async def article_stream(request: Request, article_url: str, depth: int=2):
    """
    begins server-sent event stream for article parsing
    """
    if article_url == "test":
        return EventSourceResponse(_fake_article_stream(depth=depth))
    article_url = clean_url(article_url)
    logger.info(f"hello from article stream for {article_url}")
    return EventSourceResponse(_article_stream(article_url, depth))

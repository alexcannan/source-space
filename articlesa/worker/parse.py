"""
articlesa.worker.parse reads tasks from a redis queue and processes them.
the main functionality is to download an article, parse it, then return it via redis value.
the worker can optionally use a residential proxy to cut down on bad returns.
the links parsed from the article should go through a HEAD request to make sure they're
not redirect links.
"""

import asyncio
from datetime import datetime
from typing import Optional

from aiohttp import ClientSession
from newspaper import Article

from articlesa.logger import logger
from articlesa.types import ParsedArticle, relative_to_absolute_url
from articlesa.worker.celery import app


session: Optional[ClientSession] = None


async def get_session_():
    global session
    if not session:
        session = await ClientSession().__aenter__()
    return session


class MissingArticleText(Exception):
    pass


async def check_redirect(url, session) -> str:
    logger.debug(f"checking redirect for url {url}")
    async with session.head(url, allow_redirects=True) as response:
        response.raise_for_status()
        return str(response.url)


async def download_article(url, session):
    logger.debug(f"downloading article from url {url}")
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


@app.task(name="parse_article")
async def parse_article(url) -> dict:
    """ given a url, parse the article and return a dict like ParsedArticle """
    session = await get_session_()

    # Check for redirects
    final_url = await check_redirect(url, session)
    if str(final_url) != url:
        logger.info(f"redirected from {url} to {final_url}")

    # Download the article
    article_html = await download_article(final_url, session)

    # Parse the article using forked newspaper3k with .links property
    article = Article(str(final_url))
    article.download_state = 2  # set to success
    article.set_html(article_html)
    article.parse()

    if not article.text:
        raise MissingArticleText()

    # make relative links absolute
    for i, link in enumerate(article.links):
        if link.startswith('/'):
            article.links[i] = relative_to_absolute_url(link, str(final_url))

    # redirect links if needed
    article.links = await asyncio.gather(*[check_redirect(link, session) for link in article.links])

    # TODO: filter author list by if NER thinks it's a person

    # Create a ParsedArticle object
    parsed_article = ParsedArticle(
        url=str(final_url),
        title=article.title,
        text=article.text,
        authors=article.authors,
        links=article.links,
        published=str(article.publish_date),
        parsedAtUtc=datetime.utcnow()
    ).dict()

    return parsed_article


if __name__ == "__main__":
    print("run me with:\ncelery -A articlesa.worker.parse worker -l info")
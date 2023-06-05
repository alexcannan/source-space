"""
articlesa.worker.parse reads tasks from a redis queue and processes them.
the main functionality is to download an article, parse it, then return it via redis value.
the worker can optionally use a residential proxy to cut down on bad returns.
the links parsed from the article should go through a HEAD request to make sure they're
not redirect links.
"""

from datetime import datetime
from typing import Optional

from aiohttp import ClientSession
from newspaper import Article

from articlesa.logger import logger
from articlesa.types import ParsedArticle
from articlesa.worker.celery import app


session: Optional[ClientSession] = None


async def get_session_():
    global session
    if not session:
        session = await ClientSession().__aenter__()
    return session


async def check_redirect(url, session):
    logger.debug(f"checking redirect for url {url}")
    async with session.head(url, allow_redirects=True) as response:
        return response.url


async def download_article(url, session):
    logger.debug(f"downloading article from url {url}")
    async with session.get(url) as response:
        if response.status == 200:
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
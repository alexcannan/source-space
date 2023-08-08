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
from urllib.parse import urlparse

from aiohttp import ClientSession
from newspaper import Article

from articlesa.logger import logger
from articlesa.types import ParsedArticle, relative_to_absolute_url, HostBlacklist
from articlesa.worker.app import app as celeryapp


session: Optional[ClientSession] = None
blacklist = HostBlacklist()


global_header = {
    "User-Agent": "articlesa/0.0.1",
}


async def get_session_() -> ClientSession:
    """Create a global aiohttp session if one doesn't exist."""
    global session
    if not session:
        session = await ClientSession().__aenter__()
    return session


class MissingArticleText(Exception):
    """Raised when an article has no text."""
    pass


async def check_redirect(url: str, session: ClientSession) -> Optional[str]:
    """Given a url, check if it redirects and return the final url."""
    logger.debug(f"checking redirect for url {url}")
    async with session.head(
        url, headers=global_header, allow_redirects=True
    ) as response:
        try:
            response.raise_for_status()
        except Exception:
            return None
        return str(response.url)


async def download_article(url: str, session: ClientSession) -> str:
    """Given a url, download the article and return the html as a string."""
    logger.debug(f"downloading article from url {url}")
    async with session.get(url, headers=global_header) as response:
        response.raise_for_status()
        return await response.text()


@celeryapp.task(name="parse_article")
async def parse_article(url: str) -> dict:
    """Given a url, parse the article and return a dict like ParsedArticle."""
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
        if link.startswith("/"):
            article.links[i] = relative_to_absolute_url(link, str(final_url))

    # remove links that don't have a netloc
    article.links = [link for link in article.links if urlparse(link).netloc]

    # filter links by blacklist
    article.links = [
        link for link in article.links if urlparse(link).netloc not in blacklist
    ]

    # redirect links if needed
    article.links = await asyncio.gather(
        *[check_redirect(link, session) for link in article.links]
    )

    # filter links by blacklist again after redirects, also remove None
    article.links = [
        link
        for link in article.links
        if link and (urlparse(link).netloc not in blacklist)
    ]

    # deduplicate links
    article.links = list(set(article.links))

    # MAYBE: filter author list by if NER thinks it's a person

    # Create a ParsedArticle object
    parsed_article = ParsedArticle(
        url=str(final_url),
        title=article.title,
        text=article.text,
        authors=article.authors,
        links=article.links,
        published=article.publish_date,
        parsedAtUtc=datetime.utcnow(),
    ).dict()

    return parsed_article


if __name__ == "__main__":
    print("run me with:\ncelery -A articlesa.worker.parse worker -l info")  # noqa: T201

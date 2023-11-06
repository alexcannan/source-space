"""
articlesa.worker.parse reads tasks from a redis queue and processes them.

the main functionality is to download an article, parse it, then return it via redis value.
the worker can optionally use a residential proxy to cut down on bad returns.
the links parsed from the article should go through a HEAD request to make sure they're
not redirect links.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from aiohttp import ClientSession
from arsenic import get_session, services, browsers
from newspaper import Article

from articlesa.logger import logger
from articlesa.types import ParsedArticle, relative_to_absolute_url, HostBlacklist


blacklist = HostBlacklist()
redirect_semaphore = asyncio.Semaphore(value=25)
service = services.Chromedriver(log_file=Path("chromedriver.log").open("a"))
chrome_options = {'goog:chromeOptions': {'args': ['--headless', '--disable-gpu']}}
browser = browsers.Chrome(**chrome_options)


global_header = {
    "User-Agent": "articlesa/0.0.1",
}


class MissingArticleText(Exception):
    """Raised when an article has no text."""
    pass


async def check_redirect(url: str, session: ClientSession) -> Optional[str]:
    """Given a url, check if it redirects and return the final url."""
    async with redirect_semaphore:
        logger.debug(f"checking redirect for url {url}")
        async with session.head(
            url, headers=global_header, allow_redirects=True
        ) as response:
            if response.status == 405:
                return url  # HEAD not allowed, assume no redirect
            try:
                response.raise_for_status()
            except Exception:
                return None
            return str(response.url)


async def download_article(url: str) -> str:
    """Given a url, download the article and return the html as a string."""
    logger.debug(f"downloading article from url {url}")
    async with get_session(service, browser) as session:
        await session.set_window_fullscreen()
        await session.get(url)
        # TODO: save screenshot for debugging?
        # with open('image.png', 'wb') as of:
        #     of.write((await session.get_screenshot()).getbuffer())
        return await session.get_page_source()


async def parse_article(ctx: dict, url: str) -> dict:
    """Given a url, parse the article and return a dict like ParsedArticle."""
    session: ClientSession = ctx["session"]

    # Check for redirects
    final_url = await check_redirect(url, session)
    if str(final_url) != url:
        logger.info(f"redirected from {url} to {final_url}")
    final_url = final_url or url

    # Download the article
    article_html = await download_article(final_url)

    # Parse the article using forked newspaper3k with .links property
    article = Article(str(final_url))
    article.download_state = 2  # set to success
    article.set_html(article_html)
    article.parse()

    if not article.text:
        raise MissingArticleText(f"unable to parse text from url {final_url}, other parsing likely failed too")

    logger.debug(f"{article.text=}")
    logger.debug(f"{article.links=}")

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
    )

    return parsed_article.model_dump()

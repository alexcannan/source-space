"""
articlesa.crawl helps the user to crawl popular articles from the web.

Potential sources:
- Mastodon news links
- new minimalist
- (where else to get trending articles without having to mess with an API?)
"""

import argparse
import asyncio

from aiohttp import ClientSession

from articlesa.config import ServeConfig
from articlesa.crawl import MastodonCrawler
from articlesa.logger import logger


async def submit_url(session: ClientSession, url: str) -> None:
    """Submit a URL via serve API."""
    logger.info(f"trying to GET {url}")
    async with session.get(
        f"http://localhost:{ServeConfig.port}/a/{url}"
    ) as resp:
        await resp.text()
        logger.info(f"GET {url} returned {resp.status}")


async def main(args: argparse.Namespace) -> None:
    """Run the crawler."""
    mastodon_crawler = MastodonCrawler()
    async with ClientSession() as session:
        submit_coros = []
        for url in mastodon_crawler.get_articles():
            submit_coros.append(submit_url(session, url))
        await asyncio.gather(*submit_coros)


parser = argparse.ArgumentParser(description="Crawl popular articles from the web.")
args = parser.parse_args()

asyncio.run(main(args))

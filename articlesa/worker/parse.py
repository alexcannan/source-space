"""
articlesa.worker.parse reads tasks from a redis queue and processes them.
the main functionality is to download an article, parse it, then return it via redis value.
the worker can optionally use a residential proxy to cut down on bad returns.
the links parsed from the article should go through a HEAD request to make sure they're
not redirect links.
"""

import asyncio
from datetime import datetime

import aiohttp
import redis
from newspaper import Article

from articlesa.logger import logger
from articlesa.types import ParsedArticle
from articlesa.worker.celery import app


async def check_redirect(url, session):
    async with session.head(url, allow_redirects=True) as response:
        return response.url


async def download_article(url, session):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.text()


@app.task
async def parse_article(url, session) -> ParsedArticle:
    # Check for redirects
    final_url = await check_redirect(url, session)

    # Download the article
    article_html = await download_article(final_url, session)

    # Parse the article using forked newspaper3k with .links property
    article = Article(final_url)
    article.set_html(article_html)
    article.parse()

    # Create a ParsedArticle object
    parsed_article = ParsedArticle(
        url=final_url,
        title=article.title,
        text=article.text,
        authors=article.authors,
        links=article.links,
        published=str(article.publish_date),
        parsedAtUtc=datetime.utcnow()
    )

    return parsed_article


async def worker():
    logger.info("spawned worker")
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    async with aiohttp.ClientSession() as session:
        # TODO: proxy support
        while True:
            # Read tasks from the Redis queue
            task = redis_client.lpop('article_tasks')
            logger.debug(f"got task: {task}")
            if task is None:
                # No more tasks, wait and continue
                await asyncio.sleep(1)
                continue

            url = task

            # Parse the article and check links
            parsed_article = await parse_article(url, session)

            # place the parsed article in the value of the redis key
            redis_client.set(url, parsed_article.json())


# Entry point of the worker
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-workers", type=int, default=4)
    args = parser.parse_args()

    async def main():
        await worker()
        # asyncio.gather(*[worker() for _ in range(args.n_workers)])

    asyncio.run(main())

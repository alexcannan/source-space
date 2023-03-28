"""
this worker is used to process the articles if they're not already in the database.
n amount of tasks will be spawned and will read from an article queue one at a time.
existence checking will be done elsewhere, this worker will process all articles that are
handed to it.
"""

import asyncio
import hashlib

from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient
from newspaper import Article as NewspaperArticle
from tqdm import tqdm

from articlesa.core.types import Article, clean_url
from articlesa.logger import logger


class ArticleWorker:
    def __init__(self, n_workers=10):
        self.client = AsyncIOMotorClient("mongodb://localhost:27017")
        self.db = self.client.articlesa
        self.queue = asyncio.Queue()
        self.n_workers = n_workers
        self.tasks = []

    async def startup(self):
        self.session = await ClientSession(headers={"User-Agent": "articlesa"}).__aenter__()
        logger.info(f"starting {self.n_workers} workers")
        self.tasks.append(asyncio.create_task(self.run()))

    async def shutdown(self):
        if not self.queue.empty():
            logger.info(f"shutting down workers. {self.queue.qsize()} articles left in queue.")
            pbar = tqdm(total=self.queue.qsize(), desc="article queue"); s0 = self.queue.qsize()
            while not self.queue.empty():
                await asyncio.sleep(1)
                s1 = self.queue.qsize(); pbar.update(s0 - s1); s0 = s1
            await self.queue.join()
            pbar.close()
        await self.session.close()

    async def add_article(self, url: str):
        async with self.session.get(url, ssl=False) as response:
            response.raise_for_status()
            content = await response.text()
        nparticle = NewspaperArticle(url)
        nparticle.download(input_html=content)
        nparticle.parse()
        logger.info(f"parsed {url}")
        article = Article(url=url,
                            title=nparticle.title,
                            text=nparticle.text,
                            authors=nparticle.authors,
                            links=nparticle.links,)
        if (dbarticle := await self.get_article(url)):
            result = await self.db.articles.update_one({'_id': dbarticle['_id']}, {'$set': article.to_mongo_dict()}, upsert=True)
        else:
            result = await self.db.articles.insert_one(article.to_mongo_dict())
        logger.info(f"inserted {url} into db, response: {result}")

    async def _run(self):
        while True:
            url = await self.queue.get()
            logger.info(f"processing {url}")
            await self.add_article(url)
            self.queue.task_done()

    async def run(self):
        for _ in range(self.n_workers):
            self.tasks.append(asyncio.create_task(self._run()))

    async def clean_and_add_article(self, url: str):
        """ fire and forget url through the article processing pipeline. up to client to check existence. """
        cleaned_url = clean_url(url)
        logger.debug(f"adding to queue: {cleaned_url}")
        print(self.tasks)
        await self.queue.put(cleaned_url)

    async def get_article(self, url: str):
        """ get article from db. """
        cleaned_url = clean_url(url)
        logger.debug(f"getting article from db: {cleaned_url}")
        article = await self.db.article.find_one({"url": cleaned_url})
        if not article:
            return None
        return article


worker = ArticleWorker()


if __name__ == '__main__':
    async def main():
        await worker.startup()
        await worker.add_article("https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/")
        await worker.shutdown()

    asyncio.run(main())
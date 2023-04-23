"""
this worker is used to process the articles if they're not already in the database.
n amount of tasks will be spawned and will read from an article queue one at a time.
existence checking will be done elsewhere, this worker will process all articles that are
handed to it.
"""

import asyncio
from datetime import datetime
import random
from typing import AsyncGenerator

from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from newspaper import Article as NewspaperArticle
from tqdm import tqdm

from articlesa.core.types import Article, SourceNode, SourceTree, clean_url
from articlesa.logger import logger


class ArticleWorker:
    def __init__(self, n_workers=10):
        self.client = AsyncIOMotorClient("mongodb://localhost:27017")
        self.db = self.client.articlesa
        self.articles: AsyncIOMotorCollection = self.db.articles
        self.queue = asyncio.Queue()
        self.n_workers = n_workers
        self.tasks = []

    async def startup(self):
        self.session = await ClientSession().__aenter__()
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

    def _get_time(self):
        return datetime.utcnow()

    async def add_article(self, url: str):
        headers = {"User-Agent": f"articlesa-{random.randint(0, 1000000)}"}
        async with self.session.get(url, ssl=False, headers=headers) as response:
            response.raise_for_status()
            content = await response.text()
        nparticle = NewspaperArticle(url)
        nparticle.download(input_html=content)
        nparticle.parse()
        article = Article(url=url,
                            title=nparticle.title,
                            text=nparticle.text,
                            authors=nparticle.authors,
                            links=nparticle.links,)
        if (dbarticle := await self.get_article(url)):
            updated_data = {**article.to_mongo_dict(), "updatedAt": self._get_time()}; del updated_data['url']
            result = await self.articles.update_one({'_id': dbarticle['_id']}, {'$set': updated_data})
        else:
            result = await self.articles.insert_one({**article.to_mongo_dict(), "createdAt": self._get_time()})
        logger.info(f"inserted {url} into db, response: {result.raw_result}")

    async def _run(self):
        while True:
            url = await self.queue.get()
            logger.info(f"processing {url}")
            try:
                await self.add_article(url)
            except Exception as e:
                logger.error(f"error processing {url}: {e}")
            self.queue.task_done()

    async def run(self):
        for _ in range(self.n_workers):
            self.tasks.append(asyncio.create_task(self._run()))

    async def clean_and_add_article(self, url: str):
        """ fire and forget url through the article processing pipeline. up to client to check existence. """
        cleaned_url = clean_url(url)
        logger.debug(f"adding to queue: {cleaned_url}")
        await self.queue.put(cleaned_url)
        return cleaned_url

    async def get_article(self, url: str):
        """ get article from db. """
        cleaned_url = clean_url(url)
        logger.debug(f"getting article from db: {cleaned_url}")
        article = await self.articles.find_one({"url": cleaned_url})
        if not article:
            return None
        return article

    async def wait_for_article(self, url: str):
        """ waits for article to be processed """
        if url not in self.queue._queue:
            raise ValueError(f"{url} not in queue")
        while True:
            if not (dbarticle := await self.articles.find_one({"url": url})):
                await asyncio.sleep(1)
                continue
            return dbarticle

    async def build_tree(self, tree: SourceTree, depth: int):
        """ build a tree of articles from a source """
        if depth == 0:
            yield tree
        assert len(tree.nodes) == 1, 'tree must have exactly one root node, resumption not implemented'
        while not tree.is_complete(depth):
            # create unprocessed nodes from processed node links
            for node in tree.nodes:
                if not node.parsed:
                    children = node.make_children()
                    for child in children:
                        tree.add_node(SourceNode.from_article(child))
                    links = node.make_links()
                    for link in links:
                        tree.add_link(link)
                    node.parsed = True
            unparsed_nodes = [node for node in tree.nodes if not node.parsed]
            # submit all unprocessed nodes not in queue
            for node in unparsed_nodes:
                if node not in self.queue._queue:
                    await self.queue.put(node.url)
            # await for at least one to complete, update tree, yield tree
            await asyncio.wait([self.wait_for_article(node.url) for node in unparsed_nodes], return_when=asyncio.FIRST_COMPLETED)
            dbarticles = await asyncio.gather(*[self.get_article(node.url) for node in unparsed_nodes])
            for dbarticle in dbarticles:
                if dbarticle:
                    article = SourceNode.from_db_article(dbarticle)
                    tree.update_node(article)
            yield tree
        yield tree


worker = ArticleWorker()


if __name__ == '__main__':
    async def main():
        await worker.startup()
        await worker.clean_and_add_article("https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/")
        await worker.shutdown()

    asyncio.run(main())
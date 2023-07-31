"""Entrypoint for random neo4j tasks/tests."""
import asyncio
from pprint import pprint

from articlesa.neo import Neo4JArticleDriver

article_urls = [
    "https://apnews.com/article/washington-virginia-maryland-loud-boom-crash-military-jet-biden-joint-base-andrews-7116356c23f2ade0d6c842159e261f1b",
    "https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/",
]


async def main() -> None:  # noqa: D103
    from articlesa.worker.parse import parse_article, ParsedArticle
    async with Neo4JArticleDriver() as driver:
        article = ParsedArticle.parse_obj(await parse_article(article_urls[0]))
        await driver.put_article(article)
        response = await driver.get_stats()
        pprint(response.summary.__dict__)  # noqa: T203


asyncio.run(main())

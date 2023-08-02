"""Entrypoint for random neo4j tasks/tests."""
import argparse
import asyncio
from pprint import pprint

from articlesa.neo import Neo4JArticleDriver, ArticleNotFound
from articlesa.worker.parse import parse_article, ParsedArticle


article_urls = [
    "https://apnews.com/article/washington-virginia-maryland-loud-boom-crash-military-jet-biden-joint-base-andrews-7116356c23f2ade0d6c842159e261f1b",
    "https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/",
]


parser = argparse.ArgumentParser(description="various neo4j tasks.")
subparser = parser.add_subparsers(dest="command", required=True)

parser_stats = subparser.add_parser("stats", help="get stats about the database.")

parser_put = subparser.add_parser("put", help="put and get an article from the database.")
parser_put.add_argument("--url", type=str, help="url of the article to put into the database.")

args = parser.parse_args()


async def main() -> None:  # noqa: D103
    async with Neo4JArticleDriver() as driver:
        if args.command == "stats":
            stats = await driver.get_stats()
            pprint(stats)  # noqa: T203
        elif args.command == "put":
            url = article_urls[0]
            if args.url:
                url = args.url
            parsed_article = await parse_article(url)
            await driver.put_article(ParsedArticle(**parsed_article))
            try:
                article = await driver.get_article(url)
                pprint(article)  # noqa: T203
            except ArticleNotFound:
                print("article not found in database")  # noqa: T201


asyncio.run(main())

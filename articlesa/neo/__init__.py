"""
articlesa.neo provides tooling for interacting with the neo4j database.

This module provides a single async context manager, Neo4JDriver, which
should be entered to perform any database operations.
"""

import os

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.time import DateTime, Date, Time

from articlesa.types import ParsedArticle


class ArticleNotFound(Exception):
    """Raised when an article is not found in the database."""
    pass


class Neo4JArticleDriver():
    """
    Neo4JArticleDriver is an async context manager for interacting with the neo4j database.

    All reads and writes to the database happen within this context manager.
    """
    _driver: AsyncDriver
    uri: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")

    async def __aenter__(self) -> 'Neo4JArticleDriver':
        """Enter the async context manager and return the driver."""
        self._driver = await AsyncGraphDatabase.driver(self.uri).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:  # noqa
        """Exit the async context manager."""
        # TODO: figure out why we see unclosed connection warnings  # noqa
        await self._driver.__aexit__(exc_type, exc_value, traceback)

    async def get_stats(self) -> dict:
        """Get quick stats describing the database."""
        query = """\
        MATCH (article:Article)
        MATCH (author:Author)
        MATCH (publisher:Publisher)
        RETURN COUNT(article) AS articleCount, COUNT(author) AS authorCount, COUNT(publisher) AS publisherCount
        """
        response = await self._driver.execute_query(query)
        if response.records:
            return response.records[0].data()
        else:
            return {}

    async def put_article(self,
                          parsed_article: ParsedArticle,
                          parent_url: str,
                          ) -> None:
        """
        Put a parsed article into the database.

        Includes putting author and publisher nodes.
        If a parent_url is passed, a relationship is created between the parent and the child.
        """
        query = """\
        MERGE (article:Article {url: $url})
        SET article.title = $title,
            article.links = $links,
            article.published = $published,
            article.parsedAtUtc = $parsedAtUtc
        WITH article
        UNWIND $authors AS author_name
        MERGE (author:Author {name: author_name})
        MERGE (article)-[:AUTHORED_BY]->(author)
        MERGE (publisher:Publisher {netloc: $publisherNetLoc})
        MERGE (article)-[:PUBLISHED_BY]->(publisher)
        WITH article, $parent_url AS parent_url
        MATCH (parent:Article {url: parent_url})
        MERGE (parent)-[:LINKS_TO]->(article)
        """
        _response = await self._driver.execute_query(
            query,
            url=parsed_article.url,
            title=parsed_article.title,
            links=parsed_article.links,
            published=parsed_article.published,
            parsedAtUtc=parsed_article.parsedAtUtc,
            authors=parsed_article.authors,
            publisherNetLoc=parsed_article.publisherNetLoc,
            parent_url=parent_url,
        )

    async def get_article(self, url: str) -> ParsedArticle:
        """Get an article by url. Raises KeyError if not found."""
        query = """\
        MATCH (article:Article {url: $url})
        OPTIONAL MATCH (article)-[:AUTHORED_BY]->(author:Author)
        WITH article, COLLECT(author) AS authors
        RETURN article, authors
        """
        response = await self._driver.execute_query(query, url=url)
        if response.records:
            data = response.records[0].data()
            authors = data.get("authors", [])
            data["article"]["authors"] = [author["name"] for author in authors]

            # need to call to_native on DateTime/Date/Time objects
            for key, value in data["article"].items():
                if isinstance(value, (DateTime, Date, Time)):
                    data["article"][key] = value.to_native()

            return ParsedArticle(
                **data.get("article", {}),
                text=None,
            )
        else:
            raise ArticleNotFound(url)

"""
articlesa.neo provides tooling for interacting with the neo4j database.

This module provides a single async context manager, Neo4JDriver, which
should be entered to perform any database operations.
"""

import os

from neo4j import AsyncGraphDatabase, AsyncDriver, EagerResult

from articlesa.types import ParsedArticle


class Neo4JArticleDriver():
    """
    Neo4JArticleDriver is an async context manager for interacting with the neo4j database.

    All reads and writes to the database happen within this context manager.
    """
    _driver: AsyncDriver
    uri: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")

    async def __aenter__(self) -> 'Neo4JArticleDriver':
        """Enter the async context manager and return the driver."""
        async with AsyncGraphDatabase.driver(self.uri) as driver:
            self._driver = driver
            return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:  # noqa
        """Exit the async context manager."""
        await self._driver.close()

    async def get_stats(self) -> EagerResult:
        """Get quick stats describing the database."""
        query = """\
        MATCH (article:Article)
        MATCH (author:Author)
        MATCH (publisher:Publisher)
        RETURN COUNT(article) AS articleCount, COUNT(author) AS authorCount, COUNT(publisher) AS publisherCount
        """
        return await self._driver.execute_query(query)

    async def put_article(self, parsed_article: ParsedArticle) -> None:
        """
        Put a parsed article into the database.

        Includes putting author and publisher nodes.
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
        MERGE (publisher:Publisher {netloc: $publisher})
        MERGE (article)-[:PUBLISHED_BY]->(publisher)
        """
        await self._driver.execute_query(
            query,
            url=parsed_article.url,
            title=parsed_article.title,
            links=parsed_article.links,
            published=parsed_article.published,
            parsedAtUtc=parsed_article.parsedAtUtc,
            authors=parsed_article.authors,
            publisher=parsed_article.publisher,
        )

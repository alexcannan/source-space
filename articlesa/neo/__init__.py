"""
articlesa.neo provides tooling for interacting with the neo4j database.

This module provides a single async context manager, Neo4JDriver, which
should be entered to perform any database operations.
"""

import os

from neo4j import AsyncGraphDatabase, AsyncDriver


class Neo4JDriver():
    """
    Neo4JDriver is an async context manager for interacting with the neo4j database.

    You can do a lot of things with it, I promise.
    """
    _driver: AsyncDriver
    uri: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")

    async def __aenter__(self) -> 'Neo4JDriver':
        """Enter the async context manager and return the driver."""
        async with AsyncGraphDatabase.driver(self.uri) as driver:
            self._driver = driver
            return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:  # noqa
        """Exit the async context manager."""
        await self._driver.close()

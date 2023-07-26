import asyncio
from pprint import pprint

from articlesa.neo import Neo4JDriver


async def main():
    query = '''\
    CREATE (article:FakeArticle {
        title: "Your Article Title",
        content: "Lorem ipsum dolor sit amet, consectetur adipiscing elit...",
        published_date: "2023-07-25"
    })
    '''
    async with Neo4JDriver() as driver:
        response = await driver._driver.execute_query(query)
        pprint(response.summary.__dict__)


asyncio.run(main())

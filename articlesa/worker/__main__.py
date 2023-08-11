import asyncio

from arq import create_pool
from arq.connections import RedisSettings


async def main():
    redis = await create_pool(RedisSettings())
    for url in ('https://facebook.com', 'https://microsoft.com', 'https://github.com'):
        await redis.enqueue_job('parse_article', url)


if __name__ == '__main__':
    asyncio.run(main())
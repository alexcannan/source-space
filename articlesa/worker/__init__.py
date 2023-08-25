import asyncio

from aiohttp import ClientSession
from arq import create_pool
from arq.connections import RedisSettings

from articlesa.config import RedisConfig
from articlesa.logger import logger
from articlesa.worker.parse import parse_article


async def make_pool():
    """Create a redis pool for the worker, used to enqueue jobs."""
    return await create_pool(
        RedisSettings(
            host=RedisConfig.host,
            port=RedisConfig.port,
        )
    )


async def startup(ctx):
    """Startup function for arq worker, creates aiohttp session."""
    logger.info("starting up")
    ctx['session'] = await ClientSession().__aenter__()


async def shutdown(ctx):
    """Shutdown function for arq worker, closes aiohttp session."""
    logger.info("shutting down")
    await ctx['session'].__aexit__(None, None, None)


class WorkerSettings:
    """https://arq-docs.helpmanual.io/#arq.worker.Worker"""
    functions = [parse_article]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 5

""" main module of source space worker """

import asyncio

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job


async def submit() -> None:
    """ submit a few test urls to the scrape worker. """
    redis = await create_pool(RedisSettings())
    jobs: list[Job] = []
    urls = ('https://facebook.com', 'https://microsoft.com', 'https://github.com')
    for url in urls:
        jobs.append(await redis.enqueue_job('parse_article', url))
    for url, job in zip(urls, jobs):
        try:
            result = await job.result()
        except Exception as e:
            result = f"exception {e.__class__.__name__}: {e}"
        print(f'{url} -> {result}')  # noqa: T201


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest='subcommand', required=True)
    submit_parser = subcommands.add_parser('submit')
    args = parser.parse_args()

    if args.subcommand == 'submit':
        asyncio.run(submit())

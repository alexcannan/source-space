import asyncio

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job, JobStatus


async def wait_for_job_to_complete(job: Job) -> None:
    """ Return empty when job is complete, useful for awaiting several jobs. """
    while await job.status() != JobStatus.complete:
        await asyncio.sleep(0.5)


async def main() -> None:
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
    asyncio.run(main())
""" Celery configuration; uses custom AsyncIOPool. """

import warnings

from celery import Celery
import celery_aio_pool as aio_pool

from articlesa.config import CeleryConfig

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    if aio_pool.patch_celery_tracer() is True:
        pass
    else:
        raise RuntimeError("celery_aio_pool patch failed")

app = Celery(
    "articlesa",
    broker=CeleryConfig.broker_url,
    backend=CeleryConfig.result_backend,
    worker_pool=aio_pool.AsyncIOPool,
)

app.autodiscover_tasks(["articlesa.worker.parse"], force=True)

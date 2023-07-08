""" Celery configuration; uses custom AsyncIOPool. """
import os

from celery import Celery
import celery_aio_pool as aio_pool


broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

if aio_pool.patch_celery_tracer() is True:
    pass
else:
    raise RuntimeError("celery_aio_pool patch failed")

app = Celery(
    "articlesa",
    broker=broker_url,
    backend=result_backend,
    worker_pool=aio_pool.AsyncIOPool,
)
app.autodiscover_tasks(["articlesa.worker.parse"], force=True)

"""One-stop shop for environment configuration."""

import os
from urllib.parse import urlparse


class RedisConfig:
    url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    @property
    def host(self) -> str:
        return urlparse(self.url).hostname

    @property
    def port(self) -> int:
        return urlparse(self.url).port


class ServeConfig:
    """ Configuration for serving the app. """
    port = 7654

""" Test parsing articles. """
import asyncio

import pytest

import articlesa.worker.parse


article_urls = [
    "https://apnews.com/article/washington-virginia-maryland-loud-boom-crash-military-jet-biden-joint-base-andrews-7116356c23f2ade0d6c842159e261f1b",
    "https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/",
]


@pytest.fixture(scope="session")
def event_loop():  # noqa
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.parametrize("url", article_urls)
@pytest.mark.asyncio
async def test_parse_article(url: str) -> None:
    """Test parsing articles."""
    await articlesa.worker.parse.parse_article(url)

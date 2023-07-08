""" Test parsing articles. """
import articlesa.worker.parse

import pytest


article_urls = [
    "https://apnews.com/article/washington-virginia-maryland-loud-boom-crash-military-jet-biden-joint-base-andrews-7116356c23f2ade0d6c842159e261f1b",
    "https://www.thegatewaypundit.com/2019/11/revealed-adam-schiff-connected-to-both-companies-named-in-7-4-billion-burisma-us-ukraine-corruption-case/",
]


@pytest.mark.parametrize("url", article_urls)
def test_parse_article(url: str) -> None:
    """Test parsing articles."""
    task = articlesa.worker.parse.parse_article.delay(url)
    result = task.get()
    assert result

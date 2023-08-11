"""
articlesa.crawl.__init__ helps the user to crawl popular articles from the web.

the various crawlers are aggregated here.
"""

import sys

from articlesa.logger import logger

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
except ImportError:
    logger.warning("selenium not installed, crawlers will not work")
    sys.exit(1)


class MastodonCrawler:
    """Crawl popular articles from mastodon.social."""
    url: str = "https://mastodon.social/explore/links"

    def __init__(self, headless: bool = True) -> None:
        """Initialize the MastodonCrawler."""
        self.headless = headless
        self.options = Options()
        if self.headless:
            self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)

    def get_articles(self) -> list[str]:
        """Retrieve trending articles from mastodon.social."""
        self.driver.get(self.url)
        articles = self.driver.find_elements(By.CSS_SELECTOR, "a.story")
        article_urls = [article.get_attribute("href") for article in articles]
        logger.info(f"found {len(article_urls)} articles from mastodon.social")
        return article_urls

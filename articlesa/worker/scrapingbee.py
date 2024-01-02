""" scrape article urls with scrapingbee.com """

import os

from pydantic import BaseModel, Field


SCRAPINGBEE_URL = "https://app.scrapingbee.com/api/v1/"
SCRAPINGBEE_API_KEY = os.environ['SCRAPINGBEE_API_KEY']


class ScrapingBeeResponse(BaseModel):
    """ json response from scrapingbee.com """
    body: str
    cookies: list[dict]
    headers: dict
    type: str  # "html"
    initial_status_code: int = Field(alias='initial-status-code')
    resolved_url: str = Field(alias='resolved-url')
    screenshot: str
    metadata: dict

"""OWASP scraper."""

from __future__ import annotations

import logging
import time
from http import HTTPStatus
from urllib.parse import urlparse

import requests
from lxml import etree, html
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apps.owasp.models.enums.project import AudienceChoices
from apps.owasp.models.scrape_log import ScrapeLog

logger: logging.Logger = logging.getLogger(__name__)

MAX_RETRIES = 3
TIMEOUT = 5, 10


class OwaspScraper:
    """OWASP scraper."""

    def __init__(self, url: bytes | str) -> None:
        """Create OWASP site scraper."""
        self.page_tree = None

        http_adapter = HTTPAdapter(
            max_retries=Retry(
                backoff_factor=1,
                raise_on_status=False,
                status_forcelist=(429, 500, 502, 503, 504),
                total=MAX_RETRIES,
            )
        )
        self.session = requests.Session()
        self.session.mount("http://", http_adapter)  # NOSONAR
        self.session.mount("https://", http_adapter)

        start_time = time.time()
        try:
            page_response = self.session.get(url, timeout=TIMEOUT)
            duration = time.time() - start_time

            if page_response.status_code == HTTPStatus.NOT_FOUND:
                ScrapeLog.objects.create(
                    target_url=url,
                    status="FAILURE",
                    duration=duration,
                    error_message="Resource not found (404)",
                )
                return

            if page_response.status_code == HTTPStatus.OK:
                try:
                    self.page_tree = html.fromstring(page_response.content)
                    ScrapeLog.objects.create(target_url=url, status="SUCCESS", duration=duration)
                except etree.ParserError as e:
                    ScrapeLog.objects.create(
                        target_url=url,
                        status="FAILURE",
                        duration=duration,
                        error_message=f"Parser error: {e}",
                    )
            else:
                ScrapeLog.objects.create(
                    target_url=url,
                    status="FAILURE",
                    duration=duration,
                    error_message=f"Request failed with status: {page_response.status_code}",
                )

        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            logger.exception("Request failed", extra={"url": url})
            ScrapeLog.objects.create(
                target_url=url,
                status="FAILURE",
                duration=duration,
                error_message=f"Request exception: {e}",
            )

    def get_audience(self) -> list[str]:
        """Return scraped audience with fallback selectors."""
        if self.page_tree is None:
            return []

        flexible_xpath = (
            "//div[@class='sidebar'] | "
            "//*[@role='complementary'] | "
            "//div[contains(@class, 'project-metadata')] | "
            "//div[contains(@id, 'sidebar')]"
        )
        containers = self.page_tree.xpath(flexible_xpath)

        found_keywords = set()
        audience_choices = AudienceChoices.choices

        for container in containers:
            text_components = container.xpath(".//li | .//p")
            for component in text_components:
                item_text = component.text_content()
                if not item_text:
                    continue

                for lower_kw, original_kw in audience_choices:
                    if original_kw in item_text:
                        found_keywords.add(lower_kw)

            image_components = container.xpath(".//img")
            for image in image_components:
                alt_text = image.get("alt")
                if not alt_text:
                    continue

                for lower_kw, original_kw in audience_choices:
                    if original_kw in alt_text:
                        found_keywords.add(lower_kw)

        return sorted(found_keywords)

    def get_urls(self, domain=None):
        """Return scraped URLs with fallback selectors."""
        if self.page_tree is None:
            return set()

        #Broaden the search to catch links in sidebars, complementary roles or main content areas
        xpath_base = "//div[@class='sidebar']//a | //*[@role='complementary']//a | //main//a"
        if domain is not None:
            query = f"{xpath_base}[contains(@href, '{domain}')]/@href"
        else:
            query = f"{xpath_base}/@href"
        return set(self.page_tree.xpath(query))

    def verify_url(self, url):
        """Verify URL."""
        location = urlparse(url).netloc.lower()
        if not location:
            return None

        if location.endswith(("linkedin.com", "slack.com", "youtube.com")):
            return url

        try:
            # Check for redirects.
            response = self.session.get(url, allow_redirects=False, timeout=TIMEOUT)
        except requests.exceptions.RequestException:
            logger.exception("Request failed", extra={"url": url})
            return None

        if response.status_code == HTTPStatus.OK:
            return url

        if response.status_code in {
            HTTPStatus.MOVED_PERMANENTLY,  # 301
            HTTPStatus.FOUND,  # 302
            HTTPStatus.SEE_OTHER,  # 303
            HTTPStatus.TEMPORARY_REDIRECT,  # 307
            HTTPStatus.PERMANENT_REDIRECT,  # 308
        }:
            return self.verify_url(response.headers["Location"])

        logger.warning("Couldn't verify URL %s", url)

        return None

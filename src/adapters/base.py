"""Base adapter with shared utilities."""

from __future__ import annotations

import logging
import os
import time

import httpx

from src.schema import Product

logger = logging.getLogger(__name__)


class BaseAdapter:
    """Common functionality for all retailer adapters."""

    name: str = "base"

    # Rate limiting
    _min_delay: float = 1.0  # seconds between requests
    _last_request_time: float = 0

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key or os.environ.get(f"{self.name.upper()}_API_KEY")
        self.use_api = bool(self.api_key)
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                },
            )
        return self._client

    def _throttle(self):
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str, **kwargs) -> httpx.Response:
        """Make a throttled GET request."""
        self._throttle()
        logger.debug("GET %s", url)
        return self.client.get(url, **kwargs)

    def search(
        self,
        query: str,
        zip_code: str = "11201",
        max_results: int = 100,
    ) -> list[Product]:
        """Search for products. Override in subclasses."""
        raise NotImplementedError

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

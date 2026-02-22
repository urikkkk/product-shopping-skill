"""Base adapter with shared utilities."""

from __future__ import annotations

import logging
import os
import random
import time

import httpx

from src.schema import Product

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_JITTER = 0.5  # seconds


class MissingAPIKeyError(Exception):
    """Raised when online mode is requested but required API key is missing."""

    def __init__(self, adapter_name: str, env_vars: list[str], setup_url: str = ""):
        self.adapter_name = adapter_name
        self.env_vars = env_vars
        self.setup_url = setup_url
        env_list = ", ".join(env_vars)
        msg = (
            f"[{adapter_name}] Online mode requires API key(s). "
            f"Set environment variable(s): {env_list}"
        )
        if setup_url:
            msg += f"\nSetup guide: {setup_url}"
        super().__init__(msg)


class BaseAdapter:
    """Common functionality for all retailer adapters."""

    name: str = "base"

    # Rate limiting
    _min_delay: float = 1.0  # seconds between requests
    _last_request_time: float = 0

    # Environment variable(s) for API keys — override in subclasses
    _env_vars: list[str] = []
    _setup_url: str = ""

    def __init__(self, api_key: str | None = None, mode: str = "auto", **kwargs):
        self.api_key = api_key or os.environ.get(f"{self.name.upper()}_API_KEY")
        self.mode = mode
        self._resolve_mode()
        self._client: httpx.Client | None = None

    def _resolve_mode(self):
        """Set self.use_api based on mode and key availability."""
        if self.mode == "online":
            if not self.api_key:
                raise MissingAPIKeyError(
                    self.name,
                    self._env_vars or [f"{self.name.upper()}_API_KEY"],
                    self._setup_url,
                )
            self.use_api = True
        elif self.mode == "seed":
            self.use_api = False
        else:  # auto
            self.use_api = bool(self.api_key)
            if not self.use_api:
                logger.info("[%s] Auto mode — no API key found, using seed data", self.name)

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
        """Make a throttled GET request with retry and exponential backoff."""
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                self._throttle()
                logger.debug("GET %s (attempt %d/%d)", url, attempt + 1, MAX_RETRIES)
                resp = self.client.get(url, **kwargs)
                resp.raise_for_status()
                return resp
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, MAX_JITTER)
                    logger.warning(
                        "[%s] Request failed (attempt %d/%d): %s — retrying in %.1fs",
                        self.name, attempt + 1, MAX_RETRIES, exc, delay,
                    )
                    time.sleep(delay)
        raise last_exc  # type: ignore[misc]

    def _post(self, url: str, json: dict | None = None, **kwargs) -> httpx.Response:
        """Make a throttled POST request with retry and exponential backoff."""
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                self._throttle()
                logger.debug("POST %s (attempt %d/%d)", url, attempt + 1, MAX_RETRIES)
                resp = self.client.post(url, json=json, **kwargs)
                resp.raise_for_status()
                return resp
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, MAX_JITTER)
                    logger.warning(
                        "[%s] POST failed (attempt %d/%d): %s — retrying in %.1fs",
                        self.name, attempt + 1, MAX_RETRIES, exc, delay,
                    )
                    time.sleep(delay)
        raise last_exc  # type: ignore[misc]

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

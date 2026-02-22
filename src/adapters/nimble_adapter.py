"""Nimble WSA adapter.

Dynamically discovers all available e-commerce SERP templates via the
Nimble REST API, runs searches across all of them, and normalizes results
into the unified Product schema.

When NIMBLE_API_KEY is not set, returns an empty list (additive adapter).
"""

from __future__ import annotations

import logging
import os

from src.schema import Product, normalize_price, normalize_rating

from .base import BaseAdapter

logger = logging.getLogger(__name__)

# Default base URL for the Nimble SDK REST API
_DEFAULT_BASE_URL = "https://sdk.nimbleway.com"


class NimbleAdapter(BaseAdapter):
    """Nimble Web Scraping API adapter with dynamic template discovery.

    Discovers available e-commerce SERP templates at runtime via
    ``GET /v1/agents``, then runs searches across all of them.
    """

    name = "nimble"
    _min_delay = 0.5
    _env_vars = ["NIMBLE_API_KEY"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._base_url = os.environ.get("NIMBLE_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
        self._templates: list[dict] | None = None  # cached after first discovery

    # ------------------------------------------------------------------
    # Template discovery
    # ------------------------------------------------------------------

    def _discover_templates(self) -> list[dict]:
        """Discover e-commerce SERP templates via GET /v1/agents.

        Returns a list of template dicts filtered to e-commerce SERP types.
        Results are cached for the lifetime of the adapter instance.
        """
        if self._templates is not None:
            return self._templates

        url = f"{self._base_url}/v1/agents"
        resp = self._get(url, headers=self._auth_headers())
        agents = resp.json()

        # The API returns a list of agent objects. Filter for e-commerce SERP.
        templates = []
        for agent in agents:
            vertical = (agent.get("vertical") or "").lower()
            entity_type = (agent.get("entity_type") or "").lower()
            if vertical == "ecommerce" and ("serp" in entity_type or "search" in entity_type or "plp" in entity_type):
                templates.append(agent)

        names = [t.get("name", "unknown") for t in templates]
        logger.info(
            "Discovered %d e-commerce SERP templates: %s",
            len(templates),
            names,
        )
        self._templates = templates
        return templates

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    # ------------------------------------------------------------------
    # Template execution
    # ------------------------------------------------------------------

    def _get_input_field(self, template: dict) -> str:
        """Return the primary input field name for a template.

        Looks at ``input_properties`` for the first required field, falling
        back to common names.
        """
        for prop in template.get("input_properties", []):
            if prop.get("is_required", False):
                return prop["name"]
        # Fallback: first property, or common default
        props = template.get("input_properties", [])
        if props:
            return props[0]["name"]
        return "keyword"

    def _supports_localization(self, template: dict) -> bool:
        return bool(template.get("is_localization_supported", False))

    def _run_template(
        self,
        template: dict,
        query: str,
        zip_code: str,
    ) -> list[dict]:
        """Execute a single template and return raw result items."""
        template_name = template.get("name", "")
        input_field = self._get_input_field(template)

        params: dict = {input_field: query}
        if self._supports_localization(template) and zip_code:
            params["zip_code"] = zip_code

        url = f"{self._base_url}/v1/agents/run"
        body = {
            "agent_name": template_name,
            "params": params,
        }

        logger.debug("Running template %s with params %s", template_name, params)
        resp = self._post(url, json=body, headers=self._auth_headers())
        data = resp.json()

        # Results may be nested under "results", "items", or at top level
        if isinstance(data, list):
            return data
        for key in ("results", "items", "products", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    # ------------------------------------------------------------------
    # General shopping search fallback
    # ------------------------------------------------------------------

    def _search_general(self, query: str) -> list[dict]:
        """Run a general shopping search via POST /v1/search."""
        url = f"{self._base_url}/v1/search"
        body = {"query": query, "focus": "shopping"}
        resp = self._post(url, json=body, headers=self._auth_headers())
        data = resp.json()
        if isinstance(data, list):
            return data
        for key in ("results", "items", "products", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    # ------------------------------------------------------------------
    # Result parsing
    # ------------------------------------------------------------------

    def _extract_brand(self, title: str, raw: dict) -> str:
        """Extract brand from raw data or product title."""
        for key in ("brand", "brand_name", "manufacturer"):
            if raw.get(key):
                return str(raw[key])
        # Fallback: first word of title
        if title:
            return title.split()[0]
        return ""

    def _parse_results(
        self,
        items: list[dict],
        source_name: str,
    ) -> list[Product]:
        """Convert raw result dicts into Product objects."""
        products = []
        for item in items:
            title = (
                item.get("product_name")
                or item.get("name")
                or item.get("title")
                or item.get("product_title")
                or ""
            )
            if not title:
                continue

            price = normalize_price(
                item.get("price")
                or item.get("sale_price")
                or item.get("current_price")
                or item.get("price_current")
            )
            rating = normalize_rating(
                item.get("rating")
                or item.get("rating_avg")
                or item.get("stars")
            )
            rating_count = 0
            raw_count = (
                item.get("review_count")
                or item.get("rating_count")
                or item.get("reviews_count")
                or item.get("num_reviews")
                or 0
            )
            try:
                rating_count = int(str(raw_count).replace(",", ""))
            except (ValueError, TypeError):
                rating_count = 0

            product_url = (
                item.get("product_url")
                or item.get("url")
                or item.get("link")
                or ""
            )
            image_url = (
                item.get("image_url")
                or item.get("image")
                or item.get("thumbnail")
                or ""
            )

            brand = self._extract_brand(title, item)

            products.append(
                Product(
                    source_site=source_name,
                    product_title=title,
                    brand=brand,
                    price_usd=price,
                    rating_avg=rating,
                    rating_count=rating_count,
                    product_url=product_url,
                    image_url=image_url,
                    availability=item.get("availability", ""),
                    extra={"nimble_raw": item},
                )
            )
        return products

    # ------------------------------------------------------------------
    # Main search entry point
    # ------------------------------------------------------------------

    _SOURCE_NAMES: dict[str, str] = {
        "amazon_serp": "Amazon",
        "walmart_serp": "Walmart",
        "walmart_ca_serp": "Walmart Canada",
        "target_serp": "Target",
        "b_and_h_serp": "B&H",
        "homedepot_serp": "Home Depot",
        "staples_serp": "Staples",
        "office_depot_serp": "Office Depot",
        "asos_serp": "ASOS",
        "footlocker_serp": "Foot Locker",
        "kroger_serp": "Kroger",
        "slickdeals_serp": "Slickdeals",
        "sams_club_plp": "Sam's Club",
    }

    def search(
        self,
        query: str,
        zip_code: str = "11201",
        max_results: int = 1000,
    ) -> list[Product]:
        """Search across all discovered Nimble e-commerce SERP templates."""
        if not self.use_api:
            logger.info("[nimble] No API key — returning empty (seed/auto mode)")
            return []

        all_products: list[Product] = []

        # Dynamic template discovery + execution
        templates = self._discover_templates()
        for template in templates:
            tname = template.get("name", "unknown")
            source = self._SOURCE_NAMES.get(tname, template.get("data_source", tname))
            try:
                items = self._run_template(template, query, zip_code)
                products = self._parse_results(items, source)
                logger.info("[nimble/%s] %d products", tname, len(products))
                all_products.extend(products)
            except Exception:
                logger.warning("[nimble/%s] Template failed — skipping", tname, exc_info=True)

        # General shopping search for broader coverage
        try:
            general_items = self._search_general(query)
            general_products = self._parse_results(general_items, "Nimble Shopping")
            logger.info("[nimble/general] %d products", len(general_products))
            all_products.extend(general_products)
        except Exception:
            logger.warning("[nimble/general] General search failed — skipping", exc_info=True)

        return all_products[:max_results]

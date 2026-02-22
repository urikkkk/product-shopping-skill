"""Unified product schema and normalization utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Product:
    """Normalized product record shared across all adapters."""

    source_site: str = ""
    product_title: str = ""
    brand: str = ""
    model: str = ""
    price_usd: float = 0.0
    availability: str = ""
    ship_to_zip: str = ""
    estimated_delivery: str = ""
    product_url: str = ""
    image_url: str = ""

    # Keyboard-specific
    layout_size: str = ""          # e.g. "Split Contoured", "Alice 75%", "TKL"
    switch_type: str = ""          # e.g. "Cherry MX Brown"
    switch_brand: str = ""         # e.g. "Cherry", "Gateron", "Kailh"
    hot_swappable: bool = False
    connectivity: str = ""         # e.g. "Bluetooth + USB-C"
    programmable: str = ""         # e.g. "QMK/VIA", "ZMK"

    # Ergonomic features (pipe-separated for multiple)
    ergonomic_features: str = ""   # e.g. "Split, Tented, Contoured keywells, Thumb clusters"

    # Ratings
    rating_avg: float = 0.0
    rating_count: int = 0

    # Category tag for grouping
    category: str = ""             # e.g. "Premium Split", "Alice", "Budget Ergo"

    # Extra metadata from adapter
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("extra", None)
        return d

    @classmethod
    def field_names(cls) -> list[str]:
        """Return ordered list of field names (excluding extra)."""
        return [f.name for f in cls.__dataclass_fields__.values() if f.name != "extra"]


def normalize_price(raw: str | float | int | None) -> float:
    """Parse a price string like '$129.99' into a float."""
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = str(raw).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def normalize_rating(raw: str | float | int | None) -> float:
    """Parse a rating like '4.5 out of 5' into a float."""
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    # Handle "4.5 out of 5"
    if "out of" in s:
        s = s.split("out of")[0].strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def normalize_bool(raw: str | bool | None) -> bool:
    """Parse various truthy/falsy representations."""
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    return str(raw).strip().lower() in ("true", "yes", "1", "y")

"""Local filtering against search.toml. Unknown values (None) never exclude a listing."""

from __future__ import annotations

from .config import Config
from .models import Listing


def zone_tier(postal: str | None, cfg: Config) -> str | None:
    """'1' / '2' / 'hors-zone', or None when the listing must be dropped."""
    if postal and postal in cfg.exclude:
        return None
    if postal and cfg.departments and postal[:2] not in cfg.departments:
        return None
    if postal in cfg.priority1:
        return "1"
    if postal in cfg.priority2:
        return "2"
    if not cfg.priority1 and not cfg.priority2:
        return "1"
    if postal is None or cfg.keep_out_of_zone:
        return "hors-zone"
    return None


def keep(l: Listing, cfg: Config) -> bool:
    if l.price is not None and l.price > cfg.price_ceiling:
        return False
    if l.price is not None and l.price < max(300, cfg.min_rent):  # 300: parking spots / placeholder prices
        return False
    if l.rooms is not None and l.rooms < cfg.min_rooms:
        return False
    if l.bedrooms is not None and l.bedrooms < cfg.min_bedrooms:
        return False
    if cfg.min_surface and l.surface is not None and l.surface < cfg.min_surface:
        return False
    if cfg.furnished == "yes" and l.furnished is False:
        return False
    if cfg.furnished == "no" and l.furnished is True:
        return False
    tier = zone_tier(l.postal_code, cfg)
    if tier is None:
        return False
    l.zone_tier = tier
    return True

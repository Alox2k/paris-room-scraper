"""Merge the same flat posted on several sites: same postal code, price within ±3 %, surface within ±2 m²."""

from __future__ import annotations

from .models import Listing

# When merging, keep the listing from the source with the richest data.
SOURCE_RANK = ["bienici", "leboncoin", "seloger", "pap", "logicimmo", "figaro", "jinka"]


def _rank(l: Listing) -> int:
    return SOURCE_RANK.index(l.source) if l.source in SOURCE_RANK else len(SOURCE_RANK)


def same_flat(a: Listing, b: Listing) -> bool:
    if not (a.postal_code and a.postal_code == b.postal_code):
        return False
    if a.price is None or b.price is None or a.surface is None or b.surface is None:
        return False
    return abs(a.price - b.price) <= 0.03 * max(a.price, b.price) and abs(a.surface - b.surface) <= 2


def merge(listings: list[Listing]) -> list[Listing]:
    by_url: dict[str, Listing] = {}
    for l in listings:
        by_url.setdefault(l.url, l)
    kept: list[Listing] = []
    for l in sorted(by_url.values(), key=_rank):
        twin = next((k for k in kept if same_flat(k, l)), None)
        if twin is None:
            kept.append(l)
            continue
        twin.other_urls.append(l.url)
        for f in ("bedrooms", "floor", "elevator", "furnished", "available_from", "charges_included", "description", "lat", "lng"):
            if getattr(twin, f) is None and getattr(l, f) is not None:
                setattr(twin, f, getattr(l, f))
    return kept

"""Generic result-card parser for HTML-only sites.

Splits the page at each listing link and reads price / m² / rooms / bedrooms / postal code from the
card's visible text. Deliberately ignores CSS classes, which change on every redesign.
"""

from __future__ import annotations

import html as htmlmod
import re

from .geo import postal_from_text
from .models import to_float, to_int

_TAG = re.compile(r"<(script|style)\b.*?</\1>|<[^>]+>", re.S | re.I)
_PRICE = re.compile(r"(\d{1,2}(?:[\s \xa0.]\d{3})+|\d{3,5})(?:[.,]\d{1,2})?\s*(?:€|euros?\b)", re.I)
_SURFACE = re.compile(r"(\d{1,3}(?:[.,]\d{1,2})?)\s*m\s?(?:²|2)(?!\d)", re.I)
_ROOMS = re.compile(r"(\d{1,2})\s*pi[eè]ces?\b|\b[TF](\d)\b|\b(studio)\b", re.I)
_BEDS = re.compile(r"(\d{1,2})\s*chambres?\b", re.I)
_DIGITS = re.compile(r"\D")


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(_TAG.sub(" ", fragment))).strip()


def split(page: str, link_re: re.Pattern, max_len: int = 6000) -> list[tuple[str, str]]:
    """[(url, card_html)] in page order. A listing link often appears several times (photo, title, button):
    each occurrence contributes the html up to the next link to a *different* listing."""
    hits = [(page.rfind("<", 0, m.start()), m.group(1)) for m in link_re.finditer(page)]
    chunks: dict[str, list[str]] = {}
    for i, (start, url) in enumerate(hits):
        end = next((s for s, u in hits[i + 1 :] if u != url), start + max_len)
        chunks.setdefault(url, []).append(page[start : min(end, start + max_len)])
    return [(url, " ".join(parts)) for url, parts in chunks.items()]


def facts(text: str) -> dict:
    """Best-effort extraction from card text. Missing → None."""
    price = None
    for m in _PRICE.finditer(text):
        v = to_float(_DIGITS.sub("", m.group(1)))
        if v and 300 <= v <= 20000:
            price = v
            break
    surface = _SURFACE.search(text)
    rooms = _ROOMS.search(text)
    beds = _BEDS.search(text)
    return {
        "price": price,
        "surface": to_float(surface.group(1)) if surface else None,
        "rooms": (1 if rooms.group(3) else to_int(rooms.group(1) or rooms.group(2))) if rooms else None,
        "bedrooms": to_int(beds.group(1)) if beds else None,
        "postal_code": postal_from_text(text),
    }


def listings(source: str, page: str, link_re: re.Pattern, base: str = "", dept: str | None = None, **fixed):
    """Turn every card on a results page into a Listing. `fixed` sets constant fields (contact_type, furnished...)."""
    from .geo import postal_from_city
    from .models import Listing

    out = []
    for url, card in split(page, link_re):
        text = text_of(card)
        f = facts(text)
        full = url if url.startswith("http") else base + url
        l = Listing(source=source, id=re.sub(r"\W+", "-", full.rsplit("/", 1)[-1] or full)[-60:], url=full,
                    title=text[:140], description=text[:600], **f, **fixed)
        if l.postal_code is None and dept:
            # city slug + postal code often appear in the URL: .../paris-15e-arrondissement-75015/...
            m = re.search(rf"[a-z]-({dept}\d{{3}})(?:\D|$)", url)
            arr = re.search(r"paris-(\d{1,2})(?:e|er|eme)?(?:[^\d]|$)", url) if dept == "75" else None
            if m:
                l.postal_code = m.group(1)
            elif arr and 1 <= int(arr.group(1)) <= 20:
                l.postal_code = f"750{int(arr.group(1)):02d}"
            else:
                l.postal_code = postal_from_city(_city_from_url(url), dept)
        if "contact_type" not in fixed and re.search(r"\bparticulier\b", text, re.I):
            l.contact_type = "particulier"
        out.append(l)
    return out


def _city_from_url(url: str) -> str | None:
    """'.../louer/paris-18/appartement-...' -> 'paris 18'; '.../location-appartement-montreuil/123' -> 'montreuil'."""
    m = re.search(r"/(?:louer|location-appartement|location-maison)-?/?([a-z]+(?:-[a-z]+)*(?:-\d{1,2})?)(?:/|$)", url)
    return m.group(1).replace("-", " ") if m else None

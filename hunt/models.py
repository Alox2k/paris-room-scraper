from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field


@dataclass
class Listing:
    """One rental listing, normalised across sources. Unknown values stay None — never guess."""

    source: str
    id: str
    url: str
    price: float | None = None  # monthly rent, charges included when the site says so
    charges_included: bool | None = None
    surface: float | None = None  # m²
    rooms: int | None = None  # "pièces"
    bedrooms: int | None = None
    postal_code: str | None = None
    city: str | None = None
    district: str | None = None
    floor: int | None = None
    elevator: bool | None = None
    furnished: bool | None = None
    available_from: str | None = None
    published_at: str | None = None
    title: str | None = None
    description: str | None = None
    contact_type: str | None = None  # "particulier" | "agence"
    lat: float | None = None
    lng: float | None = None  # lat/lng only when precise (street/building level), never a district centroid
    # Filled by the pipeline, not by sources
    metro_station: str | None = None
    metro_lines: list[str] | None = None
    metro_m: int | None = None  # distance to nearest metro station
    line14_m: int | None = None  # distance to nearest line 14 station
    zone_tier: str | None = None  # "1" | "2" | "hors-zone"
    other_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def to_int(v) -> int | None:
    try:
        return int(float(str(v).replace(",", ".").strip()))
    except (TypeError, ValueError):
        return None


def to_float(v) -> float | None:
    try:
        return float(str(v).replace(" ", "").replace("\xa0", "").replace(" ", "").replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


_FLOOR = re.compile(r"\b(?:au\s+)?(\d{1,2})\s*(?:e|er|ème|eme|è)\s+étage", re.I)
_RDC = re.compile(r"rez[- ]de[- ]chauss[ée]e|\bRDC\b", re.I)
_SURFACE_TXT = re.compile(r"(\d{1,3}(?:[.,]\d{1,2})?)\s*m\s?(?:²|2)(?!\d)", re.I)
MIN_RENT_PER_M2 = 8  # below this, the surface (or price) is a typo — e.g. "131 m²" for a 13 m² studette at 800 €


def enrich_from_text(l: Listing) -> Listing:
    """Fill floor / elevator / furnished from title+description, only where the source left them None.
    Also fixes a surface that gives an implausible rent per m², when the text states another one."""
    text = " ".join(x for x in (l.title, l.description) if x)
    if not text:
        return l
    if l.furnished is None:
        if re.search(r"non[- ]meubl|\bvide\b", text, re.I):
            l.furnished = False
        elif re.search(r"\bmeubl[ée]", text, re.I):
            l.furnished = True
    if l.elevator is None:
        if re.search(r"sans ascenseur", text, re.I):
            l.elevator = False
        elif re.search(r"ascenseur", text, re.I):
            l.elevator = True
    if l.surface and l.price and l.price / l.surface < MIN_RENT_PER_M2:
        # Implausible surface: take the first one stated in the text that gives a believable rent per m².
        for m in _SURFACE_TXT.finditer(text):
            v = to_float(m.group(1))
            if v and v != l.surface and l.price / v >= MIN_RENT_PER_M2:
                l.surface = v
                break
    if l.floor is None:
        if m := _FLOOR.search(text):
            l.floor = int(m.group(1))
        elif _RDC.search(text):
            l.floor = 0
    return l

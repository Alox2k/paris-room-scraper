"""Bien'ici — public JSON endpoint used by their own website."""

from __future__ import annotations

import json

from ..config import Config
from ..geo import DEPARTMENTS, slug
from ..http import Http
from ..models import Listing, to_int

NAME = "bienici"
PAGE_SIZE = 100


def _zone_id(http: Http, dept: str) -> str | None:
    for s in http.get_json("https://res.bienici.com/suggest.json", params={"q": DEPARTMENTS[dept]}):
        if s.get("type") in ("department", "city") and s.get("zoneIds") and (dept != "75" or s.get("name") == "Paris"):
            return s["zoneIds"][0]
    return None


def fetch(cfg: Config, http: Http) -> list[Listing]:
    zone_ids = [z for d in cfg.departments if d in DEPARTMENTS and (z := _zone_id(http, d))]
    out: list[Listing] = []
    for page in range(cfg.max_pages):
        filters = {
            "size": PAGE_SIZE,
            "from": page * PAGE_SIZE,
            "filterType": "rent",
            "propertyType": ["flat"],
            "minRooms": cfg.min_rooms,
            "maxPrice": cfg.price_ceiling,
            "onTheMarket": [True],
            "sortBy": "publicationDate",
            "sortOrder": "desc",
            "zoneIdsByTypes": {"zoneIds": zone_ids},
        }
        if cfg.furnished == "yes":
            filters["isFurnished"] = True
        data = http.get_json("https://www.bienici.com/realEstateAds.json", params={"filters": json.dumps(filters)})
        ads = data.get("realEstateAds", [])
        out += [_parse(a) for a in ads]
        if len(ads) < PAGE_SIZE:
            break
    return out


def _parse(a: dict) -> Listing:
    pos = (a.get("blurInfo") or {}).get("position") or {}
    return Listing(
        source=NAME,
        id=a["id"],
        url=f"https://www.bienici.com/annonce/location/{slug(a.get('city') or 'paris')}/appartement/{a.get('roomsQuantity') or 3}pieces/{a['id']}",
        price=a.get("price"),
        charges_included=a.get("chargesIncluded", True if a.get("rentWithoutCharges") else None),
        surface=a.get("surfaceArea"),
        rooms=to_int(a.get("roomsQuantity")),
        bedrooms=to_int(a.get("bedroomsQuantity")),
        postal_code=a.get("postalCode"),
        city=a.get("city"),
        district=((a.get("district") or {}).get("name")),
        floor=to_int(a.get("floor")),
        elevator=a.get("hasElevator"),
        furnished=a.get("isFurnished"),
        available_from=a.get("availableDate"),
        published_at=a.get("publicationDate"),
        title=a.get("title"),
        description=a.get("description"),
        contact_type="agence" if a.get("adCreatedByPro") else "particulier",
        lat=pos.get("lat"),
        lng=pos.get("lon"),
    )

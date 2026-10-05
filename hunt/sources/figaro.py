"""Figaro Immobilier — Nuxt payload. One search per (department, room count): the site only filters exact room counts."""

from __future__ import annotations

from ..config import Config
from ..geo import DEPARTMENTS, slug
from ..http import Http
from ..models import Listing, to_float, to_int
from ..nuxt import payload

NAME = "figaro"
BASE = "https://immobilier.lefigaro.fr/annonces/immobilier-location-appartement"


def fetch(cfg: Config, http: Http) -> list[Listing]:
    out: dict[str, Listing] = {}
    furn = "+meuble" if cfg.furnished == "yes" else ""
    for dept in cfg.departments:
        if dept not in DEPARTMENTS:
            continue
        place = slug(DEPARTMENTS[dept]).replace("-", "+")
        for rooms in (cfg.min_rooms, cfg.min_rooms + 1):
            for page in range(1, cfg.max_pages + 1):
                url = f"{BASE}{furn}+{rooms}pieces-{place}.html?priceMax={cfg.price_ceiling}"
                if page > 1:
                    url += f"&page={page}"
                data = payload(http.get_text(url))
                if not data:
                    raise RuntimeError("no __NUXT_DATA__ in page (layout changed)")
                resp = data["data"]["classifiedsListResponse"]
                for c in resp.get("classifieds", []):
                    if c.get("type") == "appartement" and c.get("transaction") == "location":
                        out.setdefault(c["id"], _parse(c))
                if page >= (resp.get("pagination") or {}).get("totalPage", 1):
                    break
    return list(out.values())


def _parse(c: dict) -> Listing:
    loc = c.get("location") or {}
    opts = c.get("options") or []
    return Listing(
        source=NAME,
        id=str(c["id"]),
        url=c.get("recordLink") or f"https://immobilier.lefigaro.fr/annonces/annonce-{c['id']}.html",
        price=to_float(c.get("price")),
        surface=to_float(c.get("area")),
        rooms=to_int((c.get("roomCount") or [None])[0]),
        bedrooms=to_int(c.get("bedRoomCount")),
        postal_code=loc.get("postalCode"),
        city=loc.get("city"),
        district=loc.get("district"),
        elevator=True if "ascenseur" in opts else None,
        furnished=True if "meuble" in opts else None,
        published_at=c.get("firstPublicationDate"),
        title=c.get("roomCountLabel"),
        description=c.get("description"),
        contact_type="particulier" if c.get("origin") == "particulier" else "agence",
        lat=loc.get("latitude"),
        lng=loc.get("longitude"),
    )

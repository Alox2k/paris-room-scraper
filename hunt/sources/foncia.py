"""Foncia — big Paris landlord/agency network. JSON API used by fr.foncia.com."""

from __future__ import annotations

from ..config import Config
from ..geo import DEPARTMENTS, postal_from_text, slug
from ..http import Http
from ..models import Listing, to_float, to_int

NAME = "foncia"
API = "https://fnc-api.prod.fonciatech.net/annonces/annonces/search"
PAGE_SIZE = 50


def fetch(cfg: Config, http: Http) -> list[Listing]:
    slugs = [f"{slug(DEPARTMENTS[d])}-{d}" for d in cfg.departments if d in DEPARTMENTS]
    filters = {
        "localities": {"slugs": slugs},
        "typesBien": ["appartement"],
        "prix": {"max": cfg.price_ceiling},
        "nbPiece": {"min": cfg.min_rooms},
    }
    out: list[Listing] = []
    for page in range(1, cfg.max_pages + 1):
        body = {"type": "location", "filters": filters, "expandNearby": False, "size": PAGE_SIZE, "page": page}
        r = http.request("POST", API, json=body, headers={"Origin": "https://fr.foncia.com"})
        r.raise_for_status()
        ads = r.json().get("annonces", [])
        out += [_parse(a) for a in ads]
        if len(ads) < PAGE_SIZE:
            break
    return out


def _parse(a: dict) -> Listing:
    loc = a.get("localisation") or {}
    surf = a.get("surface") or {}
    return Listing(
        source=NAME,
        id=str(a["reference"]),
        url="https://fr.foncia.com" + a["canonicalUrl"],
        price=to_float(a.get("loyer")),
        charges_included=True,  # Foncia displays rent "charges comprises"
        surface=to_float(surf.get("habitable") or surf.get("totale")),
        rooms=to_int(a.get("nbPiece")),
        postal_code=loc.get("codePostalRattach") or postal_from_text(a["canonicalUrl"]),
        city=loc.get("ville"),
        published_at=a.get("datePublication"),
        title=(a.get("titles") or {}).get("main"),
        description=a.get("description"),
        contact_type="agence",
    )

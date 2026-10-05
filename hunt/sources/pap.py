"""PAP — particulier à particulier. HTML result cards; one search per department."""

from __future__ import annotations

import html
import re

from ..config import Config
from ..geo import DEPARTMENTS, postal_from_city, postal_from_text, slug
from ..http import Http
from ..models import Listing, to_float, to_int

NAME = "pap"
BASE = "https://www.pap.fr"

_CARD = re.compile(r'<a class="item-title" href="(/annonces/[^"]+-r(\d+))"(.*?)</a>\s*(?:<p class="item-description"[^>]*>(.*?)</p>)?', re.S)
_PRICE = re.compile(r'item-price[^"]*">\s*([\d.\s]+)')
_PLACE = re.compile(r'<span class="h1">\s*(.*?)\s*</span>', re.S)
_TAGS = re.compile(r"<li>(.*?)</li>", re.S)


def _geo_id(http: Http, dept: str) -> int | None:
    for g in http.get_json(f"{BASE}/json/ac-geo", params={"q": DEPARTMENTS[dept]}):
        if dept in g.get("name", "") or (dept == "75" and g.get("name") == "Paris (75)"):
            return g["id"]
    return None


def fetch(cfg: Config, http: Http) -> list[Listing]:
    out: list[Listing] = []
    furn = "meuble-" if cfg.furnished == "yes" else ""
    for dept in cfg.departments:
        if dept not in DEPARTMENTS or not (gid := _geo_id(http, dept)):
            continue
        base = f"{BASE}/annonce/locations-appartement-{furn}{slug(DEPARTMENTS[dept])}-{dept}-g{gid}-{cfg.min_rooms}-pieces-jusqu-a-{cfg.price_ceiling}-euros"
        for page in range(1, cfg.max_pages + 1):
            page_html = http.get_text(base if page == 1 else f"{base}-{page}")
            cards = _CARD.findall(page_html)
            out += [_parse(c, dept) for c in cards]
            if len(cards) < 10:
                break
    return out


def _parse(card, dept: str) -> Listing:
    path, ad_id, body, desc = card
    price = _PRICE.search(body)
    place = _PLACE.search(body)
    place = html.unescape(re.sub(r"<[^>]+>", " ", place.group(1))).strip() if place else None
    l = Listing(source=NAME, id=ad_id, url=BASE + path, contact_type="particulier", city=place)
    l.price = to_float(price.group(1).replace(".", "")) if price else None
    for tag in (html.unescape(t).replace("\xa0", " ") for t in _TAGS.findall(body)):
        n = re.match(r"([\d,.]+)", tag)
        if not n:
            continue
        if "pièce" in tag:
            l.rooms = to_int(n.group(1))
        elif "chambre" in tag:
            l.bedrooms = to_int(n.group(1))
        elif "m²" in tag:
            l.surface = to_float(n.group(1))
    l.description = html.unescape(re.sub(r"\s+", " ", desc)).strip() if desc else None
    l.postal_code = postal_from_text(path) or postal_from_text(place) or postal_from_city(place, dept)
    return l

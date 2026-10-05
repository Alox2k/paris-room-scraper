"""Lodgis — furnished rentals in Paris (agency). HTML cards."""

import re

from .. import cards
from ..config import Config
from ..http import Http

NAME = "lodgis"
BASE = "https://www.lodgis.com"
LINK = re.compile(r'href="(https://www\.lodgis\.com/fr/paris,location-meublee/appartement/LPA\d+[^"]*\.mod\.html)"')


def fetch(cfg: Config, http: Http):
    if "75" not in cfg.departments or cfg.furnished == "no":
        return []
    out = {}
    # Lodgis has no generic filter URL; these two categories cover 2-bedroom and 4-room flats in Paris.
    for cat in ("location-2-chambres-meuble-paris_15644", "location-meuble-4-pieces-paris_16355"):
        for page in range(1, cfg.max_pages + 1):
            url = f"{BASE}/fr/paris,location-meublee/{cat}.cat.html" + (f"?p={page}" if page > 1 else "")
            got = cards.listings(NAME, http.get_text(url), LINK, BASE, "75", contact_type="agence", furnished=True)
            for l in got:
                out.setdefault(l.url, l)
            if len(got) < 10:
                break
    return list(out.values())

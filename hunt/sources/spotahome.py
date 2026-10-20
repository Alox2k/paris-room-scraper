"""Spotahome — mid/long-term furnished rentals bookable online. Paris only."""

import re

from .. import cards
from ..config import Config
from ..http import Http

NAME = "spotahome"
BASE = "https://www.spotahome.com"
LINK = re.compile(r'href="(/fr/paris/for-rent:apartments/\d+)"')


def fetch(cfg: Config, http: Http):
    if cfg.furnished == "no":
        return []
    out = []
    for page in range(1, cfg.max_pages + 1):
        url = f"{BASE}/fr/s/paris/for-rent:apartments" + (f"?page={page}" if page > 1 else "")
        got = cards.listings(NAME, http.get_text(url), LINK, BASE, "75", contact_type="agence", furnished=True)
        out += got
        if len(got) < 10:
            break
    return out

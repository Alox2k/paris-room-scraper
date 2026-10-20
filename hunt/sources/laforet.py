"""Laforêt — agency network. HTML cards; one search per department."""

import re

from .. import cards
from ..config import Config
from ..geo import DEPARTMENTS, slug
from ..http import Http

NAME = "laforet"
BASE = "https://www.laforet.com"
LINK = re.compile(r'href="(https://www\.laforet\.com/agence-immobiliere/[^"]+/louer/[^"]+-\d{6,})"')


def fetch(cfg: Config, http: Http):
    out = []
    for dept in cfg.departments:
        if dept not in DEPARTMENTS:
            continue
        for page in range(1, cfg.max_pages + 1):
            url = f"{BASE}/departement/location-appartement-{slug(DEPARTMENTS[dept])}"
            got = cards.listings(NAME, http.get_text(url + (f"?page={page}" if page > 1 else "")), LINK, BASE, dept,
                                 contact_type="agence")
            out += got
            if len(got) < 10:
                break
    return out

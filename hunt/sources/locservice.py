"""LocService — owner-to-owner rentals. HTML cards; one search per department."""

import re

from .. import cards
from ..config import Config
from ..geo import DEPARTMENTS, slug
from ..http import Http

NAME = "locservice"
BASE = "https://www.locservice.fr"
LINK = re.compile(r'href="(https://www\.locservice\.fr/[a-z-]+-\d{2}/location-(?:appartement|maison)[a-z0-9-]*/\d+)"')


def fetch(cfg: Config, http: Http):
    out = []
    for dept in cfg.departments:
        if dept not in DEPARTMENTS:
            continue
        for page in range(1, cfg.max_pages + 1):
            url = f"{BASE}/{slug(DEPARTMENTS[dept])}-{dept}/location-appartement.html"
            got = cards.listings(NAME, http.get_text(url + (f"?page={page}" if page > 1 else "")), LINK, BASE, dept,
                                 contact_type="particulier")
            out += got
            if len(got) < 10:
                break
    return out

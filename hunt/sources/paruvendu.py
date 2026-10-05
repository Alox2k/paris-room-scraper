"""ParuVendu — agencies + private owners. HTML cards; one search per department."""

import re

from .. import cards
from ..config import Config
from ..geo import DEPARTMENTS, postal_from_city, slug
from ..http import Http

NAME = "paruvendu"
BASE = "https://www.paruvendu.fr"
# Card text reads "... Appartement 40 m 2 Paris 10 2 pièces ..." / "... 62 m 2 Montreuil 3 pièces ..."
PLACE = re.compile(r"m\s?2\s+([A-ZÀ-Ý][^0-9(]*?(?:\s\d{1,2})?)\s*(?:\(\d{2}\)|Appartement|Exclusivit|Nouveau|Ascenseur|DPE|\d+\s+pi[eè]ce)")
LINK = re.compile(r'href="((?:https://www\.paruvendu\.fr)?/immobilier/location/appartement/\d+[A-Z0-9]+)"')


def fetch(cfg: Config, http: Http):
    out = []
    for dept in cfg.departments:
        if dept not in DEPARTMENTS:
            continue
        for page in range(1, cfg.max_pages + 1):
            url = f"{BASE}/immobilier/recherche/location/appartement/{slug(DEPARTMENTS[dept])}-{dept}/"
            got = cards.listings(NAME, http.get_text(url + (f"?p={page}" if page > 1 else "")), LINK, BASE, dept)
            for l in got:
                m = PLACE.search(l.description or "")
                if m:
                    l.city = m.group(1)
                    l.postal_code = postal_from_city(l.city, dept) or l.postal_code
            out += got
            if len(got) < 10:
                break
    return out

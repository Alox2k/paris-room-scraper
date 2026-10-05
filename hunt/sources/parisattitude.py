"""Paris Attitude — furnished rentals in Paris intra-muros (often expat-priced). One page per bedroom count."""

import re

from .. import cards
from ..config import Config
from ..http import Http

NAME = "parisattitude"
BASE = "https://www.parisattitude.com"
LINK = re.compile(r'href="(https://www\.parisattitude\.com/rent-apartment/[^"]+,\d+\.aspx)"')


def fetch(cfg: Config, http: Http):
    if "75" not in cfg.departments or cfg.furnished == "no":
        return []
    out = []
    for beds in (cfg.min_bedrooms, cfg.min_bedrooms + 1):
        page = http.get_text(f"{BASE}/rent-apartment-{beds}-bedrooms-paris.aspx")
        for l in cards.listings(NAME, page, LINK, BASE, "75", contact_type="agence", furnished=True):
            l.bedrooms = l.bedrooms or beds
            out.append(l)
    return out

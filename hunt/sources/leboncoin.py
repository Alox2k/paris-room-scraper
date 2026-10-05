"""LeBonCoin — the search page embeds its results as JSON (__NEXT_DATA__).

Their API (api.leboncoin.fr) is behind DataDome; the HTML page usually isn't.
The `real_estate_type` URL parameter tends to trigger the captcha, so type is filtered locally.
"""

from __future__ import annotations

import json
import re

from ..config import Config
from ..http import Http
from ..models import Listing, to_float, to_int

NAME = "leboncoin"
_NEXT = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def fetch(cfg: Config, http: Http) -> list[Listing]:
    locations = ",".join(f"d_{d}" for d in cfg.departments)
    out: list[Listing] = []
    for page in range(1, cfg.max_pages + 1):
        url = (
            f"https://www.leboncoin.fr/recherche?category=10&locations={locations}"
            f"&rooms={cfg.min_rooms}-max&price=min-{cfg.price_ceiling}&sort=time&order=desc"
        )
        if page > 1:
            url += f"&page={page}"
        m = _NEXT.search(http.get_text(url))
        if not m:
            raise RuntimeError("no __NEXT_DATA__ in page (layout changed or soft block)")
        ads = json.loads(m.group(1))["props"]["pageProps"].get("searchData", {}).get("ads", [])
        out += [l for a in ads if (l := _parse(a))]
        if len(ads) < 30:
            break
    return out


def _parse(a: dict) -> Listing | None:
    attrs = {x["key"]: x.get("value") for x in a.get("attributes", [])}
    if attrs.get("real_estate_type") not in (None, "2"):  # 2 = appartement
        return None
    loc = a.get("location", {})
    furnished = {"1": True, "2": False}.get(attrs.get("furnished"))
    avail = attrs.get("available_date")  # "11/2026"
    if avail and re.fullmatch(r"\d{2}/\d{4}", avail):
        avail = f"{avail[3:]}-{avail[:2]}"
    price = (a.get("price") or [None])[0]
    return Listing(
        source=NAME,
        id=str(a["list_id"]),
        url=a["url"],
        price=price,
        charges_included={"1": True, "0": False}.get(attrs.get("charges_included")),
        surface=to_float(attrs.get("square")),
        rooms=to_int(attrs.get("rooms")),
        bedrooms=to_int(attrs.get("bedrooms")),
        postal_code=loc.get("zipcode"),
        city=loc.get("city"),
        district=loc.get("district"),
        floor=to_int(attrs.get("floor_number")),
        elevator={"1": True, "2": False}.get(attrs.get("elevator")),
        furnished=furnished,
        available_from=avail,
        published_at=a.get("first_publication_date"),
        title=a.get("subject"),
        description=a.get("body"),
        contact_type="particulier" if (a.get("owner") or {}).get("type") == "private" else "agence",
        lat=loc.get("lat"),
        lng=loc.get("lng"),
    )

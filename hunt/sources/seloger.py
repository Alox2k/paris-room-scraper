"""SeLoger (and Logic-Immo, same company/platform) — results are embedded as JSON in window["__UFRN_FETCHER__"]."""

from __future__ import annotations

import json
import re

from ..config import Config
from ..http import Http
from ..models import Listing, to_float, to_int

NAME = "seloger"
_FETCHER = re.compile(r'window\["__UFRN_FETCHER__"\]=JSON\.parse\((".*?")\);</script>', re.S)


def dept_location_id(dept: str) -> str:
    # Their AD06 ids are the department's rank in the official list (2A/2B shift everything after 19 by one).
    n = int(dept)
    return f"AD06FR{n + 1 if n >= 20 else n}"


def fetch_host(cfg: Config, http: Http, host: str, source: str) -> list[Listing]:
    locations = ",".join(dept_location_id(d) for d in cfg.departments)
    out: list[Listing] = []
    seen: set[str] = set()
    for page in range(1, cfg.max_pages + 1):
        url = (
            f"https://{host}/classified-search?distributionTypes=Rent&estateTypes=Apartment"
            f"&locations={locations}&numberOfRoomsMin={cfg.min_rooms}&priceMax={cfg.price_ceiling}"
            f"&order=DateDesc&page={page}"
        )
        if cfg.furnished == "yes":
            url += "&furnished=true"
        m = _FETCHER.search(http.get_text(url))
        if not m:
            raise RuntimeError("no __UFRN_FETCHER__ data in page (layout changed or soft block)")
        p = json.loads(json.loads(m.group(1)))["data"]["classified-serp-init-data"]["pageProps"]
        ids = p.get("classifieds", [])
        for cid in ids:
            c = p["classifiedsData"].get(cid) if isinstance(cid, str) else cid
            if c and c["id"] not in seen:
                seen.add(c["id"])
                out.append(_parse(c, source))
        if len(ids) < 25:
            break
    return out


def fetch(cfg: Config, http: Http) -> list[Listing]:
    return fetch_host(cfg, http, "www.seloger.com", NAME)


def _parse(c: dict, source: str) -> Listing:
    raw = c.get("rawData", {})
    addr = (c.get("location") or {}).get("address", {})
    facts = {f["type"]: f.get("splitValue") for f in (c.get("hardFacts") or {}).get("facts", [])}
    price_info = ((c.get("hardFacts") or {}).get("price") or {}).get("additionalInformation") or ""
    floor = facts.get("numberOfFloors")
    floor = 0 if floor and floor.lower().startswith("rdc") else to_int(re.sub(r"\D", "", floor or "") or None)
    desc = (c.get("mainDescription") or {}).get("description")
    provider = c.get("provider") or {}
    return Listing(
        source=source,
        id=c["id"],
        url=c.get("url"),
        price=raw.get("price"),
        charges_included=True if "charges comprises" in price_info else None,
        surface=to_float((raw.get("surface") or {}).get("main")),
        rooms=to_int(raw.get("nbroom")),
        bedrooms=to_int(raw.get("nbbedroom")),
        postal_code=addr.get("zipCode"),
        city=addr.get("city"),
        district=addr.get("district"),
        floor=floor,
        published_at=(c.get("metadata") or {}).get("creationDate"),
        title=(c.get("hardFacts") or {}).get("title"),
        description=desc,
        contact_type="particulier" if provider.get("isPrivateOwner") else "agence",
    )

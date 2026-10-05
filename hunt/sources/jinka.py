"""Jinka — free aggregator (LeBonCoin, SeLoger, PAP, Bien'ici, agencies...). Reads YOUR alerts via their app API.

Setup: create a free account on jinka.fr, create an alert matching your search, then copy the
`LA_API_TOKEN` cookie from your browser (DevTools > Application > Cookies > jinka.fr) into the
environment variable named in search.toml ([jinka] token_env, default JINKA_TOKEN).
Response shape taken from github.com/falcononrails/jinka-mcp. Password login no longer exists.
"""

from __future__ import annotations

import os

from ..config import Config
from ..http import Http
from ..models import Listing, to_float, to_int

NAME = "jinka"
API = "https://api.jinka.fr/apiv2"


class NotConfigured(Exception):
    pass


def fetch(cfg: Config, http: Http) -> list[Listing]:
    token = os.environ.get(cfg.jinka_token_env, "").strip()
    if not token:
        raise NotConfigured(f"no token in ${cfg.jinka_token_env} — see hunt/sources/jinka.py")
    headers = {"Authorization": f"Bearer {token.removeprefix('Bearer ')}", "Origin": "https://www.jinka.fr"}
    alerts = http.get_json(f"{API}/alert", headers=headers)
    out: list[Listing] = []
    for alert in alerts:
        for page in range(1, cfg.max_pages + 1):
            d = http.get_json(f"{API}/alert/{alert['id']}/dashboard", params={"filter": "all", "page": page}, headers=headers)
            out += [_parse(a, alert["id"]) for a in d.get("ads", []) if not a.get("expired_at")]
            pag = d.get("pagination") or {}
            if page >= (pag.get("nbPages") or pag.get("nb_pages") or 1):
                break
    return out


def _parse(a: dict, alert_id) -> Listing:
    return Listing(
        source=NAME,
        id=str(a["id"]),
        # Redirects to the original listing (LeBonCoin, SeLoger...)
        url=a.get("webview_link") or f"https://api.jinka.fr/alert_result_view_ad?ad={a['id']}&alert_token={alert_id}",
        price=to_float(a.get("rent")),
        surface=to_float(a.get("area")),
        rooms=to_int(a.get("room")),
        bedrooms=to_int(a.get("bedroom")),
        postal_code=a.get("postal_code"),
        city=a.get("city"),
        floor=to_int(a.get("floor")),
        furnished=a.get("furnished") if isinstance(a.get("furnished"), bool) else None,
        published_at=a.get("created_at"),
        title=a.get("source_label"),
        description=a.get("description"),
        contact_type={"particulier": "particulier", "agence": "agence", "pro": "agence"}.get((a.get("owner_type") or "").lower()),
        lat=to_float(a.get("lat")),
        lng=to_float(a.get("lng")),
    )

"""Distance to the nearest metro station, and to line 14. Stations come from Île-de-France Mobilités open data,
cached on disk. Only listings with precise coordinates get a distance (sources drop district centroids)."""

from __future__ import annotations

import json
import math
from pathlib import Path

from curl_cffi import requests

from .models import Listing

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "metro.json"
URL = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets-lignes/exports/json"

_stations: list[dict] | None = None


def _fetch() -> list[dict]:
    rows = requests.get(URL, params={"where": 'mode="Metro"', "select": "stop_name,shortname,stop_lat,stop_lon"}, timeout=30).json()
    by_name: dict[str, dict] = {}
    for r in rows:
        s = by_name.setdefault(r["stop_name"], {"name": r["stop_name"], "lat": float(r["stop_lat"]), "lng": float(r["stop_lon"]), "lines": []})
        if r["shortname"] not in s["lines"]:
            s["lines"].append(r["shortname"])
    return list(by_name.values())


def stations() -> list[dict]:
    global _stations
    if _stations is None:
        try:
            _stations = json.loads(CACHE.read_text())
        except (OSError, ValueError):
            _stations = _fetch()
            CACHE.parent.mkdir(exist_ok=True)
            CACHE.write_text(json.dumps(_stations, ensure_ascii=False))
    return _stations


def _dist_m(lat1, lng1, lat2, lng2) -> float:
    # Equirectangular approximation: plenty at city scale.
    x = math.radians(lng2 - lng1) * math.cos(math.radians((lat1 + lat2) / 2))
    y = math.radians(lat2 - lat1)
    return 6371000 * math.hypot(x, y)


def enrich(l: Listing) -> Listing:
    """Fill metro_station / metro_lines / metro_m / line14_m from lat/lng. Leaves them None without coordinates."""
    if l.lat is None or l.lng is None:
        return l
    best, best_d, l14 = None, math.inf, math.inf
    for s in stations():
        d = _dist_m(l.lat, l.lng, s["lat"], s["lng"])
        if d < best_d:
            best, best_d = s, d
        if "14" in s["lines"]:
            l14 = min(l14, d)
    if best:
        l.metro_station, l.metro_lines, l.metro_m = best["name"], sorted(best["lines"], key=lambda x: (len(x), x)), round(best_d)
    if l14 < math.inf:
        l.line14_m = round(l14)
    return l

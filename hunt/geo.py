"""Postal-code helpers. Uses the free French government API (geo.api.gouv.fr) with an on-disk cache."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from curl_cffi import requests

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "geo.json"

DEPARTMENTS = {
    "75": "Paris",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
}

_cache: dict[str, str | None] | None = None


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _load() -> dict:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(CACHE.read_text())
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _save():
    try:
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(_cache, ensure_ascii=False, indent=0))
    except OSError:
        pass


_PARIS_ARR = re.compile(r"paris\W*(\d{1,2})\s*(?:e|er|eme|ème|è)\b", re.I)
_POSTAL = re.compile(r"\b(75|77|78|91|92|93|94|95)(\d{3})\b")


def postal_from_text(text: str | None) -> str | None:
    """Pull a postal code out of free text: '... (92100)', 'Paris 11e', 'Paris 7ème arrondissement'."""
    if not text:
        return None
    m = _POSTAL.search(text)
    if m:
        return m.group(0)
    m = _PARIS_ARR.search(text)
    if m and 1 <= int(m.group(1)) <= 20:
        return f"750{int(m.group(1)):02d}"
    return None


def postal_from_city(city: str | None, dept: str | None = None) -> str | None:
    """Resolve a commune name to its (first) postal code. Cached; returns None when unknown."""
    if not city:
        return None
    direct = postal_from_text(city)
    if direct:
        return direct
    name = re.sub(r"\(.*?\)", "", city).strip()
    if m := re.fullmatch(r"paris\W*(\d{1,2})", name, re.I):  # URL slugs like "paris-18"
        return f"750{int(m.group(1)):02d}" if 1 <= int(m.group(1)) <= 20 else None
    key = f"{slug(name)}|{dept or ''}"
    cache = _load()
    if key in cache:
        return cache[key]
    code = None
    try:
        params = {"nom": name, "fields": "codesPostaux,codeDepartement", "boost": "population", "limit": 5}
        if dept:
            params["codeDepartement"] = dept
        res = requests.get("https://geo.api.gouv.fr/communes", params=params, timeout=10).json()
        for c in res:
            if c.get("codesPostaux") and (not dept or c.get("codeDepartement") == dept):
                code = c["codesPostaux"][0]
                break
    except Exception:
        return None  # don't cache network failures
    cache[key] = code
    _save()
    return code

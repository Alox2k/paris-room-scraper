from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    max_rent: float = 2200
    rent_tolerance: float = 0.10
    min_rooms: int = 3
    min_bedrooms: int = 2
    min_surface: float = 0
    furnished: str = "any"
    move_in: str | None = None
    departments: list[str] = field(default_factory=lambda: ["75", "92", "93", "94"])
    priority1: list[str] = field(default_factory=list)
    priority2: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    keep_out_of_zone: bool = False
    sources: list[str] = field(default_factory=list)
    max_pages: int = 3
    delay_seconds: float = 1.5
    jinka_token_env: str = "JINKA_TOKEN"
    tracker: Path = ROOT / "tracker" / "appart-tracker.xlsx"
    last_run: Path = ROOT / "output" / "last-run.json"

    @property
    def price_ceiling(self) -> float:
        """Hard cut-off used in site queries and filtering (budget + tolerance)."""
        return round(self.max_rent * (1 + self.rent_tolerance))


def load(path: str | Path | None = None) -> Config:
    if path is None:
        path = ROOT / "search.toml"
        if not path.exists():
            path = ROOT / "search.example.toml"
    raw = tomllib.loads(Path(path).read_text())
    s, z, src = raw.get("search", {}), raw.get("zones", {}), raw.get("sources", {})
    out = raw.get("output", {})
    c = Config()
    for k in ("max_rent", "rent_tolerance", "min_rooms", "min_bedrooms", "min_surface", "furnished", "move_in", "departments"):
        if k in s:
            setattr(c, k, s[k])
    for k in ("priority1", "priority2", "exclude", "keep_out_of_zone"):
        if k in z:
            setattr(c, k, z[k])
    c.sources = src.get("enabled", [])
    c.max_pages = src.get("max_pages", c.max_pages)
    c.delay_seconds = src.get("delay_seconds", c.delay_seconds)
    c.jinka_token_env = raw.get("jinka", {}).get("token_env", c.jinka_token_env)
    if "tracker" in out:
        c.tracker = ROOT / out["tracker"]
    if "last_run" in out:
        c.last_run = ROOT / out["last_run"]
    return c

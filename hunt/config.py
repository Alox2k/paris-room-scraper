from __future__ import annotations

import re
import tomllib
from datetime import date, timedelta
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    min_rent: float = 0
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
    for k in ("min_rent", "max_rent", "rent_tolerance", "min_rooms", "min_bedrooms", "min_surface", "furnished", "move_in", "departments"):
        if k in s:
            setattr(c, k, s[k])
    for k in ("priority1", "priority2", "exclude", "keep_out_of_zone"):
        if k in z:
            setattr(c, k, z[k])
    c.move_in = resolve_date(c.move_in)
    c.sources = src.get("enabled", [])
    c.max_pages = src.get("max_pages", c.max_pages)
    c.delay_seconds = src.get("delay_seconds", c.delay_seconds)
    c.jinka_token_env = raw.get("jinka", {}).get("token_env", c.jinka_token_env)
    if "tracker" in out:
        c.tracker = ROOT / out["tracker"]
    if "last_run" in out:
        c.last_run = ROOT / out["last_run"]
    return c


def resolve_date(v, today: date | None = None) -> str | None:
    """'2026-12-01' stays as is; '+30d', '+4w', '+1m' are relative to the day of the run."""
    if not v or not isinstance(v, str) or not v.startswith("+"):
        return str(v) if v else None
    m = re.fullmatch(r"\+(\d+)([dwm])", v.strip())
    if not m:
        raise ValueError(f"move_in: unsupported value {v!r} (use YYYY-MM-DD, +30d, +4w or +1m)")
    n, unit = int(m.group(1)), m.group(2)
    today = today or date.today()
    if unit == "m":
        y, mo = divmod(today.month - 1 + n, 12)
        target = today.replace(year=today.year + y, month=mo + 1, day=1)
        # clamp the day to the target month's length (e.g. Jan 31 + 1m -> Feb 28)
        nxt = (target.replace(day=28) + timedelta(days=4)).replace(day=1)
        return target.replace(day=min(today.day, (nxt - timedelta(days=1)).day)).isoformat()
    return (today + timedelta(days=n * (7 if unit == "w" else 1))).isoformat()

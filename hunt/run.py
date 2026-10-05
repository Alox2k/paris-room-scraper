"""Run every enabled source, filter, merge duplicates, update the tracker, write a JSON report.

    python -m hunt.run                     # full run: new listings -> tracker + output/last-run.json
    python -m hunt.run --dry-run           # same, without touching the tracker
    python -m hunt.run --check             # health check: per-source counts and field fill rates
    python -m hunt.run --only pap,bienici  # restrict to some sources
    python -m hunt.run --set-priorities p.json   # {"<url>": "HAUTE"|"MOYENNE"|"BASSE"} -> tracker colours
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from . import config as config_mod
from . import dedup, filters, sources, tracker
from .http import Blocked, Http
from .models import Listing, enrich_from_text

CHECK_FIELDS = ["price", "surface", "rooms", "bedrooms", "postal_code", "floor", "furnished", "description"]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def run_source(name: str, cfg) -> tuple[list[Listing], dict]:
    t0 = time.monotonic()
    try:
        mod = sources.load(name)
        listings = [enrich_from_text(l) for l in mod.fetch(cfg, Http(delay=cfg.delay_seconds))]
        status = {"status": "ok" if listings else "empty", "fetched": len(listings)}
    except Blocked as e:
        listings, status = [], {"status": "blocked", "error": str(e)}
    except Exception as e:
        kind = "not-configured" if type(e).__name__ == "NotConfigured" else "error"
        listings, status = [], {"status": kind, "error": f"{type(e).__name__}: {e}"[:300]}
    status["seconds"] = round(time.monotonic() - t0, 1)
    return listings, status


def collect(cfg, names: list[str]) -> tuple[list[Listing], dict]:
    everything, report = [], {}
    for name in names:
        log(f"→ {name} ...")
        listings, status = run_source(name, cfg)
        if status["status"] in ("blocked", "error") and name in sources.FALLBACKS:
            fb = sources.FALLBACKS[name]
            log(f"  {name} failed ({status['status']}), trying fallback {fb}")
            listings, fb_status = run_source(fb, cfg)
            status["fallback"] = {fb: fb_status}
        log(f"  {status}")
        report[name] = status
        everything += listings
    return everything, report


def fill_rates(listings: list[Listing]) -> dict:
    if not listings:
        return {}
    return {f: f"{100 * sum(getattr(l, f) is not None for l in listings) // len(listings)}%" for f in CHECK_FIELDS}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m hunt.run")
    ap.add_argument("--config")
    ap.add_argument("--only", help="comma-separated source names")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--set-priorities", metavar="JSON")
    args = ap.parse_args(argv)
    cfg = config_mod.load(args.config)

    if args.set_priorities:
        n = tracker.set_priorities(cfg.tracker, json.loads(Path(args.set_priorities).read_text()))
        print(json.dumps({"updated": n}))
        return

    names = args.only.split(",") if args.only else (cfg.sources or sources.ALL)
    raw, report = collect(cfg, names)

    if args.check:
        by_src: dict[str, list[Listing]] = {}
        for l in raw:
            by_src.setdefault(l.source, []).append(l)
        for name, st in report.items():
            got = by_src.get(name, []) or [l for fb in st.get("fallback", {}) for l in by_src.get(fb, [])]
            st["fill"] = fill_rates(got)
            st["sample"] = got[0].to_dict() if got else None
            if st["sample"]:
                st["sample"]["description"] = (st["sample"]["description"] or "")[:120]
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    kept = [l for l in raw if filters.keep(l, cfg)]
    merged = dedup.merge(kept)
    seen = tracker.known_urls(cfg.tracker)
    new = [l for l in merged if l.url not in seen and not any(u in seen for u in l.other_urls)]
    if not args.dry_run and new:
        tracker.append(cfg.tracker, new)

    out = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "criteria": {"max_rent": cfg.max_rent, "min_rooms": cfg.min_rooms, "min_bedrooms": cfg.min_bedrooms,
                     "min_surface": cfg.min_surface, "furnished": cfg.furnished, "move_in": cfg.move_in},
        "sources": report,
        "counts": {"fetched": len(raw), "matching": len(kept), "after_merge": len(merged), "new": len(new)},
        "new": [l.to_dict() for l in new],
        "tracker": str(cfg.tracker),
    }
    cfg.last_run.parent.mkdir(parents=True, exist_ok=True)
    cfg.last_run.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    log(f"\n{out['counts']} → {cfg.last_run}")
    print(json.dumps({k: out[k] for k in ("run_at", "counts", "sources")} | {"report": str(cfg.last_run)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

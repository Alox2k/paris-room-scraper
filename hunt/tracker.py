"""Excel tracker (schema in tracker/README.md). Dedup key: URL, including the 'Autres URLs' column."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

from .models import Listing

SHEET = "Annonces"
COLUMNS = [
    "URL", "Plateforme", "Date d'ajout", "Prix", "Surface (m²)", "Pièces", "Chambres", "Code postal",
    "Ville / Quartier", "Étage", "Ascenseur", "Meublé", "Type de contact", "Disponible le", "Zone",
    "Priorité", "Statut", "Message envoyé", "Autres URLs", "Notes",
]
FILLS = {"HAUTE": "E2EFDA", "MOYENNE": "FFFFC7", "BASSE": "FCE4D6"}


def _open(path: Path):
    if path.exists():
        wb = load_workbook(path)
        return wb, wb[SHEET]
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET
    ws.append(COLUMNS)
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = "A2"
    return wb, ws


def known_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ws = load_workbook(path, read_only=True)[SHEET]
    head = [c.value for c in next(ws.iter_rows(max_row=1))]
    iu, io = head.index("URL"), head.index("Autres URLs") if "Autres URLs" in head else None
    urls = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[iu]:
            urls.add(row[iu])
        if io is not None and row[io]:
            urls.update(u.strip() for u in str(row[io]).split("\n") if u.strip())
    return urls


def append(path: Path, listings: list[Listing]) -> None:
    wb, ws = _open(path)
    today = date.today().isoformat()
    yn = {True: "oui", False: "non", None: ""}
    for l in listings:
        ws.append([
            l.url, l.source, today, l.price, l.surface, l.rooms, l.bedrooms, l.postal_code,
            " / ".join(x for x in (l.city, l.district) if x), l.floor, yn[l.elevator], yn[l.furnished],
            l.contact_type, l.available_from, l.zone_tier, None, "Nouveau", "non", "\n".join(l.other_urls), None,
        ])
    wb.save(path)


def set_priorities(path: Path, priorities: dict[str, str]) -> int:
    """priorities: {url: 'HAUTE'|'MOYENNE'|'BASSE'}. Writes the column and colours the row. Returns rows updated."""
    wb, ws = _open(path)
    head = [c.value for c in ws[1]]
    iu, ip = head.index("URL"), head.index("Priorité")
    n = 0
    for row in ws.iter_rows(min_row=2):
        p = priorities.get(row[iu].value)
        if p:
            row[ip].value = p
            fill = PatternFill("solid", fgColor=FILLS.get(p, "FFFFFF"))
            for c in row:
                c.fill = fill
            n += 1
    wb.save(path)
    return n

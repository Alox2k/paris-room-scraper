"""Each source module exposes NAME and fetch(cfg, http) -> list[Listing]."""

import importlib

ALL = [
    "bienici", "leboncoin", "pap", "seloger", "logicimmo", "jinka",
    "figaro", "entreparticuliers", "locservice", "foncia", "paruvendu",
    "laforet", "parisattitude", "lodgis", "spotahome",
]

# Used only when the primary source fails in a run.
FALLBACKS = {"seloger": "logicimmo"}


def load(name: str):
    return importlib.import_module(f"{__name__}.{name}")

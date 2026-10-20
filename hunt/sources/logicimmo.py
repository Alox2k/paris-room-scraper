"""Logic-Immo — same platform and largely the same inventory as SeLoger. Kept as a fallback source."""

from ..config import Config
from ..http import Http
from .seloger import fetch_host

NAME = "logicimmo"


def fetch(cfg: Config, http: Http):
    return fetch_host(cfg, http, "www.logic-immo.com", NAME)

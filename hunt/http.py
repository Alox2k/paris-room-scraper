"""Polite HTTP client that looks like a real browser (TLS fingerprint via curl_cffi)."""

from __future__ import annotations

import random
import time

from curl_cffi import requests

# Fingerprints that got through during testing. "chrome131" and "edge" were blocked by DataDome.
FINGERPRINTS = ["chrome", "safari", "firefox"]


class Blocked(Exception):
    """The site answered with a bot-protection page instead of content."""


BLOCK_MARKERS = ("captcha-delivery.com", "cf-challenge", "challenge-platform", "px-captcha", "Just a moment...")


class Http:
    def __init__(self, delay: float = 1.5, timeout: int = 25):
        self.delay = delay
        self.timeout = timeout
        self._last = 0.0

    def _wait(self):
        gap = self.delay + random.uniform(0, self.delay / 2)
        sleep_for = self._last + gap - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last = time.monotonic()

    def request(self, method: str, url: str, **kw) -> requests.Response:
        """Fresh request per call (no shared cookies), retrying with another fingerprint when blocked."""
        last_exc: Exception | None = None
        for fp in FINGERPRINTS:
            self._wait()
            try:
                r = requests.request(method, url, impersonate=fp, timeout=self.timeout, **kw)
            except Exception as e:  # network errors
                last_exc = e
                continue
            if r.status_code in (403, 429) or (len(r.text) < 60000 and any(m in r.text for m in BLOCK_MARKERS)):
                last_exc = Blocked(f"{r.status_code} bot protection on {url[:80]}")
                continue
            return r
        raise last_exc or Blocked(url)

    def get(self, url: str, **kw) -> requests.Response:
        return self.request("GET", url, **kw)

    def get_text(self, url: str, **kw) -> str:
        r = self.get(url, **kw)
        r.raise_for_status()
        return r.text

    def get_json(self, url: str, **kw):
        r = self.get(url, **kw)
        r.raise_for_status()
        return r.json()

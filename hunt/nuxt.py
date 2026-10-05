"""Decode Nuxt 3 payloads (<script id="__NUXT_DATA__">, 'devalue' format: a flat array of index references)."""

from __future__ import annotations

import json
import re
import sys

_SCRIPT = re.compile(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', re.S)
_WRAPPERS = {"Reactive", "ShallowReactive", "Ref", "ShallowRef"}
_OPAQUE = {"Set", "Map", "Date", "Object", "BigInt", "RegExp", "null", "EmptyRef", "EmptyShallowRef"}


def payload(page_html: str):
    m = _SCRIPT.search(page_html)
    if not m:
        return None
    arr = json.loads(m.group(1))
    memo: dict[int, object] = {}
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))

    def res(i: int):
        if i in memo:
            return memo[i]
        v = arr[i]
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in _WRAPPERS:
                out = res(v[1])
            elif v and isinstance(v[0], str) and v[0] in _OPAQUE:
                out = v[1] if v[0] == "Date" and len(v) > 1 else None
            else:
                out = [res(x) for x in v]
        elif isinstance(v, dict):
            out = {k: res(x) for k, x in v.items()}
        else:
            out = v
        memo[i] = out
        return out

    return res(0)

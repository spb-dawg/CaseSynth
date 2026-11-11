"""Minimal HTTP fetch. Lookups take a `fetch` argument so tests run without a network."""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "crash-report-decoder/0.1"


class LookupFailed(Exception):
    """The outside service could not be reached or returned an error."""


def fetch(url: str, timeout: float = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LookupFailed(f"{urllib.parse.urlsplit(url).netloc}: {exc}") from exc
    return raw.decode(charset, errors="replace")


def quote(value) -> str:
    return urllib.parse.quote(str(value), safe="")

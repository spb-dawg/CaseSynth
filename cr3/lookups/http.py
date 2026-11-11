"""Minimal HTTP fetch. Lookups take a `fetch` argument so tests run without a network."""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "crash-report-decoder/0.1"


class LookupFailed(Exception):
    """The outside service could not be reached or returned an error."""


class HttpError(LookupFailed):
    """The service answered with an error status. `body` is the start of its response.

    The message names only the host, never the URL, so a key in a query string cannot
    leak into a flag or a log.
    """

    def __init__(self, host: str, status: int, body: str):
        super().__init__(f"{host}: HTTP {status}")
        self.host, self.status, self.body = host, status, body


def fetch(url: str, timeout: float = 30) -> str:
    host = urllib.parse.urlsplit(url).netloc
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(2000).decode("utf-8", errors="replace")
        except OSError:
            body = ""
        raise HttpError(host, exc.code, body) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LookupFailed(f"{host}: {exc}") from exc
    return raw.decode(charset, errors="replace")


def quote(value) -> str:
    return urllib.parse.quote(str(value), safe="")

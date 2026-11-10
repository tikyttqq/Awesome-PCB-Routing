from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class FetchError(RuntimeError):
    pass


class Client:
    """Single-threaded, host-throttled requests with bounded retry and local cache."""

    def __init__(self, cache: Path, contact="", ttl=21600):
        self.cache, self.ttl = cache, ttl
        self.agent = "awesome-pcb-routing/0.1" + (f" (mailto:{contact})" if contact else "")
        self.last = {}

    def get(self, url, headers=None):
        host = urlsplit(url).netloc
        # Cache keys contain hashes only; API keys never appear in logs or filenames.
        key = hashlib.sha256((url + json.dumps(headers or {}, sort_keys=True)).encode()).hexdigest()
        path = self.cache / (key + ".cache")
        if path.exists() and time.time() - path.stat().st_mtime < self.ttl:
            return path.read_bytes()
        delay = 3.1 if host.endswith("arxiv.org") else 1.1
        for attempt in range(4):
            time.sleep(max(0, delay - (time.monotonic() - self.last.get(host, 0))))
            self.last[host] = time.monotonic()
            try:
                req = Request(url, headers={"User-Agent": self.agent, "Accept": "application/json, application/atom+xml", **(headers or {})})
                with urlopen(req, timeout=40) as response:
                    body = response.read()
                self.cache.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
                return body
            except HTTPError as exc:
                if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == 3:
                    raise FetchError(f"{host}: HTTP {exc.code}") from None
                retry = exc.headers.get("Retry-After", "")
                if retry.isdigit() and int(retry) > 60:
                    raise FetchError(f"{host}: rate limited; retry in a later run") from None
                time.sleep(max(int(retry) if retry.isdigit() else 0, 2 ** (attempt + 1)))
            except (URLError, TimeoutError, OSError):
                if attempt == 3:
                    raise FetchError(f"{host}: connection/timeout failure") from None
                time.sleep(2 ** (attempt + 1))
        raise FetchError(f"{host}: request failed")

    def json(self, url, headers=None):
        try:
            return json.loads(self.get(url, headers))
        except (ValueError, UnicodeError):
            raise FetchError(f"{urlsplit(url).netloc}: invalid JSON response") from None

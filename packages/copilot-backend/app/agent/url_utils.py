"""Extract HTTP(S) URLs from user messages — no hardcoded demo hosts."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    """Return unique URLs in order of appearance."""
    seen: set[str] = set()
    urls: list[str] = []
    for match in _URL_RE.finditer(text):
        url = match.group(0).rstrip(".,);]")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def validate_url(url: str) -> bool:
    """Return True when scheme is http/https and netloc is present."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:  # noqa: BLE001
        return False


def extract_urls_from_messages(messages: list) -> list[str]:
    """Extract unique URLs from a list of message strings or (role, content) tuples."""
    seen: set[str] = set()
    urls: list[str] = []
    for msg in messages:
        if isinstance(msg, str):
            text = msg
        elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
            text = str(msg[1])
        else:
            text = str(getattr(msg, "content", msg))
        for url in extract_urls(text):
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls

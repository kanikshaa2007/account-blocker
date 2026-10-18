"""Web-Writer (Stage4): public-pages-only evidence fetcher.

Uses httpx + HTML text extraction (no login, respects timeout).
Playwright can replace `_fetch_html` later for JS pages; interface stays same.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_HTML = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class Evidence:
    url: str
    title: str
    snippet: str
    fetched_at: str = ""


def extract_text(html: str, limit: int = 2000) -> str:
    text = _TAG.sub(" ", html or "")
    text = _HTML.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def fetch_evidence(url: str, timeout: float = 15.0) -> Evidence:
    """Fetch one public URL. Caller must pass PIB/ministry URLs only."""
    import httpx
    from datetime import datetime, timezone
    if not url.startswith(("https://", "http://")):
        raise ValueError("only http(s) public URLs allowed")
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url, headers={"User-Agent": "MiroFish-verifier/1.0"})
        resp.raise_for_status()
        html = resp.text
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else url
    return Evidence(
        url=url, title=title[:300], snippet=extract_text(html),
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )

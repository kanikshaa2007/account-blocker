"""Live free-source clients (Stage7): Google News RSS + PIB fact-check page + Reddit public JSON.

All official/public endpoints, proper User-Agent, graceful skip on block.
No login, no tokens required for these three.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

try:
    from .models import NormalizedPost
except ImportError:
    import importlib.util as _ilu
    import sys as _sys
    from pathlib import Path as _Path
    _spec = _ilu.spec_from_file_location(
        "live_models_fallback", _Path(__file__).resolve().parent / "models.py")
    _models = _ilu.module_from_spec(_spec)
    _sys.modules["live_models_fallback"] = _models
    _spec.loader.exec_module(_models)
    NormalizedPost = _models.NormalizedPost

UA = {"User-Agent": "MiroFish-realtime/1.0 (research dashboard)"}
_TIMEOUT = 30.0


def _get_text(url: str) -> str:
    import httpx
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True, headers=UA) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def fetch_google_news(query: str, limit: int = 20) -> List[NormalizedPost]:
    """Google News RSS (India edition): real live news, no key."""
    import urllib.parse
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(query) +
           "&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        xml = _get_text(url)
    except Exception:
        return []
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    posts: List[NormalizedPost] = []
    for node in root.iter("item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        pub = (node.findtext("pubDate") or "").strip()
        source_el = node.find("source")
        source = (source_el.text or "").strip() if source_el is not None else ""
        if not title or not link:
            continue
        posts.append(NormalizedPost(
            platform="gnews", platform_post_id=link,
            text=f"{title} — {source}", author_id=source,
            language="en", content_type="link",
            created_at=pub, url=link, raw={"source": source},
        ))
        if len(posts) >= limit:
            break
    return posts


def fetch_pib_factchecks(limit: int = 20) -> List[Dict[str, Any]]:
    """PIB Fact Check homepage: public list of recent fact checks (ground truth)."""
    try:
        html = _get_text("https://factcheck.pib.gov.in/")
    except Exception:
        return []
    items: List[Dict[str, Any]] = []
    seen: set = set()
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I):
        href, inner = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        text = re.sub(r"\s+", " ", inner).strip()
        if len(text) < 25 or "fact" not in text.lower() and "fake" not in text.lower() \
                and "false" not in text.lower() and "misleading" not in text.lower():
            continue
        if not href.startswith("http"):
            href = "https://factcheck.pib.gov.in/" + href.lstrip("/")
        if href in seen:
            continue
        seen.add(href)
        items.append({"title": text[:300], "link": href})
        if len(items) >= limit:
            break
    return items


def fetch_reddit_hot(subreddit: str = "india", limit: int = 20) -> List[NormalizedPost]:
    """Reddit public JSON (may 403 without OAuth; graceful skip)."""
    import json as _json
    for host in ("https://www.reddit.com", "https://old.reddit.com"):
        try:
            import httpx
            with httpx.Client(timeout=_TIMEOUT, follow_redirects=True,
                              headers={**UA, "Accept": "application/json"}) as client:
                resp = client.get(f"{host}/r/{subreddit}/hot/.json?limit={limit}")
                resp.raise_for_status()
                payload = _json.loads(resp.text)
        except Exception:
            continue
        posts: List[NormalizedPost] = []
        for child in payload.get("data", {}).get("children", []):
            data = child.get("data", {})
            if not data.get("title"):
                continue
            posts.append(NormalizedPost(
                platform="reddit", platform_post_id=str(data.get("id", "")),
                text=f"{data.get('title', '')} {data.get('selftext', '') or ''}".strip(),
                author_id=str(data.get("author", "")),
                language="en", content_type="link" if data.get("url") else "text",
                likes=int(data.get("ups", 0) or 0), comments=int(data.get("num_comments", 0) or 0),
                created_at=str(data.get("created_utc", "")),
                url=f"https://www.reddit.com{data.get('permalink', '')}",
                raw={"score": data.get("score"), "upvote_ratio": data.get("upvote_ratio")},
            ))
        return posts
    return []


def parse_reddit_rss(xml_text: str) -> List[NormalizedPost]:
    """Parse Reddit public RSS (.rss works without OAuth). Real authors + post IDs."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    posts: List[NormalizedPost] = []
    for entry in root.findall("a:entry", ns):
        link_el = entry.find("a:link", ns)
        author_el = entry.find("a:author/a:name", ns)
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        updated = (entry.findtext("a:updated", default="", namespaces=ns) or "").strip()
        entry_id = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
        href = link_el.get("href", "") if link_el is not None else ""
        author = (author_el.text or "").strip() if author_el is not None else ""
        if author.startswith("/u/"):
            author = author[3:]
        post_id = entry_id.split("_")[-1] if "_" in entry_id else entry_id
        if not title:
            continue
        posts.append(NormalizedPost(
            platform="reddit", platform_post_id=post_id or href, text=title,
            author_id=author, language="en", content_type="link" if href else "text",
            created_at=updated, url=href, raw={"rss_id": entry_id},
        ))
    return posts


def fetch_reddit_rss(subreddit: str = "india", limit: int = 25) -> List[NormalizedPost]:
    """Reddit public RSS feed: real posts + real author accounts, no key."""
    try:
        xml = _get_text(f"https://www.reddit.com/r/{subreddit}/hot/.rss")
    except Exception:
        return []
    return parse_reddit_rss(xml)[: max(1, limit)]


def resolve_youtube_channel_id(page_url: str) -> str:
    """Resolve a YouTube @handle or channel URL to its channelId via public page HTML."""
    try:
        html = _get_text(page_url)
    except Exception:
        return ""
    m = re.search(r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{20,})"', html)
    return m.group(1) if m else ""


def parse_youtube_rss(xml_text: str, channel_id: str = "") -> List[NormalizedPost]:
    """Parse YouTube channel RSS XML (pure, offline-testable)."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    author_el = root.find("a:author/a:name", ns)
    channel = (author_el.text or "").strip() if author_el is not None else channel_id
    posts: List[NormalizedPost] = []
    for entry in root.findall("a:entry", ns):
        vid = (entry.findtext("yt:videoId", default="", namespaces=ns) or "").strip()
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        published = (entry.findtext("a:published", default="", namespaces=ns) or "").strip()
        if not vid:
            continue
        posts.append(NormalizedPost(
            platform="youtube", platform_post_id=vid,
            text=f"{title} — {channel}", author_id=channel,
            language="en", content_type="video", created_at=published,
            url=f"https://www.youtube.com/watch?v={vid}", raw={"channel_id": channel_id},
        ))
    return posts


def fetch_youtube_channel_rss(channel_id: str, limit: int = 15) -> List[NormalizedPost]:
    """YouTube channel RSS: real videos + real channel accounts, no API key."""
    if not channel_id:
        return []
    try:
        xml = _get_text(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    except Exception:
        return []
    if "<feed" not in xml[:500] and "<rss" not in xml[:500]:
        return []  # bot-check HTML page, skip gracefully
    return parse_youtube_rss(xml, channel_id)[: max(1, limit)]

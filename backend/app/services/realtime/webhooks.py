"""Free push/semi-push receivers (Stage3): RSS poll + webhook verify handlers.

RSS is quota-free and cuts API calls: use it as trigger, APIs only enrich.
Instagram/YouTube webhooks are push: no polling while subscribed.
"""
from __future__ import annotations

import hashlib
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class RssItem:
    source: str
    external_id: str
    title: str
    link: str
    published: str = ""


def parse_rss(xml_text: str, source: str = "rss") -> List[RssItem]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items: List[RssItem] = []
    for node in root.iter("item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        guid = (node.findtext("guid") or "").strip()
        pub = (node.findtext("pubDate") or "").strip()
        key = guid or link or title
        if not key:
            continue
        external_id = hashlib.sha256(key.encode("utf-8", "replace")).hexdigest()[:16]
        items.append(RssItem(source=source, external_id=external_id, title=title, link=link, published=pub))
    return items


def fetch_rss(url: str, timeout: float = 15.0) -> str:
    import httpx
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url, headers={"User-Agent": "MiroFish-realtime/1.0"})
        resp.raise_for_status()
        return resp.text


# ---------------- Webhook verification (pure, testable) ----------------

def verify_instagram_webhook(query: Dict[str, Any], verify_token: str = "") -> tuple[bool, str]:
    """Meta GET verification: hub.mode=subscribe + hub.verify_token match -> return challenge."""
    expected = verify_token or os.environ.get("INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "")
    if query.get("hub.mode") == "subscribe" and query.get("hub.verify_token") == expected and expected:
        return True, str(query.get("hub.challenge", ""))
    return False, ""


def verify_pubsubhubbub(query: Dict[str, Any]) -> tuple[bool, str]:
    """YouTube PubSubHubbub GET verification: echo hub.challenge on subscribe."""
    if query.get("hub.mode") in ("subscribe", "unsubscribe") and query.get("hub.challenge"):
        return True, str(query.get("hub.challenge"))
    return False, ""


def parse_instagram_webhook_payload(payload: Dict[str, Any]) -> List[str]:
    """Extract changed media IDs from Meta POST body (caller then enriches via Graph API)."""
    ids: List[str] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            media_id = value.get("media_id") or value.get("object_id")
            if media_id:
                ids.append(str(media_id))
    return ids

"""Official API clients (Stage1). All token reads are lazy; missing token => skip."""
from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx

try:
    from .models import NormalizedPost
except ImportError:  # isolated file-path loading in tests
    import importlib.util as _ilu
    import sys as _sys
    from pathlib import Path as _Path
    _mod_name = __name__ + ".models_fallback" if __name__ else "models_fallback"
    _spec = _ilu.spec_from_file_location(_mod_name, _Path(__file__).resolve().parent / "models.py")
    _models = _ilu.module_from_spec(_spec)
    _sys.modules[_mod_name] = _models
    _spec.loader.exec_module(_models)
    NormalizedPost = _models.NormalizedPost

_TIMEOUT = 15.0


def _get(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _as_int(value: Any) -> int:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, number)


# ---------------- X (API v2 recent search, bearer only) ----------------

def fetch_x_recent(query: str, max_results: int = 20) -> List[NormalizedPost]:
    token = _get("X_BEARER_TOKEN")
    if not token:
        return []
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": max(10, min(100, max_results)),
        "tweet.fields": "created_at,public_metrics,author_id,lang",
    }
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
    return [parse_x_tweet(t) for t in payload.get("data", [])]


def parse_x_tweet(item: Dict[str, Any]) -> NormalizedPost:
    metrics = item.get("public_metrics", {}) or {}
    return NormalizedPost(
        platform="x",
        platform_post_id=str(item.get("id", "")),
        text=item.get("text", "") or "",
        author_id=str(item.get("author_id", "")),
        language=item.get("lang"),
        content_type="text",
        likes=_as_int(metrics.get("like_count")),
        shares=_as_int(metrics.get("retweet_count")),
        comments=_as_int(metrics.get("reply_count")),
        views=_as_int(metrics.get("impression_count")),
        created_at=str(item.get("created_at", "")),
        url=f"https://x.com/i/status/{item.get('id', '')}",
        raw=item,
    )


# ---------------- Instagram Graph API (hashtag search, token only) ----------------

def fetch_instagram_hashtag(hashtag_id: str, user_id: str, limit: int = 20) -> List[NormalizedPost]:
    token = _get("INSTAGRAM_ACCESS_TOKEN")
    if not token or not hashtag_id or not user_id:
        return []
    url = f"https://graph.facebook.com/v21.0/{hashtag_id}/recent_media"
    params = {"user_id": user_id, "fields": "id,caption,like_count,comments_count,timestamp,media_type,permalink", "limit": limit, "access_token": token}
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    return [parse_instagram_media(m) for m in payload.get("data", [])]


def parse_instagram_media(item: Dict[str, Any]) -> NormalizedPost:
    media_type = str(item.get("media_type", "TEXT")).upper()
    content_type = {"VIDEO": "video", "IMAGE": "image", "CAROUSEL_ALBUM": "mixed"}.get(media_type, "text")
    return NormalizedPost(
        platform="instagram",
        platform_post_id=str(item.get("id", "")),
        text=item.get("caption", "") or "",
        content_type=content_type,
        likes=_as_int(item.get("like_count")),
        comments=_as_int(item.get("comments_count")),
        created_at=str(item.get("timestamp", "")),
        url=str(item.get("permalink", "")),
        raw=item,
    )


# ---------------- YouTube Data API v3 (search, key only) ----------------

def fetch_youtube_search(query: str, max_results: int = 20) -> List[NormalizedPost]:
    key = _get("YOUTUBE_API_KEY")
    if not key:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {"part": "snippet", "q": query, "type": "video", "maxResults": max(1, min(50, max_results)), "key": key}
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    return [parse_youtube_item(i) for i in payload.get("items", [])]


def parse_youtube_item(item: Dict[str, Any]) -> NormalizedPost:
    video_id = ((item.get("id") or {}).get("videoId", "")) or ""
    snippet = item.get("snippet", {}) or {}
    return NormalizedPost(
        platform="youtube",
        platform_post_id=video_id,
        text=f"{snippet.get('title', '')} {snippet.get('description', '')}".strip(),
        author_id=str((snippet.get("channelId", ""))),
        content_type="video",
        created_at=str(snippet.get("publishedAt", "")),
        url=f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
        raw=item,
    )

"""Neo4jStore (Stage2). Driver-injectable; missing creds or server => disabled, never raises at import."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from .schema import (
        BURST_POSTS,
        CONSTRAINTS,
        FOLLOW_EDGE,
        INDEXES,
        RECORD_VELOCITY,
        SUPERSPREADERS_FALLBACK,
        UPSERT_POST,
    )
except ImportError:  # isolated file-path loading in tests
    import importlib.util as _ilu
    import sys as _sys
    from pathlib import Path as _Path
    _base = _Path(__file__).resolve().parent

    def _load(_name: str):
        _mod_name = f"{__name__}.{_name}" if __name__ else _name
        _spec = _ilu.spec_from_file_location(_mod_name, _base / f"{_name}.py")
        _mod = _ilu.module_from_spec(_spec)
        _sys.modules[_mod_name] = _mod
        _spec.loader.exec_module(_mod)
        return _mod

    _schema = _load("schema")
    BURST_POSTS = _schema.BURST_POSTS
    CONSTRAINTS = _schema.CONSTRAINTS
    FOLLOW_EDGE = _schema.FOLLOW_EDGE
    INDEXES = _schema.INDEXES
    RECORD_VELOCITY = _schema.RECORD_VELOCITY
    SUPERSPREADERS_FALLBACK = _schema.SUPERSPREADERS_FALLBACK
    UPSERT_POST = _schema.UPSERT_POST


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Neo4jStore:
    def __init__(self, driver: Any = None, uri: str = "", user: str = "", password: str = ""):
        self._uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self._user = user or os.environ.get("NEO4J_USER", "neo4j")
        self._password = password if password != "" else os.environ.get("NEO4J_PASSWORD", "")
        self._driver = driver  # injected fake in tests
        self._enabled = bool(self._password) or driver is not None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _get_driver(self) -> Any:
        if self._driver is not None:
            return self._driver
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
        return self._driver

    def ensure_schema(self) -> None:
        if not self.enabled:
            return
        driver = self._get_driver()
        with driver.session() as session:
            for stmt in (*CONSTRAINTS, *INDEXES):
                session.run(stmt)

    def upsert_post(self, post: Any, claim_key: str, topic: str = "") -> None:
        if not self.enabled:
            return
        params = {
            "platform": post.platform, "author_id": post.author_id or "unknown",
            "followers": int(getattr(post, "author_followers", 0) or 0),
            "post_id": post.platform_post_id, "text": (post.text or "")[:4000],
            "content_type": post.content_type, "language": post.language or "",
            "likes": int(post.likes or 0), "shares": int(post.shares or 0),
            "comments": int(post.comments or 0), "views": int(post.views or 0),
            "created_at": post.created_at or "", "url": post.url or "",
            "claim_key": claim_key, "topic": topic or claim_key,
        }
        with self._get_driver().session() as session:
            session.run(UPSERT_POST, params)

    def record_velocity(self, platform: str, post_id: str, velocity: float, post: Any = None) -> None:
        if not self.enabled:
            return
        params = {
            "platform": platform, "post_id": post_id, "ts": _utcnow(),
            "velocity": max(0.0, min(1.0, float(velocity))),
            "likes": int(getattr(post, "likes", 0) or 0) if post else 0,
            "shares": int(getattr(post, "shares", 0) or 0) if post else 0,
            "comments": int(getattr(post, "comments", 0) or 0) if post else 0,
            "views": int(getattr(post, "views", 0) or 0) if post else 0,
        }
        with self._get_driver().session() as session:
            session.run(RECORD_VELOCITY, params)

    def add_follow(self, platform: str, src: str, dst: str) -> None:
        if not self.enabled:
            return
        with self._get_driver().session() as session:
            session.run(FOLLOW_EDGE, {"platform": platform, "src": src, "dst": dst})

    def superspreaders(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        with self._get_driver().session() as session:
            result = session.run(SUPERSPREADERS_FALLBACK, {"limit": int(limit)})
            return [dict(r) for r in result]

    def burst_posts(self, since_ts: str, min_velocity: float = 0.6, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        with self._get_driver().session() as session:
            result = session.run(BURST_POSTS, {"since_ts": since_ts, "min_velocity": float(min_velocity), "limit": int(limit)})
            return [dict(r) for r in result]

    def to_zep_payload(self, post: Any, velocity: float, tier: Optional[str] = None) -> Dict[str, Any]:
        """Shape Stage1+2 output for existing Zep ingestion (no I/O here)."""
        return {
            "text": f"[{post.platform} {post.created_at}] @{post.author_id}: {post.text[:1000]}",
            "metadata": {
                "platform": post.platform, "post_id": post.platform_post_id,
                "url": post.url, "velocity": velocity, "tier": tier or "",
                "likes": post.likes, "shares": post.shares,
            },
        }

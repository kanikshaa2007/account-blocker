"""Realtime scheduler loop (Stage3): poll RSS free first, APIs only enrich.

Design: single background thread, per-source intervals, dedup set,
quota buckets, gov-gate + router + Neo4j writes via injected callbacks.
No network or Neo4j required in tests (all I/O injected).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

try:
    from .quota import AdaptiveLanes, make_buckets
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

    _quota = _load("quota")
    AdaptiveLanes = _quota.AdaptiveLanes
    make_buckets = _quota.make_buckets


@dataclass
class RealtimeConfig:
    rss_interval_s: int = 180
    x_interval_s: int = 300
    instagram_interval_s: int = 420
    youtube_interval_s: int = 600
    max_items_per_cycle: int = 30


@dataclass
class RealtimeCollector:
    """Injectable loop: sources + sink are callables, so tests run offline."""

    fetch_rss_items: Callable[[], List[Any]]
    fetch_x_posts: Callable[[], List[Any]]
    fetch_instagram_posts: Callable[[], List[Any]]
    fetch_youtube_posts: Callable[[], List[Any]]
    on_post: Callable[[Any, float], None]  # (NormalizedPost, velocity) -> route+store
    config: RealtimeConfig = field(default_factory=RealtimeConfig)
    lanes: AdaptiveLanes = field(default_factory=AdaptiveLanes)

    def __post_init__(self) -> None:
        self._seen: set[str] = set()
        self._buckets = make_buckets()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.stats: Dict[str, int] = {"rss": 0, "x": 0, "instagram": 0, "youtube": 0, "deduped": 0, "routed": 0}

    def _key(self, post: Any) -> str:
        return f"{getattr(post, 'platform', '?')}:{getattr(post, 'platform_post_id', '?')}"

    def _drain(self, name: str, posts: List[Any]) -> int:
        allowed = self._buckets[name].allow(cost=1) if posts else True
        if not allowed:
            return 0
        fresh: List[Any] = []
        for post in posts[: self.config.max_items_per_cycle]:
            key = self._key(post)
            if key in self._seen:
                self.stats["deduped"] += 1
                continue
            self._seen.add(key)
            fresh.append(post)
        for post in fresh:
            self.on_post(post, 0.0)
            self.stats["routed"] += 1
        self.stats[name] += len(fresh)
        return len(fresh)

    def run_once(self) -> Dict[str, int]:
        """One cycle: RSS always (free trigger), APIs gated by quota."""
        self._drain("rss", list(self.fetch_rss_items() or []))
        self._drain("x", list(self.fetch_x_posts() or []))
        self._drain("instagram", list(self.fetch_instagram_posts() or []))
        self._drain("youtube", list(self.fetch_youtube_posts() or []))
        return dict(self.stats)

    def start_background(self, interval_s: int = 60) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _loop() -> None:
            while not self._stop.is_set():
                try:
                    self.run_once()
                except Exception:
                    pass  # never kill the loop on one bad cycle
                self._stop.wait(interval_s)

        self._stop.clear()
        self._thread = threading.Thread(target=_loop, daemon=True, name="mirofish-realtime")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

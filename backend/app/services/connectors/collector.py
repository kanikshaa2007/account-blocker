"""Collector orchestrator: gather -> gov-gate -> RoutingInput (Stage1)."""
from __future__ import annotations

from typing import Callable, Dict, List

try:
    from .clients import fetch_instagram_hashtag, fetch_x_recent, fetch_youtube_search
    from .models import NormalizedPost
    from .scoring import to_routing_input
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

    _clients = _load("clients")
    _models = _load("models")
    _scoring = _load("scoring")
    fetch_instagram_hashtag = _clients.fetch_instagram_hashtag
    fetch_x_recent = _clients.fetch_x_recent
    fetch_youtube_search = _clients.fetch_youtube_search
    NormalizedPost = _models.NormalizedPost
    to_routing_input = _scoring.to_routing_input

DEFAULT_QUERIES = (
    "government of india fake",
    "PIB fact check",
)


def collect_all(
    queries: tuple[str, ...] = DEFAULT_QUERIES,
    instagram_hashtag: str = "",
    instagram_user_id: str = "",
    fetch: Dict[str, Callable] | None = None,
) -> List[dict]:
    """Collect from all platforms. `fetch` injects fakes for tests/offline runs."""
    fetch = fetch or {}
    fetch_x = fetch.get("x", fetch_x_recent)
    fetch_ig = fetch.get("instagram", fetch_instagram_hashtag)
    fetch_yt = fetch.get("youtube", fetch_youtube_search)

    posts: List[NormalizedPost] = []
    for query in queries:
        posts.extend(fetch_x(query) if fetch_x is fetch_x_recent else fetch_x(query))
        posts.extend(fetch_yt(query) if fetch_yt is fetch_youtube_search else fetch_yt(query))
    if instagram_hashtag and instagram_user_id:
        posts.extend(fetch_ig(instagram_hashtag, instagram_user_id))

    routed: List[dict] = []
    for post in posts:
        try:
            signal = to_routing_input(post)
        except ValueError:
            continue  # off-topic: skip, do not route
        routed.append({"post": post, "signal": signal})
    return routed

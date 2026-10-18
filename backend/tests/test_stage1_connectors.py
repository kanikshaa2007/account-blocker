"""Stage1 connector tests (isolated: no app package import, no network)."""
import importlib.util
import sys
from pathlib import Path

_CONN = Path(__file__).resolve().parents[1] / "app" / "services" / "connectors"


def _load(name):
    mod_name = f"stage1_test_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, _CONN / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_parsers_and_gov_gate():
    clients = _load("clients")
    gov = _load("gov_topics")
    post = clients.parse_x_tweet({
        "id": "123", "text": "PIB says viral Government of India UPI claim is fake",
        "author_id": "a1", "lang": "en",
        "public_metrics": {"like_count": 100, "retweet_count": 50, "reply_count": 10, "impression_count": 1000},
    })
    assert post.platform == "x"
    assert gov.mentions_gov(post.text) is True
    assert gov.mentions_gov("cute cat video") is False

    ig = clients.parse_instagram_media({"id": "ig1", "caption": "PM-KISAN update", "media_type": "VIDEO", "like_count": 5})
    assert ig.content_type == "video"

    yt = clients.parse_youtube_item({"id": {"videoId": "v1"}, "snippet": {"title": "RBI alert", "description": "fake circulating"}})
    assert yt.platform_post_id == "v1"


def test_scoring_and_collector_offline():
    scoring = _load("scoring")
    collector = _load("collector")
    clients = _load("clients")
    viral = clients.parse_x_tweet({
        "id": "9", "text": "Government of India Aadhaar shutdown viral claim",
        "author_id": "a9", "lang": "hi",
        "public_metrics": {"like_count": 5000, "retweet_count": 2000, "reply_count": 500, "impression_count": 200000},
    })
    signal = scoring.to_routing_input(viral)
    assert signal.spread_reliable is True
    assert 0.0 <= signal.harm_if_false <= 1.0

    quiet = clients.parse_x_tweet({"id": "1", "text": "Government of India holiday list", "public_metrics": {}})
    quiet_signal = scoring.to_routing_input(quiet)
    assert quiet_signal.spread_reliable is False  # router fallback path

    routed = collector.collect_all(
        queries=("q1",),
        fetch={
            "x": lambda q: [viral, clients.parse_x_tweet({"id": "2", "text": "cat video", "public_metrics": {"like_count": 9}})],
            "youtube": lambda q: [],
        },
    )
    assert len(routed) == 1  # off-topic cat video skipped
    assert routed[0]["post"].platform_post_id == "9"

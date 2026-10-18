"""Stage8 live-source parser tests (isolated: sample XML, no network)."""
import importlib.util
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1] / "app" / "services" / "connectors"


def _load(name):
    mod_name = f"stage8_test_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, _BASE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


REDDIT_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>t3_abc123</id><link href="https://www.reddit.com/r/india/comments/abc123/x/"/>
<author><name>/u/test_user</name><uri>https://www.reddit.com/user/test_user</uri></author>
<title>Government of India UPI update</title><updated>2026-10-16T00:00:00+00:00</updated></entry>
<entry><id>t3_def456</id><link href="https://x/y"/>
<author><name>/u/other</name></author><title>cat video</title><updated>2026-10-16T00:00:00+00:00</updated></entry>
</feed>"""

YOUTUBE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
<author><name>DD News</name></author>
<entry><yt:videoId>vid001</yt:videoId><title>PIB briefing today</title>
<published>2026-10-16T00:00:00+00:00</published></entry>
</feed>"""


def test_reddit_rss_parse():
    live = _load("live_sources")
    posts = live.parse_reddit_rss(REDDIT_RSS)
    assert len(posts) == 2
    assert posts[0].platform == "reddit"
    assert posts[0].platform_post_id == "abc123"
    assert posts[0].author_id == "test_user"
    assert posts[0].url.startswith("https://www.reddit.com")
    assert live.parse_reddit_rss("not xml") == []


def test_youtube_rss_parse():
    live = _load("live_sources")
    posts = live.parse_youtube_rss(YOUTUBE_RSS, channel_id="UCx")
    assert len(posts) == 1
    assert posts[0].platform == "youtube"
    assert posts[0].platform_post_id == "vid001"
    assert posts[0].author_id == "DD News"
    assert posts[0].url == "https://www.youtube.com/watch?v=vid001"
    assert live.parse_youtube_rss("<html>bot check</html>") == []

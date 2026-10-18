"""Cypher schema + statement builders (Stage2, pure strings, no I/O)."""
from __future__ import annotations

CONSTRAINTS = (
    "CREATE CONSTRAINT account_key IF NOT EXISTS FOR (a:Account) REQUIRE (a.platform, a.account_id) IS UNIQUE",
    "CREATE CONSTRAINT post_key IF NOT EXISTS FOR (p:Post) REQUIRE (p.platform, p.post_id) IS UNIQUE",
    "CREATE CONSTRAINT claim_key IF NOT EXISTS FOR (c:Claim) REQUIRE c.claim_key IS UNIQUE",
)

INDEXES = (
    "CREATE INDEX post_created IF NOT EXISTS FOR (p:Post) ON (p.created_at)",
    "CREATE INDEX velocity_ts IF NOT EXISTS FOR (v:VelocitySnapshot) ON (v.ts)",
)

UPSERT_POST = """
MERGE (a:Account {platform: $platform, account_id: $author_id})
SET a.followers = $followers
MERGE (p:Post {platform: $platform, post_id: $post_id})
SET p.text = $text, p.content_type = $content_type, p.language = $language,
    p.likes = $likes, p.shares = $shares, p.comments = $comments, p.views = $views,
    p.created_at = $created_at, p.url = $url
MERGE (a)-[:POSTED]->(p)
MERGE (c:Claim {claim_key: $claim_key})
SET c.topic = $topic
MERGE (p)-[:HAS_CLAIM]->(c)
"""

RECORD_VELOCITY = """
MATCH (p:Post {platform: $platform, post_id: $post_id})
CREATE (v:VelocitySnapshot {ts: $ts, velocity: $velocity, likes: $likes, shares: $shares, comments: $comments, views: $views})
CREATE (p)-[:HAS_VELOCITY]->(v)
"""

FOLLOW_EDGE = """
MERGE (a:Account {platform: $platform, account_id: $src})
MERGE (b:Account {platform: $platform, account_id: $dst})
MERGE (a)-[:FOLLOWS]->(b)
"""

# Fallback super-spreaders when GDS is unavailable: degree + follower weight.
SUPERSPREADERS_FALLBACK = """
MATCH (a:Account)-[:POSTED]->(p:Post)
WITH a, count(p) AS posts, sum(p.shares + p.likes) AS engagement, max(a.followers) AS followers
RETURN a.platform AS platform, a.account_id AS account_id, posts, engagement, followers,
       (posts * 2 + log(1 + engagement) + log(1 + followers) / 10.0) AS spread_score
ORDER BY spread_score DESC LIMIT $limit
"""

BURST_POSTS = """
MATCH (p:Post)-[:HAS_VELOCITY]->(v:VelocitySnapshot)
WHERE v.ts >= $since_ts
WITH p, max(v.velocity) AS peak, count(v) AS snaps
WHERE peak >= $min_velocity
RETURN p.platform AS platform, p.post_id AS post_id, peak, snaps
ORDER BY peak DESC LIMIT $limit
"""

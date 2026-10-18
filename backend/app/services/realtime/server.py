"""Flask webhook blueprint (Stage3): Instagram + YouTube push receivers.

Register in app factory when needed:
    from app.services.realtime.server import realtime_bp
    app.register_blueprint(realtime_bp, url_prefix='/api/realtime')
"""
from __future__ import annotations

try:
    from flask import Blueprint, jsonify, request
except ImportError:  # tests without flask installed
    Blueprint = None  # type: ignore

try:
    from .webhooks import parse_instagram_webhook_payload, verify_instagram_webhook, verify_pubsubhubbub
except ImportError:
    from webhooks import parse_instagram_webhook_payload, verify_instagram_webhook, verify_pubsubhubbub  # type: ignore

if Blueprint is not None:
    realtime_bp = Blueprint("realtime", __name__)

    @realtime_bp.route("/instagram/webhook", methods=["GET", "POST"])
    def instagram_webhook():
        if request.method == "GET":
            ok, challenge = verify_instagram_webhook(dict(request.args))
            return (challenge, 200) if ok else ("forbidden", 403)
        ids = parse_instagram_webhook_payload(request.get_json(silent=True) or {})
        # Push path: enqueue IDs for Graph API enrichment (quota-free receive).
        return jsonify({"received": len(ids), "ids": ids[:50]})

    @realtime_bp.route("/youtube/notify", methods=["GET", "POST"])
    def youtube_notify():
        if request.method == "GET":
            ok, challenge = verify_pubsubhubbub(dict(request.args))
            return (challenge, 200) if ok else ("forbidden", 403)
        # PubSubHubbub POST is an Atom XML ping; enrichment fetches video details.
        return jsonify({"received": True})
else:
    realtime_bp = None  # type: ignore

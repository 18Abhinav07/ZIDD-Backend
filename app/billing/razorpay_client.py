"""Razorpay thin wrapper. The `razorpay` SDK is imported LAZILY inside _client()
so this module imports cleanly when the package is absent and so tests can
monkeypatch create_order / verify_webhook_signature without the SDK.
"""
import hashlib
import hmac

from app.config import get_settings


def _client():
    import razorpay  # lazy: only needed when actually creating a real order

    s = get_settings()
    return razorpay.Client(auth=(s.razorpay_key_id, s.razorpay_key_secret))


def create_order(amount_paise: int, receipt: str) -> dict:
    """Create a Razorpay order; the returned dict contains the order 'id'."""
    client = _client()
    return client.order.create(
        {"amount": amount_paise, "currency": "INR", "receipt": receipt}
    )


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """HMAC-SHA256 verify a webhook payload against the configured secret."""
    secret = get_settings().razorpay_webhook_secret.encode("utf-8")
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

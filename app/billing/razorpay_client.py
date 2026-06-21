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


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify a Razorpay Checkout success signature.

    Checkout's success handler returns razorpay_payment_id / razorpay_order_id /
    razorpay_signature, where the signature is HMAC-SHA256 of "order_id|payment_id"
    keyed by the API SECRET (distinct from the webhook signature, which is over the
    raw webhook body keyed by the webhook secret). Verifying it server-side is the
    standard accepted proof of a genuine payment, so credits can be granted on
    success without waiting on — or being reachable by — the webhook (the latter
    is impossible on localhost)."""
    if not (order_id and payment_id and signature):
        return False
    secret = get_settings().razorpay_key_secret.encode("utf-8")
    msg = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(secret, msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

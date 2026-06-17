import os
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)
from app.config import Settings

def test_settings_expose_billing_fields():
    s = Settings()
    assert s.razorpay_key_id == ""
    assert s.razorpay_key_secret == ""
    assert s.razorpay_webhook_secret == ""
    assert s.welcome_credits == 50

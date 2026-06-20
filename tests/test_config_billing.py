import os
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)
from app.config import Settings

def test_settings_expose_billing_fields(monkeypatch):
    # Hermetic by design: this asserts the *schema defaults* (the contract that
    # these fields exist and default empty), NOT whatever .env sits in the CWD.
    # A real localhost run populates .env with live Razorpay sandbox keys, which
    # Settings() would otherwise read — so disable .env loading (_env_file=None)
    # and clear any exported RAZORPAY_* first. The defaults must hold regardless.
    for var in ("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.razorpay_key_id == ""
    assert s.razorpay_key_secret == ""
    assert s.razorpay_webhook_secret == ""
    assert s.welcome_credits == 50

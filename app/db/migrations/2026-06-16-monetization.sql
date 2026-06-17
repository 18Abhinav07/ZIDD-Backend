CREATE TABLE IF NOT EXISTS content_unlocks (
    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
    scope TEXT NOT NULL, ref_id TEXT NOT NULL,
    credits_spent INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, scope, ref_id));
CREATE INDEX IF NOT EXISTS idx_unlocks_user ON content_unlocks(user_id);
CREATE TABLE IF NOT EXISTS purchases (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
    pack_id TEXT NOT NULL, credits INTEGER NOT NULL,
    amount_paise INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'created',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
ALTER TABLE content_unlocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;

-- Unified beta-to-paid credit wallet.
-- Preserve existing balances by backfilling each non-zero legacy balance into
-- one non-expiring lot, then make every future spend traceable to its lots.

BEGIN;

CREATE TABLE IF NOT EXISTS public.credit_lots (
    id                BIGSERIAL PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    source            TEXT NOT NULL CHECK (
        source IN ('beta_grant', 'paid_purchase', 'promo', 'legacy_migrated')
    ),
    grant_key         TEXT NOT NULL,
    original_credits  INTEGER NOT NULL CHECK (original_credits >= 0),
    remaining_credits INTEGER NOT NULL CHECK (
        remaining_credits >= 0 AND remaining_credits <= original_credits
    ),
    expires_at        TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, grant_key)
);

CREATE INDEX IF NOT EXISTS idx_credit_lots_user_expiry
    ON public.credit_lots(user_id, expires_at, created_at, id);

CREATE TABLE IF NOT EXISTS public.credit_lot_spends (
    transaction_id BIGINT NOT NULL REFERENCES public.credit_transactions(id),
    lot_id         BIGINT NOT NULL REFERENCES public.credit_lots(id),
    amount         INTEGER NOT NULL CHECK (amount > 0),
    PRIMARY KEY (transaction_id, lot_id)
);

CREATE INDEX IF NOT EXISTS idx_credit_lot_spends_lot
    ON public.credit_lot_spends(lot_id);

INSERT INTO public.credit_lots (
    user_id,
    source,
    grant_key,
    original_credits,
    remaining_credits
)
SELECT
    user_id,
    'legacy_migrated',
    'legacy_balance_v1',
    credits,
    credits
FROM public.learner_profiles
WHERE credits > 0
ON CONFLICT (user_id, grant_key) DO NOTHING;

ALTER TABLE public.credit_lots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_lot_spends ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.credit_lots FROM anon;
REVOKE ALL ON TABLE public.credit_lots FROM authenticated;
REVOKE ALL ON TABLE public.credit_lots FROM PUBLIC;
REVOKE ALL ON TABLE public.credit_lot_spends FROM anon;
REVOKE ALL ON TABLE public.credit_lot_spends FROM authenticated;
REVOKE ALL ON TABLE public.credit_lot_spends FROM PUBLIC;

COMMIT;

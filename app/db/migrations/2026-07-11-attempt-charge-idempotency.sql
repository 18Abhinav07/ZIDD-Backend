-- Make metered session starts crash-safe. A stale retry with the same client
-- start id reuses the original debit instead of charging a second time.

ALTER TABLE public.credit_transactions
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_transactions_idempotency_key
    ON public.credit_transactions(user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

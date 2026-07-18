-- Keep vectors comparable only within the embedding provider/model that made them.
-- Existing rows remain NULL provenance and are intentionally ignored by retrieval.
ALTER TABLE public.memory_entries
    ADD COLUMN IF NOT EXISTS embedding_provider TEXT,
    ADD COLUMN IF NOT EXISTS embedding_model TEXT;

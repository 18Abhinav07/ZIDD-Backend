ALTER TABLE school_placement_reports
    ADD COLUMN IF NOT EXISTS deviation_note TEXT NOT NULL DEFAULT '';

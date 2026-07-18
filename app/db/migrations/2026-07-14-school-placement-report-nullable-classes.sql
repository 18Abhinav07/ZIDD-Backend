-- Incomplete placement reports cannot truthfully publish a class estimate or
-- active learning class. Established reports continue storing integer values.
ALTER TABLE public.school_placement_reports
    ALTER COLUMN evaluated_class_no DROP NOT NULL,
    ALTER COLUMN active_learning_class_no DROP NOT NULL;

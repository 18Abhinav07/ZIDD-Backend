-- Correct one verified source-map metadata error without weakening the
-- curriculum-release immutability trigger for normal application writes.
-- The exact old digest and field value are required so an unexpected row is
-- never rewritten silently.

DO $preimage$
DECLARE
    current_digest TEXT;
    current_genre TEXT;
BEGIN
    SELECT release_digest,
           manifest #>> '{units,0,modules,0,source_genre}'
      INTO current_digest, current_genre
      FROM public.school_curriculum_releases
     WHERE curriculum_release_id = 'english_cbse_2026_27_c5_eesa1'
     FOR UPDATE;

    IF current_digest IS NULL THEN
        RAISE EXCEPTION 'school_curriculum_release_correction_missing:c5_eesa1'
            USING ERRCODE = '55000';
    END IF;
    IF current_digest = 'e7524ce60fa8d8cd4e40c8e0b5170047d085e0a42311831d4fc5637caec7a83b'
       AND current_genre = 'poem' THEN
        RETURN;
    END IF;
    IF current_digest <> 'b2af0483dd918273dc2d5c6c9fb785da1063a33fa69ca7d628a6cf5f4950bf6b'
       OR current_genre <> 'play' THEN
        RAISE EXCEPTION
            'school_curriculum_release_correction_preimage_mismatch:%:%',
            current_digest,
            current_genre
            USING ERRCODE = '55000';
    END IF;
END;
$preimage$;

ALTER TABLE public.school_curriculum_releases
    DISABLE TRIGGER school_curriculum_releases_immutable;

UPDATE public.school_curriculum_releases
   SET manifest = jsonb_set(
           manifest,
           '{units,0,modules,0,source_genre}',
           '"poem"'::jsonb,
           false
       ),
       release_digest = 'e7524ce60fa8d8cd4e40c8e0b5170047d085e0a42311831d4fc5637caec7a83b',
       updated_at = now()
 WHERE curriculum_release_id = 'english_cbse_2026_27_c5_eesa1'
   AND release_digest = 'b2af0483dd918273dc2d5c6c9fb785da1063a33fa69ca7d628a6cf5f4950bf6b';

ALTER TABLE public.school_curriculum_releases
    ENABLE TRIGGER school_curriculum_releases_immutable;

DO $postcondition$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM public.school_curriculum_releases
         WHERE curriculum_release_id = 'english_cbse_2026_27_c5_eesa1'
           AND release_digest = 'e7524ce60fa8d8cd4e40c8e0b5170047d085e0a42311831d4fc5637caec7a83b'
           AND manifest #>> '{units,0,modules,0,source_genre}' = 'poem'
    ) THEN
        RAISE EXCEPTION 'school_curriculum_release_correction_postcondition_failed'
            USING ERRCODE = '55000';
    END IF;
END;
$postcondition$;

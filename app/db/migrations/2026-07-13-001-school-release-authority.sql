CREATE TABLE IF NOT EXISTS public.school_curriculum_releases (
    curriculum_release_id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    class_no INTEGER NOT NULL CHECK (class_no BETWEEN 1 AND 12),
    academic_year TEXT NOT NULL,
    manifest JSONB NOT NULL,
    release_digest TEXT NOT NULL CHECK (release_digest ~ '^[0-9a-f]{64}$'),
    status TEXT NOT NULL CHECK (status IN ('current', 'retired')),
    effective_from DATE NOT NULL,
    effective_through DATE NOT NULL,
    retired_on DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT school_curriculum_releases_identity_digest_unique
        UNIQUE (board_id, subject_id, class_no, academic_year, release_digest),
    CHECK (effective_through >= effective_from),
    CHECK (retired_on IS NULL OR retired_on BETWEEN effective_from AND effective_through)
);

CREATE OR REPLACE FUNCTION public.reject_school_curriculum_release_identity_change()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    RAISE EXCEPTION 'school_curriculum_release_immutable:%',
        OLD.curriculum_release_id
        USING ERRCODE = '55000';
    RETURN OLD;
END;
$function$;

DROP TRIGGER IF EXISTS school_curriculum_releases_immutable
    ON public.school_curriculum_releases;
CREATE TRIGGER school_curriculum_releases_immutable
BEFORE UPDATE OR DELETE ON public.school_curriculum_releases
FOR EACH ROW
EXECUTE FUNCTION public.reject_school_curriculum_release_identity_change();

INSERT INTO public.school_curriculum_releases
    (curriculum_release_id, board_id, subject_id, class_no, academic_year,
     manifest, release_digest, status, effective_from, effective_through,
     retired_on)
VALUES
    ('english_cbse_2026_27_c2_bemr1', 'cbse', 'english', 2, '2026-27',
     $release_0${"academic_year":"2026-27","board_id":"cbse","book_code":"bemr1","book_title":"Mridang","class_no":2,"curriculum_release_id":"english_cbse_2026_27_c2_bemr1","edition_history":[{"kind":"first_edition","month":"May","year":2023},{"kind":"reprint","month":"March","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"February","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-434-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Sing","mode":"singing","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Read","mode":"reading","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Draw","mode":"drawing","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Say","mode":"pronunciation","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"bd8b09e5eec4502a47bcaa5b46a0e4cb3cee9643fd5e20918a8b72a496ac22ca","source_size_bytes":2812044,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c2_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"My Bicycle"},{"kind":"picture_reading","module_id":"eng_c2_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c2_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"It is Fun"},{"kind":"lesson","module_id":"eng_c2_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Seeing without Seeing"}],"order":2,"title":"Welcome to My World","unit_id":"eng_c2_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Come Back Soon"},{"kind":"lesson","module_id":"eng_c2_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Between Home and School"},{"kind":"lesson","module_id":"eng_c2_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"This is My Town"}],"order":3,"title":"Going Places","unit_id":"eng_c2_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"A Show of Clouds"},{"kind":"lesson","module_id":"eng_c2_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"My Name"},{"kind":"lesson","module_id":"eng_c2_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Crow"},{"kind":"lesson","module_id":"eng_c2_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"The Smart Monkey"}],"order":4,"title":"Life Around Us","unit_id":"eng_c2_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Little Drops of Water"},{"kind":"lesson","module_id":"eng_c2_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"mixed","title":"We are all Indians"}],"order":5,"title":"Harmony","unit_id":"eng_c2_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_0$::jsonb,
     'a03eabb3015cf0917e54894caa5c3b7526671537bdfb58b76493579d41964c19', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
    ('english_cbse_2026_27_c3_cesa1', 'cbse', 'english', 3, '2026-27',
     $release_1${"academic_year":"2026-27","board_id":"cbse","book_code":"cesa1","book_title":"Santoor","class_no":3,"curriculum_release_id":"english_cbse_2026_27_c3_cesa1","edition_history":[{"kind":"first_edition","month":"April","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-991-7","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c3_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Our National Anthem"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"6b0ce2a24327c9fad6acd997b38a12ce4bff961e729856133c4474656b424816","source_size_bytes":1956951,"subject_id":"english","units":[{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Colours"},{"kind":"lesson","module_id":"eng_c3_u01_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Badal and Moti"},{"kind":"lesson","module_id":"eng_c3_u01_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Best Friends"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c3_u01"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Out in the Garden"},{"kind":"lesson","module_id":"eng_c3_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"play","title":"Talking Toys"},{"kind":"lesson","module_id":"eng_c3_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Paper Boats"},{"kind":"self_assessment","module_id":"eng_c3_u02_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":2,"title":"Toys and Games","unit_id":"eng_c3_u02"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Big Laddoo"},{"kind":"lesson","module_id":"eng_c3_u03_m03","order":3,"phase_0_public_display_title":"Thank God!","source_genre":"poem","title":"Thank God"},{"kind":"lesson","module_id":"eng_c3_u03_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"Madhu's Wish"}],"order":3,"title":"Good Food","unit_id":"eng_c3_u03"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Night"},{"kind":"lesson","module_id":"eng_c3_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Chanda Mama Counts the Stars"},{"kind":"lesson","module_id":"eng_c3_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"informational","title":"Chandrayaan"},{"kind":"self_assessment","module_id":"eng_c3_u04_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":4,"title":"The Sky","unit_id":"eng_c3_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_1$::jsonb,
     '3330785de9b1378ef5da4dd702883d9bffc470d8aa2effec33832c5c9ff3f8b1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
    ('english_cbse_2026_27_c4_desa1', 'cbse', 'english', 4, '2026-27',
     $release_2${"academic_year":"2026-27","board_id":"cbse","book_code":"desa1","book_title":"Santoor","class_no":4,"curriculum_release_id":"english_cbse_2026_27_c4_desa1","edition_history":[{"kind":"first_edition","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-932-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Read","mode":"reading","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Recite","mode":"recitation","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":8,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":9,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c4_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Constitution of India"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"ab890381b64c55094ea0651adb3e2c68d32a8341665d587ef90873fb9ab35f9a","source_size_bytes":6888606,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c4_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Together We Can"},{"kind":"lesson","module_id":"eng_c4_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Tinkling Bells"},{"kind":"lesson","module_id":"eng_c4_u01_m03","order":3,"phase_0_public_display_title":"Be Smart, Be Safe","source_genre":"informational","title":"Be Smart Be Safe"}],"order":1,"title":"My Land","unit_id":"eng_c4_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"One Thing at a Time"},{"kind":"lesson","module_id":"eng_c4_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Old Stag"},{"kind":"lesson","module_id":"eng_c4_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Braille"},{"kind":"self_assessment","module_id":"eng_c4_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 1"}],"order":2,"title":"My Beautiful World","unit_id":"eng_c4_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u03_m01","order":1,"phase_0_public_display_title":"Fit Body, Fit Mind, Fit Nation","source_genre":"informational","title":"Fit Body Fit Mind Fit Nation"},{"kind":"lesson","module_id":"eng_c4_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Lagori Champions"},{"kind":"lesson","module_id":"eng_c4_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Hekko"}],"order":3,"title":"Fun with Games","unit_id":"eng_c4_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Swing"},{"kind":"lesson","module_id":"eng_c4_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"A Journey to the Magical Mountains"},{"kind":"lesson","module_id":"eng_c4_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Maheshwar"},{"kind":"self_assessment","module_id":"eng_c4_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 2"}],"order":4,"title":"Up High","unit_id":"eng_c4_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_2$::jsonb,
     '426767f21ba2f38082aca8a2b05da202055e423245b3ece43c9c55f92b571ab1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
    ('english_cbse_2026_27_c5_eesa1', 'cbse', 'english', 5, '2026-27',
     $release_3${"academic_year":"2026-27","board_id":"cbse","book_code":"eesa1","book_title":"Santoor","class_no":5,"curriculum_release_id":"english_cbse_2026_27_c5_eesa1","edition_history":[{"kind":"first_edition","month":"June","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-062-3","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c5_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Gandhiji's Talisman"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"7ecaefaa0ed0ada410282fa18ab5a944b8e818cbc897993404cc4924a2682e5d","source_size_bytes":4469179,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c5_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"play","title":"Papa's Spectacles"},{"kind":"lesson","module_id":"eng_c5_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"Gone with the Scooter"}],"order":1,"title":"Let's Have Fun","unit_id":"eng_c5_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Rainbow"},{"kind":"lesson","module_id":"eng_c5_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Wise Parrot"},{"kind":"self_assessment","module_id":"eng_c5_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 1"}],"order":2,"title":"My Colourful World","unit_id":"eng_c5_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Frog"},{"kind":"lesson","module_id":"eng_c5_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"What a Tank!"}],"order":3,"title":"Water","unit_id":"eng_c5_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"story","title":"Gilli Danda"},{"kind":"lesson","module_id":"eng_c5_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"play","title":"The Decision of the Panchayat"}],"order":4,"title":"Ups and Downs","unit_id":"eng_c5_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Vocation"},{"kind":"lesson","module_id":"eng_c5_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"Glass Bangles"},{"kind":"self_assessment","module_id":"eng_c5_u05_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 2"}],"order":5,"title":"Work is Worship","unit_id":"eng_c5_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_3$::jsonb,
     'b2af0483dd918273dc2d5c6c9fb785da1063a33fa69ca7d628a6cf5f4950bf6b', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date)
ON CONFLICT (curriculum_release_id) DO NOTHING;

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_curriculum_releases_one_current
ON public.school_curriculum_releases(board_id, subject_id, class_no, academic_year)
WHERE status = 'current';

DO $seed_validation$
DECLARE
    mismatch_count INTEGER;
BEGIN
    SELECT count(*)
    INTO mismatch_count
    FROM (
        VALUES
            ('english_cbse_2026_27_c2_bemr1', 'cbse', 'english', 2, '2026-27',
             $expected_0${"academic_year":"2026-27","board_id":"cbse","book_code":"bemr1","book_title":"Mridang","class_no":2,"curriculum_release_id":"english_cbse_2026_27_c2_bemr1","edition_history":[{"kind":"first_edition","month":"May","year":2023},{"kind":"reprint","month":"March","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"February","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-434-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Sing","mode":"singing","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Read","mode":"reading","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Draw","mode":"drawing","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Say","mode":"pronunciation","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"bd8b09e5eec4502a47bcaa5b46a0e4cb3cee9643fd5e20918a8b72a496ac22ca","source_size_bytes":2812044,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c2_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"My Bicycle"},{"kind":"picture_reading","module_id":"eng_c2_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c2_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"It is Fun"},{"kind":"lesson","module_id":"eng_c2_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Seeing without Seeing"}],"order":2,"title":"Welcome to My World","unit_id":"eng_c2_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Come Back Soon"},{"kind":"lesson","module_id":"eng_c2_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Between Home and School"},{"kind":"lesson","module_id":"eng_c2_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"This is My Town"}],"order":3,"title":"Going Places","unit_id":"eng_c2_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"A Show of Clouds"},{"kind":"lesson","module_id":"eng_c2_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"My Name"},{"kind":"lesson","module_id":"eng_c2_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Crow"},{"kind":"lesson","module_id":"eng_c2_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"The Smart Monkey"}],"order":4,"title":"Life Around Us","unit_id":"eng_c2_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Little Drops of Water"},{"kind":"lesson","module_id":"eng_c2_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"mixed","title":"We are all Indians"}],"order":5,"title":"Harmony","unit_id":"eng_c2_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_0$::jsonb,
             'a03eabb3015cf0917e54894caa5c3b7526671537bdfb58b76493579d41964c19', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
            ('english_cbse_2026_27_c3_cesa1', 'cbse', 'english', 3, '2026-27',
             $expected_1${"academic_year":"2026-27","board_id":"cbse","book_code":"cesa1","book_title":"Santoor","class_no":3,"curriculum_release_id":"english_cbse_2026_27_c3_cesa1","edition_history":[{"kind":"first_edition","month":"April","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-991-7","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c3_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Our National Anthem"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"6b0ce2a24327c9fad6acd997b38a12ce4bff961e729856133c4474656b424816","source_size_bytes":1956951,"subject_id":"english","units":[{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Colours"},{"kind":"lesson","module_id":"eng_c3_u01_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Badal and Moti"},{"kind":"lesson","module_id":"eng_c3_u01_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Best Friends"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c3_u01"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Out in the Garden"},{"kind":"lesson","module_id":"eng_c3_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"play","title":"Talking Toys"},{"kind":"lesson","module_id":"eng_c3_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Paper Boats"},{"kind":"self_assessment","module_id":"eng_c3_u02_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":2,"title":"Toys and Games","unit_id":"eng_c3_u02"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Big Laddoo"},{"kind":"lesson","module_id":"eng_c3_u03_m03","order":3,"phase_0_public_display_title":"Thank God!","source_genre":"poem","title":"Thank God"},{"kind":"lesson","module_id":"eng_c3_u03_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"Madhu's Wish"}],"order":3,"title":"Good Food","unit_id":"eng_c3_u03"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Night"},{"kind":"lesson","module_id":"eng_c3_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Chanda Mama Counts the Stars"},{"kind":"lesson","module_id":"eng_c3_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"informational","title":"Chandrayaan"},{"kind":"self_assessment","module_id":"eng_c3_u04_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":4,"title":"The Sky","unit_id":"eng_c3_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_1$::jsonb,
             '3330785de9b1378ef5da4dd702883d9bffc470d8aa2effec33832c5c9ff3f8b1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
            ('english_cbse_2026_27_c4_desa1', 'cbse', 'english', 4, '2026-27',
             $expected_2${"academic_year":"2026-27","board_id":"cbse","book_code":"desa1","book_title":"Santoor","class_no":4,"curriculum_release_id":"english_cbse_2026_27_c4_desa1","edition_history":[{"kind":"first_edition","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-932-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Read","mode":"reading","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Recite","mode":"recitation","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":8,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":9,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c4_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Constitution of India"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"ab890381b64c55094ea0651adb3e2c68d32a8341665d587ef90873fb9ab35f9a","source_size_bytes":6888606,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c4_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Together We Can"},{"kind":"lesson","module_id":"eng_c4_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Tinkling Bells"},{"kind":"lesson","module_id":"eng_c4_u01_m03","order":3,"phase_0_public_display_title":"Be Smart, Be Safe","source_genre":"informational","title":"Be Smart Be Safe"}],"order":1,"title":"My Land","unit_id":"eng_c4_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"One Thing at a Time"},{"kind":"lesson","module_id":"eng_c4_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Old Stag"},{"kind":"lesson","module_id":"eng_c4_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Braille"},{"kind":"self_assessment","module_id":"eng_c4_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 1"}],"order":2,"title":"My Beautiful World","unit_id":"eng_c4_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u03_m01","order":1,"phase_0_public_display_title":"Fit Body, Fit Mind, Fit Nation","source_genre":"informational","title":"Fit Body Fit Mind Fit Nation"},{"kind":"lesson","module_id":"eng_c4_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Lagori Champions"},{"kind":"lesson","module_id":"eng_c4_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Hekko"}],"order":3,"title":"Fun with Games","unit_id":"eng_c4_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Swing"},{"kind":"lesson","module_id":"eng_c4_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"A Journey to the Magical Mountains"},{"kind":"lesson","module_id":"eng_c4_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Maheshwar"},{"kind":"self_assessment","module_id":"eng_c4_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 2"}],"order":4,"title":"Up High","unit_id":"eng_c4_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_2$::jsonb,
             '426767f21ba2f38082aca8a2b05da202055e423245b3ece43c9c55f92b571ab1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
            ('english_cbse_2026_27_c5_eesa1', 'cbse', 'english', 5, '2026-27',
             $expected_3${"academic_year":"2026-27","board_id":"cbse","book_code":"eesa1","book_title":"Santoor","class_no":5,"curriculum_release_id":"english_cbse_2026_27_c5_eesa1","edition_history":[{"kind":"first_edition","month":"June","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-062-3","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c5_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Gandhiji's Talisman"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"7ecaefaa0ed0ada410282fa18ab5a944b8e818cbc897993404cc4924a2682e5d","source_size_bytes":4469179,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c5_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"play","title":"Papa's Spectacles"},{"kind":"lesson","module_id":"eng_c5_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"Gone with the Scooter"}],"order":1,"title":"Let's Have Fun","unit_id":"eng_c5_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Rainbow"},{"kind":"lesson","module_id":"eng_c5_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Wise Parrot"},{"kind":"self_assessment","module_id":"eng_c5_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 1"}],"order":2,"title":"My Colourful World","unit_id":"eng_c5_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Frog"},{"kind":"lesson","module_id":"eng_c5_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"What a Tank!"}],"order":3,"title":"Water","unit_id":"eng_c5_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"story","title":"Gilli Danda"},{"kind":"lesson","module_id":"eng_c5_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"play","title":"The Decision of the Panchayat"}],"order":4,"title":"Ups and Downs","unit_id":"eng_c5_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Vocation"},{"kind":"lesson","module_id":"eng_c5_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"Glass Bangles"},{"kind":"self_assessment","module_id":"eng_c5_u05_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 2"}],"order":5,"title":"Work is Worship","unit_id":"eng_c5_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_3$::jsonb,
             'b2af0483dd918273dc2d5c6c9fb785da1063a33fa69ca7d628a6cf5f4950bf6b', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date)
    ) AS expected(
        curriculum_release_id,
        board_id,
        subject_id,
        class_no,
        academic_year,
        manifest,
        release_digest,
        status,
        effective_from,
        effective_through,
        retired_on
    )
    LEFT JOIN public.school_curriculum_releases AS actual
      ON actual.curriculum_release_id = expected.curriculum_release_id
    WHERE actual.curriculum_release_id IS NULL
       OR actual.board_id IS DISTINCT FROM expected.board_id
       OR actual.subject_id IS DISTINCT FROM expected.subject_id
       OR actual.class_no IS DISTINCT FROM expected.class_no
       OR actual.academic_year IS DISTINCT FROM expected.academic_year
       OR actual.manifest IS DISTINCT FROM expected.manifest
       OR actual.release_digest IS DISTINCT FROM expected.release_digest
       OR actual.status IS DISTINCT FROM expected.status
       OR actual.effective_from IS DISTINCT FROM expected.effective_from
       OR actual.effective_through IS DISTINCT FROM expected.effective_through
       OR actual.retired_on IS DISTINCT FROM expected.retired_on;

    IF mismatch_count <> 0 THEN
        RAISE EXCEPTION 'school_curriculum_release_seed_mismatch:%', mismatch_count
            USING ERRCODE = '55000';
    END IF;
END;
$seed_validation$;


ALTER TABLE public.school_migration_markers
    ADD COLUMN IF NOT EXISTS file_sha256 TEXT,
    ADD COLUMN IF NOT EXISTS applied_at TIMESTAMPTZ;

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_migration_markers'::regclass
          AND conname = 'school_migration_markers_file_sha256'
    ) THEN
        ALTER TABLE public.school_migration_markers
            ADD CONSTRAINT school_migration_markers_file_sha256
            CHECK (file_sha256 IS NULL OR file_sha256 ~ '^[0-9a-f]{64}$');
    END IF;
END;
$migration$;

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS coach_avatar_id TEXT,
    ADD COLUMN IF NOT EXISTS coach_palette_id TEXT;

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_profile_versions'::regclass
          AND conname = 'school_profile_versions_coach_identity'
    ) THEN
        ALTER TABLE public.school_profile_versions
            ADD CONSTRAINT school_profile_versions_coach_identity
            CHECK (
                (coach_avatar_id IS NULL AND coach_palette_id IS NULL)
                OR (
                    coach_avatar_id = coach_palette_id
                    AND coach_avatar_id IN (
                        'stuttering_sam', 'fluent_finn', 'brave_bella',
                        'quiet_quint', 'tech_black', 'casual_purple',
                        'casual_male', 'casual_female', 'casual_blue'
                    )
                )
            );
    END IF;
END;
$migration$;

WITH avatar_authority AS (
    SELECT ARRAY[
        'stuttering_sam', 'fluent_finn', 'brave_bella',
        'quiet_quint', 'tech_black', 'casual_purple',
        'casual_male', 'casual_female', 'casual_blue'
    ]::text[] AS avatar_ids
),
profile_backfill AS (
    SELECT profile.profile_version_id,
           authority.avatar_ids[
               1 + (
                   get_byte(
                       decode(md5(profile.profile_version_id::text), 'hex'),
                       0
                   ) % array_length(authority.avatar_ids, 1)
               )
           ] AS avatar_id
    FROM public.school_profile_versions AS profile
    CROSS JOIN avatar_authority AS authority
    WHERE profile.coach_avatar_id IS NULL
      AND profile.coach_palette_id IS NULL
)
UPDATE public.school_profile_versions AS profile
SET coach_avatar_id = backfill.avatar_id,
    coach_palette_id = backfill.avatar_id
FROM profile_backfill AS backfill
WHERE profile.profile_version_id = backfill.profile_version_id;

ALTER TABLE public.school_sessions
    ADD COLUMN IF NOT EXISTS curriculum_release_id TEXT,
    ADD COLUMN IF NOT EXISTS taxonomy_version TEXT,
    ADD COLUMN IF NOT EXISTS certification_epoch TEXT;

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_sessions'::regclass
          AND conname = 'school_sessions_curriculum_release_id_fkey'
    ) THEN
        ALTER TABLE public.school_sessions
            ADD CONSTRAINT school_sessions_curriculum_release_id_fkey
            FOREIGN KEY (curriculum_release_id)
            REFERENCES public.school_curriculum_releases(curriculum_release_id);
    END IF;
END;
$migration$;

ALTER TABLE public.school_placement_reports
    ADD COLUMN IF NOT EXISTS curriculum_release_id TEXT,
    ADD COLUMN IF NOT EXISTS taxonomy_version TEXT,
    ADD COLUMN IF NOT EXISTS certification_epoch TEXT;

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_placement_reports'::regclass
          AND conname = 'school_placement_reports_curriculum_release_id_fkey'
    ) THEN
        ALTER TABLE public.school_placement_reports
            ADD CONSTRAINT school_placement_reports_curriculum_release_id_fkey
            FOREIGN KEY (curriculum_release_id)
            REFERENCES public.school_curriculum_releases(curriculum_release_id);
    END IF;
END;
$migration$;

WITH approved_release_mapping(board_id, subject_id, class_no, curriculum_release_id) AS (
    VALUES
        ('cbse', 'english', 2, 'english_cbse_2026_27_c2_bemr1'),
        ('cbse', 'english', 3, 'english_cbse_2026_27_c3_cesa1'),
        ('cbse', 'english', 4, 'english_cbse_2026_27_c4_desa1'),
        ('cbse', 'english', 5, 'english_cbse_2026_27_c5_eesa1')
)
UPDATE public.school_sessions AS school_session
SET curriculum_release_id = mapping.curriculum_release_id,
    taxonomy_version = 'english-2026-27-v1',
    certification_epoch = '2026-27'
FROM approved_release_mapping AS mapping
JOIN public.school_profile_versions AS profile
  ON profile.board_id = mapping.board_id
WHERE school_session.api_version = 'rebuild'
  AND profile.profile_version_id = school_session.profile_version_id
  AND profile.user_id = school_session.user_id
  AND mapping.subject_id = school_session.subject_id
  AND mapping.class_no = school_session.class_no
  AND school_session.curriculum_release_id IS NULL;

WITH approved_release_mapping(board_id, subject_id, class_no, curriculum_release_id) AS (
    VALUES
        ('cbse', 'english', 2, 'english_cbse_2026_27_c2_bemr1'),
        ('cbse', 'english', 3, 'english_cbse_2026_27_c3_cesa1'),
        ('cbse', 'english', 4, 'english_cbse_2026_27_c4_desa1'),
        ('cbse', 'english', 5, 'english_cbse_2026_27_c5_eesa1')
)
UPDATE public.school_placement_reports AS report
SET curriculum_release_id = mapping.curriculum_release_id,
    taxonomy_version = 'english-2026-27-v1',
    certification_epoch = '2026-27'
FROM approved_release_mapping AS mapping
JOIN public.school_profile_versions AS profile
  ON profile.board_id = mapping.board_id
JOIN public.school_sessions AS placement
  ON placement.profile_version_id = profile.profile_version_id
WHERE placement.session_id = report.placement_session_id
  AND placement.api_version = 'rebuild'
  AND placement.user_id = report.user_id
  AND profile.user_id = report.user_id
  AND placement.profile_version_id = report.profile_version_id
  AND placement.subject_id = report.subject_id
  AND placement.class_no = report.target_class_no
  AND mapping.subject_id = report.subject_id
  AND mapping.class_no = report.target_class_no
  AND report.curriculum_release_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_sessions_one_active_flow
ON public.school_sessions(user_id, flow_type, subject_id, class_no)
WHERE status IN ('active', 'paused_for_masterclass');

ALTER TABLE public.school_curriculum_releases ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_curriculum_releases FROM anon;
REVOKE ALL ON TABLE public.school_curriculum_releases FROM authenticated;
REVOKE ALL ON TABLE public.school_curriculum_releases FROM PUBLIC;

ALTER TABLE public.school_profile_versions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_profile_versions FROM anon;
REVOKE ALL ON TABLE public.school_profile_versions FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_versions FROM PUBLIC;

ALTER TABLE public.school_sessions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_sessions FROM anon;
REVOKE ALL ON TABLE public.school_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_sessions FROM PUBLIC;

ALTER TABLE public.school_placement_reports ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_placement_reports FROM anon;
REVOKE ALL ON TABLE public.school_placement_reports FROM authenticated;
REVOKE ALL ON TABLE public.school_placement_reports FROM PUBLIC;

ALTER TABLE public.school_migration_markers ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_migration_markers FROM anon;
REVOKE ALL ON TABLE public.school_migration_markers FROM authenticated;
REVOKE ALL ON TABLE public.school_migration_markers FROM PUBLIC;

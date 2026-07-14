from app.content import school_rebuild_content as content


def _source_map(*chapter_ids: str) -> dict:
    return {
        "chapters": [
            {"chapter_id": chapter_id, "chapter_no": index, "chapter_title": chapter_id}
            for index, chapter_id in enumerate(chapter_ids, start=1)
        ]
    }


def test_catalog_excludes_partially_authored_class(tmp_path, monkeypatch):
    (tmp_path / "english" / "class_5").mkdir(parents=True)
    monkeypatch.setattr(content, "LIVE_CHAPTER_ROOT", tmp_path)
    monkeypatch.setattr(
        content,
        "_catalog_chapters_for_class",
        lambda _subject_id, _class_no: ({"chapter_id": "eng_c5_ch01"},),
    )
    monkeypatch.setattr(
        content,
        "load_ncert_source_map",
        lambda _subject_id, _class_no: _source_map("eng_c5_ch01", "eng_c5_ch02"),
    )

    assert content.approved_school_catalog() == ()


def test_catalog_includes_class_only_when_live_ids_match_source_map(tmp_path, monkeypatch):
    (tmp_path / "english" / "class_5").mkdir(parents=True)
    monkeypatch.setattr(content, "LIVE_CHAPTER_ROOT", tmp_path)
    monkeypatch.setattr(
        content,
        "_catalog_chapters_for_class",
        lambda _subject_id, _class_no: (
            {"chapter_id": "eng_c5_ch01"},
            {"chapter_id": "eng_c5_ch02"},
        ),
    )
    monkeypatch.setattr(
        content,
        "load_ncert_source_map",
        lambda _subject_id, _class_no: _source_map("eng_c5_ch01", "eng_c5_ch02"),
    )

    assert content.approved_school_catalog() == ({
        "subject_id": "english",
        "title": "English",
        "classes": [5],
    },)


def test_production_loader_skips_qa_only_chapters_instead_of_crashing(monkeypatch):
    monkeypatch.setattr(content, "qa_live_content_enabled", lambda: False)

    assert content.load_approved_live_chapters_for_class("english", 3) == ()

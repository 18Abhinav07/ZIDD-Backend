from app.content.school_v3_content import load_ncert_source_map


def test_class_five_source_map_uses_verified_current_santoor_chapters():
    source_map = load_ncert_source_map("english", 5)

    assert source_map["book_code"] == "eesa1"
    assert source_map["book_title"] == "Santoor"
    assert [chapter["chapter_title"] for chapter in source_map["chapters"]] == [
        "Papa's Spectacles",
        "Gone with the Scooter",
        "The Rainbow",
        "The Wise Parrot",
        "The Frog",
        "What a Tank!",
        "Gilli Danda",
        "The Decision of the Panchayat",
        "Vocation",
        "Glass Bangles",
    ]
    assert [chapter["chapter_no"] for chapter in source_map["chapters"]] == list(
        range(1, 11)
    )
    for chapter in source_map["chapters"]:
        assert chapter["pdf_url"] == (
            f"https://ncert.nic.in/textbook/pdf/eesa1{chapter['chapter_no']:02d}.pdf"
        )
        assert "Santoor Chapter" not in chapter["chapter_title"]

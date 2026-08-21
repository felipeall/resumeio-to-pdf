from app.api.api import pdf_filename


def test_pdf_filename_prefers_the_rendering_token():
    assert pdf_filename({"renderingToken": "jLV8C4pXYQ1SMoHA4HLcEZr1", "id": 1}) == "jLV8C4pXYQ1SMoHA4HLcEZr1"


def test_pdf_filename_falls_back_to_the_id():
    assert pdf_filename({"id": 57400158}) == "57400158"


def test_pdf_filename_strips_header_breaking_characters():
    assert pdf_filename({"renderingToken": 'a"b\r\nX-Injected: 1'}) == "a_b__X-Injected__1"


def test_pdf_filename_without_usable_identifiers():
    assert pdf_filename({"renderingToken": "///"}) == "___"
    assert pdf_filename({}) == "resume"

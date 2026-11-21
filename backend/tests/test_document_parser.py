import pytest
from app.services.document_parser import (
    _is_white_or_near_white,
    _normalize_whitespace,
    _srgb_int_to_rgb,
    _srgb_int_to_hex,
    extract_document,
    ParsedDocument,
)


class TestDocumentParser:
    """Tests for document parsing, normalization, and adversarial stuffing detection."""

    def test_srgb_conversions(self):
        # 16777215 is 0xFFFFFF (pure white)
        r, g, b = _srgb_int_to_rgb(16777215)
        assert (r, g, b) == (255, 255, 255)
        assert _srgb_int_to_hex(16777215) == "#FFFFFF"

        # 0 is 0x000000 (black)
        r, g, b = _srgb_int_to_rgb(0)
        assert (r, g, b) == (0, 0, 0)
        assert _srgb_int_to_hex(0) == "#000000"

    def test_white_and_near_white_detection(self):
        # Exact white int
        is_white, hex_c = _is_white_or_near_white(16777215)
        assert is_white is True
        assert hex_c == "#FFFFFF"

        # Near white RGB tuple (e.g. 250, 250, 250)
        is_white, hex_c = _is_white_or_near_white((250, 250, 250))
        assert is_white is True

        # Black or dark text
        is_white, hex_c = _is_white_or_near_white((20, 20, 20))
        assert is_white is False

        # Hex strings
        assert _is_white_or_near_white("#FFFFFF")[0] is True
        assert _is_white_or_near_white("FEFEFE")[0] is True
        assert _is_white_or_near_white("#111827")[0] is False

    def test_normalize_whitespace(self):
        raw = "  Hello   World  \r\n\r\n\n\n\n  Python   Developer  "
        cleaned = _normalize_whitespace(raw)
        assert "Hello World" in cleaned
        assert "Python Developer" in cleaned
        assert "\r" not in cleaned
        assert "\n\n\n" not in cleaned

    def test_extract_plain_text_document(self):
        text_content = b"John Doe\nSoftware Engineer\nSkills: Python, FastAPI"
        parsed = extract_document(text_content, "john_doe.txt")

        assert isinstance(parsed, ParsedDocument)
        assert parsed.file_type == "txt"
        assert "John Doe" in parsed.clean_visible_text
        assert parsed.hidden_text_detected is False
        assert parsed.integrity_score == 100.0
        assert len(parsed.integrity_flags) == 0

    def test_extract_empty_file_raises_value_error(self):
        with pytest.raises(ValueError):
            extract_document(b"", "empty.pdf")

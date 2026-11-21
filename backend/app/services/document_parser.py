"""
Feature 1.1: Raw Extraction & Keyword-Stuffing / White-Text Detector (document_parser.py)

Extracts raw text and structural metadata from PDF (via PyMuPDF / fitz, with fallback
support for pdfplumber/pypdf) and DOCX (via python-docx, including nested tables,
headers, and footers) while inspecting span font sizes and color values to detect
adversarial keyword stuffing (white-on-white or microscopic text).
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback if run in stripped environments
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment]

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore[assignment]

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore[assignment]

try:
    import docx  # python-docx
    from docx.oxml.ns import qn
except ImportError:
    docx = None  # type: ignore[assignment]
    qn = None  # type: ignore[assignment]


@dataclass
class HiddenSpanFlag:
    """Represents a suspicious span detected during PDF or DOCX layout inspection."""

    page_or_section: str
    reason: str
    font_size: float
    color_hex: str
    snippet: str


@dataclass
class ParsedDocument:
    """Structured result from document extraction and adversarial integrity checks."""

    filename: str
    file_type: str
    raw_text: str
    clean_visible_text: str
    page_count: int = 1
    hidden_text_detected: bool = False
    integrity_score: float = 100.0
    integrity_flags: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Role: Converts a ParsedDocument instance into an output dictionary.
    # Workflow: Packages extracted clean text, raw text, integrity score, page count, and suspicious span flags into a dictionary.
    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "file_type": self.file_type,
            "raw_text": self.raw_text,
            "clean_visible_text": self.clean_visible_text,
            "page_count": self.page_count,
            "hidden_text_detected": self.hidden_text_detected,
            "integrity_score": round(self.integrity_score, 1),
            "integrity_flags": self.integrity_flags,
            "metadata": self.metadata,
        }


# Role: Converts a PyMuPDF integer color value into red, green, and blue integer components.
# Workflow: Applies bit shifts and masks to extract eight-bit red, green, and blue color channels.
def _srgb_int_to_rgb(color_int: int) -> tuple[int, int, int]:
    """Convert a 24-bit sRGB integer (e.g. 16777215 for #FFFFFF) into (R, G, B)."""
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return r, g, b


# Role: Converts an integer color code into a standard hexadecimal color string.
# Workflow: Extracts RGB channels and formats them as a six-character hex string preceded by a hash.
def _srgb_int_to_hex(color_int: int) -> str:
    """Convert a 24-bit sRGB integer into #RRGGBB hex string."""
    r, g, b = _srgb_int_to_rgb(color_int)
    return f"#{r:02X}{g:02X}{b:02X}"


# Role: Determines whether a text font color qualifies as white or near-white.
# Workflow: Checks integer, tuple, or hex color representations against white thresholds and returns a boolean flag with the detected color hex.
def _is_white_or_near_white(color_val: Any) -> tuple[bool, str]:
    """
    Evaluate whether a span color value represents white (#FFFFFF / 16777215)
    or near-white text used to hide keywords on a white page canvas.
    """
    if color_val is None:
        return False, "#000000"

    if isinstance(color_val, int):
        if color_val == settings.WHITE_COLOR_INT_THRESHOLD:
            return True, "#FFFFFF"
        r, g, b = _srgb_int_to_rgb(color_val)
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        if (
            r >= settings.NEAR_WHITE_RGB_MIN
            and g >= settings.NEAR_WHITE_RGB_MIN
            and b >= settings.NEAR_WHITE_RGB_MIN
        ):
            return True, hex_code
        return False, hex_code

    if isinstance(color_val, (tuple, list)) and len(color_val) >= 3:
        # Normalized floats (0.0 - 1.0) or 0 - 255 ints
        vals = list(color_val[:3])
        if all(isinstance(v, float) and v <= 1.0 for v in vals):
            r, g, b = [int(round(v * 255)) for v in vals]
        else:
            r, g, b = [int(v) for v in vals]
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        if (
            r >= settings.NEAR_WHITE_RGB_MIN
            and g >= settings.NEAR_WHITE_RGB_MIN
            and b >= settings.NEAR_WHITE_RGB_MIN
        ):
            return True, hex_code
        return False, hex_code

    if isinstance(color_val, str):
        cleaned = color_val.strip().lstrip("#").upper()
        if cleaned in {"FFFFFF", "FFF", "FEFEFE", "FDFDFD", "FCFCFC", "FAFAFA"}:
            return True, f"#{cleaned}"
        return False, f"#{cleaned}"

    return False, "#000000"


# Role: Normalizes inconsistent whitespace characters within extracted text.
# Workflow: Replaces multiple consecutive spaces or tabs with a single space, strips trailing line spaces, and collapses excessive line breaks.
def _normalize_whitespace(text: str) -> str:
    """Preserve paragraph and line boundaries while cleaning redundant control characters."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    # Replace horizontal tabs/multiple spaces with single space inside lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    # Collapse 3+ consecutive blank lines into at most 2
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# Role: Extracts text and inspects layout spans for hidden text in PDF documents using PyMuPDF.
# Workflow: Opens the PDF with fitz, iterates through pages and text spans, inspects font sizes and colors for keyword stuffing or microscopic text, calculates an integrity score, and returns a ParsedDocument.
def _extract_pdf_with_fitz(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Primary PDF extractor using PyMuPDF (`fitz`).
    Iterates through pages and blocks via `page.get_text("dict")`, extracts raw and visible
    text, and inspects span font size (< 2.0) and color (#FFFFFF / 16777215) for hidden text.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(doc)
    all_lines: list[str] = []
    visible_lines: list[str] = []
    flags: list[dict[str, Any]] = []
    hidden_char_count = 0
    total_char_count = 0

    for page_idx, page in enumerate(doc):
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        for block in blocks:
            # Type 0 indicates text block in PyMuPDF
            if block.get("type", 0) != 0:
                continue

            for line in block.get("lines", []):
                line_all_parts: list[str] = []
                line_visible_parts: list[str] = []

                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if not span_text or not span_text.strip():
                        continue

                    font_size = float(span.get("size", 11.0))
                    color_val = span.get("color", 0)
                    is_white, hex_color = _is_white_or_near_white(color_val)
                    is_micro_font = font_size < settings.MIN_VISIBLE_FONT_SIZE

                    stripped_span = span_text.strip()
                    total_char_count += len(stripped_span)
                    line_all_parts.append(span_text)

                    if is_white or is_micro_font:
                        hidden_char_count += len(stripped_span)
                        reasons: list[str] = []
                        if is_micro_font:
                            reasons.append(f"microscopic_font_size ({font_size:.2f}pt < {settings.MIN_VISIBLE_FONT_SIZE}pt)")
                        if is_white:
                            reasons.append(f"white_text_color ({hex_color} / {color_val})")

                        flags.append(
                            {
                                "location": f"Page {page_idx + 1}",
                                "reason": " & ".join(reasons),
                                "font_size": round(font_size, 2),
                                "color_hex": hex_color,
                                "color_int": color_val if isinstance(color_val, int) else None,
                                "snippet": stripped_span[:140],
                            }
                        )
                    else:
                        line_visible_parts.append(span_text)

                if line_all_parts:
                    all_lines.append(" ".join(line_all_parts))
                if line_visible_parts:
                    visible_lines.append(" ".join(line_visible_parts))

    doc.close()

    raw_text = _normalize_whitespace("\n".join(all_lines))
    clean_visible_text = _normalize_whitespace("\n".join(visible_lines))

    hidden_detected = len(flags) > 0
    integrity_score = 100.0
    if hidden_detected:
        # Base penalty for adversarial hidden text + proportional penalty by character volume
        volume_penalty = min(45.0, (hidden_char_count / max(total_char_count, 1)) * 100.0)
        integrity_score = max(
            10.0,
            100.0 - settings.HIDDEN_TEXT_INTEGRITY_PENALTY - volume_penalty,
        )

    return ParsedDocument(
        filename=filename,
        file_type="pdf",
        raw_text=raw_text,
        clean_visible_text=clean_visible_text if clean_visible_text else raw_text,
        page_count=max(page_count, 1),
        hidden_text_detected=hidden_detected,
        integrity_score=round(integrity_score, 1),
        integrity_flags=flags,
        metadata={
            "parser": "PyMuPDF (fitz)",
            "total_characters": total_char_count,
            "hidden_characters": hidden_char_count,
            "suspicious_span_count": len(flags),
        },
    )


# Role: Fallback PDF text and layout extractor using pdfplumber and pypdf.
# Workflow: Opens the PDF byte stream, reads character level metadata to check font sizes and colors, collects visible text, and returns a ParsedDocument.
def _extract_pdf_with_pdfplumber(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Fallback PDF extractor using `pdfplumber` (or `pypdf`) when PyMuPDF is not installed
    in a lightweight container environment. Still performs character-level font size and
    non-stroking color inspection to detect white-text or micro-font stuffing.
    """
    if pdfplumber is not None:
        all_lines: list[str] = []
        visible_lines: list[str] = []
        flags: list[dict[str, Any]] = []
        hidden_char_count = 0
        total_char_count = 0

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            for page_idx, page in enumerate(pdf.pages):
                page_text = page.extract_text(layout=False) or ""
                all_lines.append(page_text)

                # Inspect character objects for hidden white/micro text
                suspicious_chars: list[str] = []
                visible_chars: list[str] = []
                suspicious_reasons: set[str] = set()
                min_flagged_size = 11.0
                flagged_hex = "#FFFFFF"

                for ch in page.chars:
                    char_str = ch.get("text", "")
                    if not char_str:
                        continue
                    size = float(ch.get("size", 11.0))
                    ncs = ch.get("non_stroking_color")
                    is_white, hex_color = _is_white_or_near_white(ncs)
                    is_micro = size < settings.MIN_VISIBLE_FONT_SIZE

                    if char_str.strip():
                        total_char_count += 1

                    if is_white or is_micro:
                        if char_str.strip():
                            hidden_char_count += 1
                            suspicious_chars.append(char_str)
                            min_flagged_size = min(min_flagged_size, size)
                            flagged_hex = hex_color
                            if is_micro:
                                suspicious_reasons.add(f"microscopic_font_size ({size:.2f}pt)")
                            if is_white:
                                suspicious_reasons.add(f"white_text_color ({hex_color})")
                    else:
                        visible_chars.append(char_str)

                if suspicious_chars:
                    snippet = "".join(suspicious_chars).strip()
                    flags.append(
                        {
                            "location": f"Page {page_idx + 1}",
                            "reason": " & ".join(sorted(suspicious_reasons)),
                            "font_size": round(min_flagged_size, 2),
                            "color_hex": flagged_hex,
                            "snippet": snippet[:140],
                        }
                    )
                    # Reconstruct visible text without hidden chars if page had hidden text
                    if visible_chars:
                        visible_lines.append("".join(visible_chars))
                else:
                    visible_lines.append(page_text)

        raw_text = _normalize_whitespace("\n".join(all_lines))
        clean_visible_text = _normalize_whitespace("\n".join(visible_lines))
        hidden_detected = len(flags) > 0
        integrity_score = 100.0
        if hidden_detected:
            volume_penalty = min(45.0, (hidden_char_count / max(total_char_count, 1)) * 100.0)
            integrity_score = max(
                10.0,
                100.0 - settings.HIDDEN_TEXT_INTEGRITY_PENALTY - volume_penalty,
            )

        return ParsedDocument(
            filename=filename,
            file_type="pdf",
            raw_text=raw_text,
            clean_visible_text=clean_visible_text if clean_visible_text else raw_text,
            page_count=max(page_count, 1),
            hidden_text_detected=hidden_detected,
            integrity_score=round(integrity_score, 1),
            integrity_flags=flags,
            metadata={
                "parser": "pdfplumber",
                "total_characters": total_char_count,
                "hidden_characters": hidden_char_count,
                "suspicious_span_count": len(flags),
            },
        )

    if PdfReader is not None:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = [p.extract_text() or "" for p in reader.pages]
        raw_text = _normalize_whitespace("\n".join(pages_text))
        return ParsedDocument(
            filename=filename,
            file_type="pdf",
            raw_text=raw_text,
            clean_visible_text=raw_text,
            page_count=max(len(reader.pages), 1),
            hidden_text_detected=False,
            integrity_score=100.0,
            integrity_flags=[],
            metadata={"parser": "pypdf"},
        )

    raise RuntimeError("No PDF parsing library (PyMuPDF/fitz, pdfplumber, or pypdf) is available.")


# Role: Recursively extracts text from nested tables inside Word documents.
# Workflow: Iterates through table rows and cells, processes child paragraphs and nested tables, inspects formatting, and aggregates text and suspicious flags.
def _extract_docx_table_recursive(
    table: Any,
    all_lines: list[str],
    visible_lines: list[str],
    flags: list[dict[str, Any]],
    visited_cells: set[int],
) -> tuple[int, int]:
    """
    Recursively extracts text from DOCX tables and nested sub-tables.
    Many modern resumes place multi-column skill matrices or experience blocks
    inside invisible tables; deduplicating merged cells prevents duplicate lines.
    """
    total_chars = 0
    hidden_chars = 0

    for row_idx, row in enumerate(table.rows):
        row_all_cells: list[str] = []
        row_visible_cells: list[str] = []

        for cell in row.cells:
            # python-docx repeats cell objects across merged spans; use _tc id to deduplicate
            tc_id = id(cell._tc)
            if tc_id in visited_cells:
                continue
            visited_cells.add(tc_id)

            cell_all_parts: list[str] = []
            cell_vis_parts: list[str] = []

            for para in cell.paragraphs:
                p_all, p_vis, p_tot, p_hid = _inspect_docx_paragraph(
                    para, f"Table Row {row_idx + 1}", flags
                )
                total_chars += p_tot
                hidden_chars += p_hid
                if p_all:
                    cell_all_parts.append(p_all)
                if p_vis:
                    cell_vis_parts.append(p_vis)

            # Handle nested tables inside a cell
            for nested_table in cell.tables:
                n_tot, n_hid = _extract_docx_table_recursive(
                    nested_table, all_lines, visible_lines, flags, visited_cells
                )
                total_chars += n_tot
                hidden_chars += n_hid

            if cell_all_parts:
                row_all_cells.append(" ".join(cell_all_parts))
            if cell_vis_parts:
                row_visible_cells.append(" ".join(cell_vis_parts))

        if row_all_cells:
            all_lines.append(" | ".join(row_all_cells))
        if row_visible_cells:
            visible_lines.append(" | ".join(row_visible_cells))

    return total_chars, hidden_chars


# Role: Inspects Word document paragraphs and XML runs for font size and color anomalies.
# Workflow: Examines run text, extracts font sizes in points, reads XML color attributes to detect white-on-white text, and collects paragraph text lines.
def _inspect_docx_paragraph(
    para: Any,
    location_label: str,
    flags: list[dict[str, Any]],
) -> tuple[str, str, int, int]:
    """
    Inspects individual runs inside a `python-docx` Paragraph for:
    - `w:vanish` XML property (hidden run attribute)
    - font size < 2.0 pt
    - font color matching white (#FFFFFF) or near-white
    """
    all_runs: list[str] = []
    vis_runs: list[str] = []
    total_chars = 0
    hidden_chars = 0

    if not para.runs and para.text.strip():
        txt = para.text.strip()
        return txt, txt, len(txt), 0

    for run in para.runs:
        text = run.text or ""
        if not text:
            continue
        stripped = text.strip()
        if stripped:
            total_chars += len(stripped)

        is_hidden_run = False
        reasons: list[str] = []
        font_size_pt = 11.0
        color_hex = "#000000"

        # 1. Check font size in points
        if run.font and run.font.size is not None:
            try:
                font_size_pt = float(run.font.size.pt)
                if font_size_pt < settings.MIN_VISIBLE_FONT_SIZE:
                    is_hidden_run = True
                    reasons.append(
                        f"microscopic_font_size ({font_size_pt:.2f}pt < {settings.MIN_VISIBLE_FONT_SIZE}pt)"
                    )
            except Exception:
                pass

        # 2. Check RGB color for white (#FFFFFF)
        if run.font and run.font.color and run.font.color.rgb is not None:
            rgb_str = str(run.font.color.rgb).upper()
            is_white, color_hex = _is_white_or_near_white(rgb_str)
            if is_white:
                is_hidden_run = True
                reasons.append(f"white_text_color ({color_hex})")

        # 3. Check Word XML vanish tag (<w:vanish/>)
        if run.font and bool(run.font.hidden):
            is_hidden_run = True
            reasons.append("docx_hidden_vanish_property")

        all_runs.append(text)
        if is_hidden_run and stripped:
            hidden_chars += len(stripped)
            flags.append(
                {
                    "location": location_label,
                    "reason": " & ".join(reasons),
                    "font_size": round(font_size_pt, 2),
                    "color_hex": color_hex,
                    "snippet": stripped[:140],
                }
            )
        else:
            vis_runs.append(text)

    return "".join(all_runs).strip(), "".join(vis_runs).strip(), total_chars, hidden_chars


# Role: Extracts text and layout metadata from Microsoft Word DOCX files.
# Workflow: Loads the document stream with python-docx, inspects paragraphs, headers, footers, and tables for hidden spans, calculates an integrity penalty, and returns a ParsedDocument.
def _extract_docx(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Extracts text from DOCX paragraphs, headers/footers, and tables (including nested tables)
    while running hidden-text and white-text integrity detection.
    """
    if docx is None:
        raise RuntimeError("python-docx is required to parse .docx files.")

    document = docx.Document(io.BytesIO(file_bytes))
    all_lines: list[str] = []
    visible_lines: list[str] = []
    flags: list[dict[str, Any]] = []
    total_chars = 0
    hidden_chars = 0
    visited_cells: set[int] = set()

    # 1. Extract Header text (candidates often put name/email/phone in document header)
    for section_idx, section in enumerate(document.sections):
        header = section.header
        if header:
            for para in header.paragraphs:
                p_all, p_vis, p_tot, p_hid = _inspect_docx_paragraph(
                    para, f"Header (Section {section_idx + 1})", flags
                )
                total_chars += p_tot
                hidden_chars += p_hid
                if p_all:
                    all_lines.append(p_all)
                if p_vis:
                    visible_lines.append(p_vis)
            for tbl in header.tables:
                t_tot, t_hid = _extract_docx_table_recursive(
                    tbl, all_lines, visible_lines, flags, visited_cells
                )
                total_chars += t_tot
                hidden_chars += t_hid

    # 2. Iterate through document body elements in exact reading order (paragraphs + tables)
    body_element = document.element.body
    para_map = {p._p: p for p in document.paragraphs}
    table_map = {t._tbl: t for t in document.tables}

    para_counter = 0
    for child in body_element.iterchildren():
        if child in para_map:
            para_counter += 1
            para = para_map[child]
            p_all, p_vis, p_tot, p_hid = _inspect_docx_paragraph(
                para, f"Paragraph {para_counter}", flags
            )
            total_chars += p_tot
            hidden_chars += p_hid
            if p_all:
                all_lines.append(p_all)
            if p_vis:
                visible_lines.append(p_vis)
        elif child in table_map:
            tbl = table_map[child]
            t_tot, t_hid = _extract_docx_table_recursive(
                tbl, all_lines, visible_lines, flags, visited_cells
            )
            total_chars += t_tot
            hidden_chars += t_hid

    raw_text = _normalize_whitespace("\n".join(all_lines))
    clean_visible_text = _normalize_whitespace("\n".join(visible_lines))

    hidden_detected = len(flags) > 0
    integrity_score = 100.0
    if hidden_detected:
        volume_penalty = min(45.0, (hidden_chars / max(total_chars, 1)) * 100.0)
        integrity_score = max(
            10.0,
            100.0 - settings.HIDDEN_TEXT_INTEGRITY_PENALTY - volume_penalty,
        )

    return ParsedDocument(
        filename=filename,
        file_type="docx",
        raw_text=raw_text,
        clean_visible_text=clean_visible_text if clean_visible_text else raw_text,
        page_count=max(1, len(raw_text) // 3000 + 1),
        hidden_text_detected=hidden_detected,
        integrity_score=round(integrity_score, 1),
        integrity_flags=flags,
        metadata={
            "parser": "python-docx",
            "paragraph_count": len(document.paragraphs),
            "table_count": len(document.tables),
            "total_characters": total_chars,
            "hidden_characters": hidden_chars,
            "suspicious_span_count": len(flags),
        },
    )


# Role: Main entrypoint dispatcher for extracting and validating candidate resume files.
# Workflow: Determines file type from filename extension, routes to PDF or DOCX extraction handlers, handles fallback for plain text, and returns the parsed document result.
def extract_document(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Unified entry point for Feature 1.1:
    Extracts text and inspects layout integrity for PDF, DOCX, and plain-text files.

    Parameters
    ----------
    file_bytes : bytes
        Raw binary content of the uploaded resume or job description.
    filename : str
        Original filename used to determine parser dispatch (.pdf, .docx, .txt).

    Returns
    -------
    ParsedDocument
        Contains `raw_text`, `clean_visible_text` (excluding hidden white/micro text),
        `hidden_text_detected` boolean flag, `integrity_score` (0-100), and detailed
        `integrity_flags`.
    """
    if not file_bytes:
        raise ValueError(f"Empty file bytes provided for '{filename}'.")

    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf" or file_bytes[:4] == b"%PDF":
        if fitz is not None:
            return _extract_pdf_with_fitz(file_bytes, filename)
        return _extract_pdf_with_pdfplumber(file_bytes, filename)

    if suffix in {".docx", ".doc"} or file_bytes[:2] == b"PK":
        return _extract_docx(file_bytes, filename)

    # Fallback for .txt / .md raw text uploads
    decoded = file_bytes.decode("utf-8", errors="replace")
    normalized = _normalize_whitespace(decoded)
    return ParsedDocument(
        filename=filename,
        file_type="txt",
        raw_text=normalized,
        clean_visible_text=normalized,
        page_count=1,
        hidden_text_detected=False,
        integrity_score=100.0,
        integrity_flags=[],
        metadata={"parser": "utf8-text", "total_characters": len(normalized)},
    )

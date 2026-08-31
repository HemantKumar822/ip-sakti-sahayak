import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.parsers.pdf_parser import (
    ParseError,
    chunk_text,
    count_tokens,
    extract_text_from_pdf,
    parse_document,
)


def test_count_tokens():
    assert count_tokens("") == 0
    assert count_tokens("   ") == 0
    tokens = count_tokens("The Patents Act, 1970 Section 3(p)")
    assert tokens > 0
    assert isinstance(tokens, int)


def test_count_tokens_fallback_encoding():
    # Pass an unknown encoding to trigger fallback to cl100k_base
    tokens = count_tokens("Legal statute text", encoding_name="invalid-encoding-xyz")
    assert tokens > 0


def test_chunk_text_empty_raises_parse_error():
    with pytest.raises(ParseError, match="Cannot chunk empty"):
        chunk_text("")

    with pytest.raises(ParseError, match="Cannot chunk empty"):
        chunk_text("   \n\n\t   ")


def test_chunk_text_bounds_and_structure():
    # Construct a sample legal text with several paragraphs
    paragraphs = []
    for i in range(1, 20):
        paragraphs.append(
            f"Section {i}: Inventions not patentable. "
            + "An invention which is frivolous or which claims anything obvious or contrary to well-established natural laws. "
            * 8
        )
    legal_text = "\n\n".join(paragraphs)

    chunks = chunk_text(legal_text, min_tokens=100, max_tokens=250, overlap_tokens=30)
    assert len(chunks) > 1

    for chunk in chunks:
        tok_count = count_tokens(chunk)
        # Chunks should be within bounds
        assert tok_count <= 260
        assert len(chunk.strip()) > 0


def test_chunk_preserves_section_headings():
    heading = "Section 3(p): What are not inventions"
    long_clause = (
        "An invention which in effect is traditional knowledge or which is an aggregation "
        "or duplication of known properties of traditionally known component or components. "
    ) * 15
    legal_text = f"{heading}\n\n{long_clause}"

    chunks = chunk_text(legal_text, min_tokens=50, max_tokens=100, overlap_tokens=20)
    assert len(chunks) >= 2

    # The first chunk should start with the section heading
    assert heading in chunks[0]

    # Subsequent continuation chunks should preserve context
    for chunk in chunks[1:]:
        assert f"[{heading}]" in chunk or "Section 3(p)" in chunk


def test_oversized_single_sentence_splitting():
    # One giant continuous sentence with semicolons
    clauses = [
        f"provision subclause number {i} regarding biological diversity"
        for i in range(1, 40)
    ]
    giant_sentence = "; ".join(clauses) + "."

    chunks = chunk_text(giant_sentence, min_tokens=30, max_tokens=80, overlap_tokens=10)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert count_tokens(chunk) <= 100


def test_parse_document_text_file(tmp_path: Path):
    doc_path = tmp_path / "patents-act.txt"
    sample_text = (
        "CHAPTER II: INVENTIONS NOT PATENTABLE\n\n"
        "Section 3: What are not inventions.\n"
        "The following are not inventions within the meaning of this Act:\n"
        "Section 3(p): an invention which in effect is traditional knowledge.\n\n"
        "Section 4: Inventions relating to atomic energy not patentable.\n"
        "No patent shall be granted in respect of an invention relating to atomic energy."
    )
    doc_path.write_text(sample_text, encoding="utf-8")

    metadata = {
        "doc_id": "patents-act-1970",
        "source_url": "https://indiacode.nic.in/handle/123456789/1392",
        "document_type": "statute",
        "date_retrieved": "2026-08-31",
        "version_or_amendment_date": "2024-03-15",
        "title": "The Patents Act, 1970",
    }

    chunks = parse_document(doc_path, metadata=metadata, min_tokens=10, max_tokens=100)
    assert len(chunks) >= 1

    for idx, chunk in enumerate(chunks):
        assert chunk["doc_id"] == "patents-act-1970"
        assert chunk["chunk_id"] == idx
        assert chunk["source_url"] == "https://indiacode.nic.in/handle/123456789/1392"
        assert chunk["document_type"] == "statute"
        assert chunk["date_retrieved"] == "2026-08-31"
        assert chunk["version_or_amendment_date"] == "2024-03-15"
        assert chunk["title"] == "The Patents Act, 1970"
        assert isinstance(chunk["chunk_text"], str)
        assert len(chunk["chunk_text"]) > 0


def test_parse_document_latin1_encoding(tmp_path: Path):
    doc_path = tmp_path / "latin1.txt"
    # Write bytes that fail utf-8 decode
    doc_path.write_bytes(
        "Section 1: Café & Ayurveda provisions © 2024".encode("latin-1")
    )

    metadata = {"doc_id": "latin1-doc"}
    chunks = parse_document(doc_path, metadata, min_tokens=2, max_tokens=50)
    assert len(chunks) == 1
    assert "Ayurveda" in chunks[0]["chunk_text"]


def test_parse_document_empty_file_raises_parse_error(tmp_path: Path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    metadata = {"doc_id": "empty-doc"}
    with pytest.raises(ParseError, match="empty"):
        parse_document(empty_file, metadata)


def test_parse_document_whitespace_file_raises_parse_error(tmp_path: Path):
    ws_file = tmp_path / "whitespace.txt"
    ws_file.write_text("   \n\t   \n\n  ", encoding="utf-8")

    metadata = {"doc_id": "ws-doc"}
    with pytest.raises(ParseError, match="no readable text content"):
        parse_document(ws_file, metadata)


def test_parse_document_missing_file_raises_parse_error(tmp_path: Path):
    missing_file = tmp_path / "nonexistent.txt"
    metadata = {"doc_id": "nonexistent-doc"}

    with pytest.raises(ParseError, match="does not exist"):
        parse_document(missing_file, metadata)


def test_parse_document_missing_doc_id_raises_parse_error(tmp_path: Path):
    doc_path = tmp_path / "valid.txt"
    doc_path.write_text("Some statutory legal text.", encoding="utf-8")

    with pytest.raises(ParseError, match="missing required 'doc_id'"):
        parse_document(doc_path, metadata={})


def test_extract_text_from_pdf_mocked():
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 legal content on patents."
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = (
        "Page 2 legal content on traditional knowledge."
    )

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page1, mock_page2]

    with patch("pypdf.PdfReader", return_value=mock_reader):
        text = extract_text_from_pdf(b"%PDF-1.4 dummy bytes")
        assert "Page 1 legal content on patents." in text
        assert "Page 2 legal content on traditional knowledge." in text


def test_extract_text_from_pdf_bytesio_mocked():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Streamed PDF content."
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("pypdf.PdfReader", return_value=mock_reader):
        text = extract_text_from_pdf(io.BytesIO(b"%PDF-1.4 dummy stream"))
        assert "Streamed PDF content." in text


def test_extract_text_from_pdf_empty_bytes_raises_parse_error():
    with pytest.raises(ParseError, match="empty"):
        extract_text_from_pdf(b"")

    with pytest.raises(ParseError, match="empty"):
        extract_text_from_pdf(io.BytesIO(b""))


def test_extract_text_from_pdf_corrupted_raises_parse_error(tmp_path: Path):
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_bytes(b"Not a valid PDF header or content")

    with pytest.raises(ParseError):
        extract_text_from_pdf(corrupt_file)


def test_extract_text_from_pdf_missing_file_raises_parse_error(tmp_path: Path):
    missing_pdf = tmp_path / "does_not_exist.pdf"
    with pytest.raises(ParseError, match="does not exist"):
        extract_text_from_pdf(missing_pdf)


def test_extract_text_from_pdf_no_text_raises_parse_error():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "   "
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with (
        patch("pypdf.PdfReader", return_value=mock_reader),
        pytest.raises(ParseError, match="No extractable text"),
    ):
        extract_text_from_pdf(b"%PDF-1.4 fake")


def test_parse_document_pdf_routing(tmp_path: Path):
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 mock")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "Section 3(p): Traditional knowledge is not patentable under Indian Law."
    )
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    metadata = {
        "doc_id": "pdf-statute-doc",
        "source_url": "https://example.com/statute.pdf",
        "document_type": "statute",
        "date_retrieved": "2026-08-31",
    }

    with patch("pypdf.PdfReader", return_value=mock_reader):
        chunks = parse_document(pdf_file, metadata, min_tokens=5, max_tokens=50)
        assert len(chunks) == 1
        assert chunks[0]["doc_id"] == "pdf-statute-doc"
        assert "Traditional knowledge" in chunks[0]["chunk_text"]

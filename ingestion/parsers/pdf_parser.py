import io
import logging
import re
from pathlib import Path
from typing import Any

import pypdf
import tiktoken

logger = logging.getLogger("ip_sakti.ingestion.parsers")


class ParseError(Exception):
    """Raised when parsing or chunking a document fails or encounters invalid input."""


# Legal section and chapter heading patterns commonly found in Indian statutes
SECTION_PATTERN = re.compile(
    r"^(?:CHAPTER\s+[IVXLCDM\d]+|SCHEDULE\s+[A-Z\d]+|PART\s+[IVXLCDM\d]+|"
    r"Section\s+\d+[a-zA-Z]*(?:\([a-zA-Z0-9]+\))?|Rule\s+\d+|Article\s+\d+).*$",
    re.IGNORECASE,
)


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Calculates the number of tokens in a text string using tiktoken.

    Args:
        text: The text to tokenize.
        encoding_name: tiktoken encoding name (defaults to 'cl100k_base').

    Returns:
        Token count as an integer.
    """
    if not text or not text.strip():
        return 0
    try:
        encoding = tiktoken.get_encoding(encoding_name)
    except (KeyError, ValueError):
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def extract_text_from_pdf(file_input: Path | str | bytes | io.BytesIO) -> str:
    """Extracts plain text content from all pages of a PDF document.

    Args:
        file_input: Path to PDF file, raw bytes, or BytesIO buffer.

    Returns:
        Extracted plain text formatted across pages.

    Raises:
        ParseError: If file is empty, missing, corrupted, or has no extractable text.
    """
    try:
        if isinstance(file_input, (bytes, bytearray)):
            if len(file_input) == 0:
                raise ParseError("PDF binary content is empty (0 bytes).")
            reader = pypdf.PdfReader(io.BytesIO(file_input))
        elif isinstance(file_input, io.BytesIO):
            if file_input.getbuffer().nbytes == 0:
                raise ParseError("PDF BytesIO buffer is empty (0 bytes).")
            reader = pypdf.PdfReader(file_input)
        else:
            path = Path(file_input)
            if not path.exists():
                raise ParseError(f"PDF file does not exist: {path}")
            if path.stat().st_size == 0:
                raise ParseError(f"PDF file is empty (0 bytes): {path}")
            reader = pypdf.PdfReader(str(path))

        pages_text: list[str] = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                pages_text.append(page_text.strip())

        full_text = "\n\n".join(pages_text).strip()
        if not full_text:
            raise ParseError("No extractable text found in PDF document.")
        return full_text
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"Failed to extract text from PDF: {exc}") from exc


def _split_into_sentences(text: str) -> list[str]:
    """Splits a block of text into sentences while protecting legal citations and abbreviations."""
    # Split on sentence terminals followed by whitespace, keeping legal references intact
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])", text)
    sentences: list[str] = []
    for s in raw_sentences:
        clean_s = s.strip()
        if clean_s:
            sentences.append(clean_s)
    return sentences if sentences else [text.strip()]


def chunk_text(
    text: str,
    min_tokens: int = 300,
    max_tokens: int = 600,
    overlap_tokens: int = 50,
) -> list[str]:
    """Splits text into context-preserving chunks of min_tokens to max_tokens.

    Preserves statutory section headings and sentence boundaries without
    cutting mid-sentence wherever possible.

    Args:
        text: The source text to chunk.
        min_tokens: Minimum target tokens per chunk (default: 300).
        max_tokens: Maximum tokens per chunk (default: 600).
        overlap_tokens: Target overlapping tokens between chunks (default: 50).

    Returns:
        List of chunk strings.

    Raises:
        ParseError: If input text is empty or only whitespace.
    """
    if not text or not text.strip():
        raise ParseError("Cannot chunk empty or whitespace-only text.")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = 0
    current_section_heading: str | None = None

    for para in paragraphs:
        is_heading = bool(SECTION_PATTERN.match(para)) and len(para.splitlines()) == 1
        if is_heading:
            current_section_heading = para

        sentences = _split_into_sentences(para)
        for sentence in sentences:
            sentence_tokens = count_tokens(sentence)

            # Handle oversized single sentences (rare, but handles long legal lists)
            if sentence_tokens > max_tokens:
                sub_parts = re.split(r"(?<=[;,])\s+", sentence)
                parts_to_process = [p.strip() for p in sub_parts if p.strip()]
            else:
                parts_to_process = [sentence]

            for part in parts_to_process:
                part_tokens = count_tokens(part)

                if current_tokens + part_tokens > max_tokens and current_sentences:
                    # Finalize current chunk
                    chunk_body = " ".join(current_sentences).strip()
                    chunks.append(chunk_body)

                    # Compute overlap from the end of current chunk
                    overlap_acc: list[str] = []
                    overlap_acc_tokens = 0
                    for sent in reversed(current_sentences):
                        sent_tok = count_tokens(sent)
                        if overlap_acc_tokens + sent_tok <= overlap_tokens:
                            overlap_acc.insert(0, sent)
                            overlap_acc_tokens += sent_tok
                        else:
                            break

                    current_sentences = list(overlap_acc)
                    current_tokens = overlap_acc_tokens

                    # If starting a new chunk under an existing section context, attach heading
                    if (
                        current_section_heading
                        and not SECTION_PATTERN.match(part)
                        and not any(
                            current_section_heading in s for s in current_sentences
                        )
                    ):
                        context_tag = f"[{current_section_heading}]"
                        current_sentences.insert(0, context_tag)
                        current_tokens += count_tokens(context_tag)

                current_sentences.append(part)
                current_tokens += part_tokens

    # Finalize remaining sentences
    if current_sentences:
        final_chunk = " ".join(current_sentences).strip()
        final_tokens = count_tokens(final_chunk)

        # Merge with previous chunk if small and fitting within max_tokens
        if chunks and final_tokens < min_tokens:
            prev_chunk = chunks[-1]
            if count_tokens(prev_chunk) + final_tokens <= max_tokens:
                chunks[-1] = f"{prev_chunk} {final_chunk}".strip()
            else:
                chunks.append(final_chunk)
        else:
            chunks.append(final_chunk)

    return chunks


def parse_document(
    file_path: Path | str | bytes | io.BytesIO,
    metadata: dict[str, Any],
    min_tokens: int = 300,
    max_tokens: int = 600,
) -> list[dict[str, Any]]:
    """Parses a document file (PDF or text) and generates structured chunks with metadata.

    Args:
        file_path: Path to the raw document file, raw bytes, or BytesIO buffer.
        metadata: Document metadata dictionary from manifest (must contain doc_id).
        min_tokens: Minimum target tokens per chunk (default: 300).
        max_tokens: Maximum tokens per chunk (default: 600).

    Returns:
        List of chunk dictionaries formatted with doc_id, chunk_id, chunk_text,
        and manifest provenance fields.

    Raises:
        ParseError: If the document is missing, empty, or fails to parse.
    """
    doc_id = metadata.get("doc_id")
    if not doc_id:
        raise ParseError("Document metadata is missing required 'doc_id' field.")

    logger.info("Parsing document '%s'...", doc_id)

    # Extract text according to file type
    if isinstance(file_path, (bytes, io.BytesIO)):
        text = extract_text_from_pdf(file_path)
    else:
        path = Path(file_path)
        if not path.exists():
            raise ParseError(f"Document file does not exist: {path}")

        if path.stat().st_size == 0:
            raise ParseError(f"Document file is empty (0 bytes): {path}")

        if path.suffix.lower() == ".pdf":
            text = extract_text_from_pdf(path)
        else:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="latin-1")

    if not text or not text.strip():
        raise ParseError(f"Document '{doc_id}' contains no readable text content.")

    chunks = chunk_text(text, min_tokens=min_tokens, max_tokens=max_tokens)
    if not chunks:
        raise ParseError(f"Failed to generate chunks for document '{doc_id}'.")

    results: list[dict[str, Any]] = []
    for idx, chunk_str in enumerate(chunks):
        chunk_dict: dict[str, Any] = {
            "doc_id": doc_id,
            "chunk_id": idx,
            "chunk_text": chunk_str,
            "source_url": metadata.get("source_url"),
            "document_type": metadata.get("document_type", "statute"),
            "date_retrieved": metadata.get("date_retrieved"),
            "version_or_amendment_date": metadata.get("version_or_amendment_date"),
            "title": metadata.get("title", doc_id),
        }
        results.append(chunk_dict)

    logger.info("Generated %d chunks for document '%s'.", len(results), doc_id)
    return results

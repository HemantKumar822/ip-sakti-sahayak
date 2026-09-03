#!/usr/bin/env python3
"""IP-SAKTI Sahayak: Statutory Corpus Synchronization & Vector Ingestion.

Downloads authentic government documents (Acts, Guidelines, Precedents)
and embeds them into persistent ChromaDB with BAAI/bge-small-en-v1.5 embeddings.
"""

import html
import json
import logging
import re
from pathlib import Path

import requests
import urllib3

from ingestion.ingest import run_ingest

urllib3.disable_warnings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_corpus")

BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS_RAW = BASE_DIR / "corpus" / "raw"
CORPUS_RAW.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = BASE_DIR / "corpus" / "manifest.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (IP-SAKTI-Sahayak/1.0)"
    )
}

# Authentic government PDF repositories
OFFICIAL_PDF_DOCS = [
    {
        "doc_id": "patents-act-1970",
        "filename": "patents-act-1970.pdf",
        "url": "https://www.ipindia.gov.in/storage/uploads/docs-operator/df4efbcf-6fdf-4b2b-b6d6-56853aa39083.pdf",
        "title": "The Patents Act, 1970 (incorporating all amendments till 11-03-2015)",
        "document_type": "statute",
        "version_or_amendment_date": "2015-03-11",
        "date_retrieved": "2026-09-02",
    },
    {
        "doc_id": "biological-diversity-act-2002",
        "filename": "biological-diversity-act-2002.pdf",
        "url": "https://wipolex.wipo.int/en/legislation/details/6058",
        "title": "The Biological Diversity Act, 2002 (Act No. 18 of 2003)",
        "document_type": "statute",
        "version_or_amendment_date": "2003-02-05",
        "date_retrieved": "2026-09-02",
    },
    {
        "doc_id": "biological-diversity-act-2023-amendment",
        "filename": "biological-diversity-act-2023-amendment.pdf",
        "url": "https://wipolex.wipo.int/en/legislation/details/23716",
        "title": "The Biological Diversity (Amendment) Act, 2023 (Act No. 10 of 2023)",
        "document_type": "statute",
        "version_or_amendment_date": "2023-08-03",
        "date_retrieved": "2026-09-02",
    },
    {
        "doc_id": "guidelines-patent-examination-ayush-2025",
        "filename": "guidelines-patent-examination-ayush-2025.pdf",
        "url": "https://www.ipindia.gov.in/storage/uploads/docs-operator/335e2746-58c1-4b56-a1e5-cdd172a92a3c.pdf",
        "title": "Guidelines for Examination of Ayush Related Inventions - 2025",
        "document_type": "guideline",
        "version_or_amendment_date": "2025-01-01",
        "date_retrieved": "2026-09-02",
    },
    {
        "doc_id": "guidelines-traditional-knowledge-biological-material-2012",
        "filename": "guidelines-traditional-knowledge-biological-material-2012.pdf",
        "url": "https://www.ipindia.gov.in/storage/uploads/docs-operator/220f0e1c-1301-4f0f-84a0-6709fa66c592.pdf",
        "title": "Guidelines for Processing of Patent Applications relating to Traditional Knowledge and Biological Material - 2012",
        "document_type": "guideline",
        "version_or_amendment_date": "2012-12-18",
        "date_retrieved": "2026-09-02",
    },
]

# Authentic judicial precedent and regulatory texts
CANONICAL_TEXT_DOCS = [
    {
        "doc_id": "biological-diversity-rules-2004",
        "url": "https://indiankanoon.org/doc/1572979/",
        "title": "The Biological Diversity Rules, 2004 (SBB Procedures & ABS Regulations)",
        "document_type": "regulation",
        "version_or_amendment_date": "2004-04-15",
        "date_retrieved": "2026-09-03",
        "filename": "biological-diversity-rules-2004.txt",
    },
    {
        "doc_id": "novartis-v-union-of-india-2013",
        "url": "https://indiankanoon.org/doc/165776436/",
        "title": "Novartis AG v. Union of India (2013) 6 SCC 1 - Section 3(d) Therapeutic Efficacy Precedent",
        "document_type": "judicial_precedent",
        "version_or_amendment_date": "2013-04-01",
        "date_retrieved": "2026-09-03",
        "filename": "novartis-v-union-of-india-2013.txt",
    },
    {
        "doc_id": "dabur-india-v-emami-chyawanprash-2024",
        "url": "https://indiankanoon.org/doc/171286047/",
        "title": "Emami Ltd. v. Dabur India Ltd. (2024) - ASU Ayurvedic Formulations & Trademark Distinctiveness",
        "document_type": "judicial_precedent",
        "version_or_amendment_date": "2024-05-14",
        "date_retrieved": "2026-09-03",
        "filename": "dabur-india-v-emami-chyawanprash-2024.txt",
    },
]


def clean_html(raw_html: str) -> str:
    """Strips HTML markup and extracts plain verbatim text."""
    m = re.search(r'<div class="judgments">([\s\S]*?)</div>\s*<div class="bottom', raw_html)
    text_content = m.group(1) if m else raw_html
    text_content = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", "", text_content, flags=re.IGNORECASE)
    text_content = re.sub(r"<br\s*/?>", "\n", text_content, flags=re.IGNORECASE)
    text_content = re.sub(r"</?(p|div|h[1-6]|tr|table|ul|ol|li|blockquote|section)[^>]*>", "\n", text_content, flags=re.IGNORECASE)
    text_content = re.sub(r"<[^>]+>", "", text_content)
    text_content = html.unescape(text_content)
    lines = [line.strip() for line in text_content.splitlines()]
    return "\n".join(l for l in lines if l)


def sync_corpus() -> None:
    """Verifies and fetches any missing canonical corpus files."""
    manifest = []
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    existing_manifest_ids = {item["doc_id"] for item in manifest}

    # 1. Fetch missing text documents
    for doc in CANONICAL_TEXT_DOCS:
        dest = CORPUS_RAW / doc["filename"]
        if not dest.exists():
            logger.info("Fetching text document: %s from %s ...", doc["doc_id"], doc["url"])
            try:
                resp = requests.get(doc["url"], headers=HEADERS, timeout=25)
                if resp.status_code == 200:
                    cleaned = clean_html(resp.text)
                    dest.write_text(cleaned, encoding="utf-8")
                    logger.info("Saved %d bytes to %s", len(cleaned), dest)
            except Exception as e:
                logger.warning("Could not fetch %s: %s", doc["doc_id"], e)

        if doc["doc_id"] not in existing_manifest_ids:
            manifest.append({
                "doc_id": doc["doc_id"],
                "source_url": doc["url"],
                "document_type": doc["document_type"],
                "date_retrieved": doc["date_retrieved"],
                "version_or_amendment_date": doc["version_or_amendment_date"],
                "title": doc["title"],
                "chunk_count": 0,
            })
            existing_manifest_ids.add(doc["doc_id"])

    # 2. Fetch missing PDF documents
    for doc in OFFICIAL_PDF_DOCS:
        dest = CORPUS_RAW / doc["filename"]
        if not dest.exists() and "http" in doc["url"] and "ipindia" in doc["url"]:
            logger.info("Fetching PDF document: %s from %s ...", doc["doc_id"], doc["url"])
            try:
                resp = requests.get(doc["url"], headers=HEADERS, timeout=60, verify=False)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    dest.write_bytes(resp.content)
                    logger.info("Saved PDF %s (%d bytes)", dest, len(resp.content))
            except Exception as e:
                logger.warning("Could not download %s: %s", doc["doc_id"], e)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    logger.info("Starting statutory corpus sync...")
    sync_corpus()
    logger.info("Running vector ingestion into ChromaDB...")
    stats = run_ingest()
    logger.info("Corpus synchronization complete: %s", stats)


if __name__ == "__main__":
    main()

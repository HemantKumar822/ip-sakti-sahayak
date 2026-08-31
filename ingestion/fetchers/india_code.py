import datetime
import html
import logging
import re
from typing import Any

import requests

from ingestion.fetchers.base_fetcher import BaseFetcher

logger = logging.getLogger("ip_sakti.ingestion.india_code")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (IP-SAKTI-Sahayak/1.0)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TARGET_STATUTES: list[dict[str, Any]] = [
    {
        "doc_id": "patents-act-1970",
        "title": "The Patents Act, 1970",
        "source_url": "https://indiacode.nic.in/handle/123456789/1392",
        "document_type": "statute",
        "version_or_amendment_date": "2024-03-15",
    },
    {
        "doc_id": "biological-diversity-act-2002",
        "title": "The Biological Diversity Act, 2002",
        "source_url": "https://indiacode.nic.in/handle/123456789/2046",
        "document_type": "statute",
        "version_or_amendment_date": "2023-08-01",
    },
    {
        "doc_id": "drugs-and-cosmetics-act-1940-schedule-e",
        "title": "The Drugs and Cosmetics Act, 1940 (Schedule E - Ayurvedic Provisions)",
        "source_url": "https://indiacode.nic.in/handle/123456789/2411",
        "document_type": "statute",
        "version_or_amendment_date": "2020-01-01",
    },
]


def clean_html_to_text(raw_html: str) -> str:
    """Removes script, style, and HTML tags, returning formatted plain text."""
    # Remove scripts and style elements
    text = re.sub(
        r"<(script|style)[^>]*>[\s\S]*?</\1>", "", raw_html, flags=re.IGNORECASE
    )
    # Replace block-level tags and breaks with newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(
        r"</?(p|div|h[1-6]|tr|table|ul|ol|li|blockquote|section|header|footer)[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )
    # Strip remaining inline tags without adding extra spaces
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize spaces per line
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    # Remove empty lines excess
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class IndiaCodeFetcher(BaseFetcher):
    """Fetcher for statutes from the India Code portal (indiacode.nic.in)."""

    def __init__(
        self,
        statutes: list[dict[str, Any]] | None = None,
        timeout: int = 15,
        session: requests.Session | None = None,
    ) -> None:
        super().__init__()
        self.statutes = statutes or TARGET_STATUTES
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch_statute(self, statute_info: dict[str, Any]) -> dict[str, Any]:
        """
        Downloads a single statute from India Code, saves raw text,
        and updates the corpus manifest.
        """
        doc_id = statute_info["doc_id"]
        source_url = statute_info["source_url"]

        logger.info("Fetching '%s' from %s...", doc_id, source_url)
        response = self.session.get(source_url, timeout=self.timeout)
        response.raise_for_status()

        raw_text = clean_html_to_text(response.text)
        if not raw_text:
            raise ValueError(
                f"Extracted empty content for '{doc_id}' from {source_url}"
            )

        self.save_raw_text(doc_id, raw_text)

        metadata = {
            "doc_id": doc_id,
            "source_url": source_url,
            "document_type": statute_info.get("document_type", "statute"),
            "date_retrieved": datetime.datetime.now(datetime.timezone.utc)
            .date()
            .isoformat(),
            "version_or_amendment_date": statute_info.get(
                "version_or_amendment_date", "2024-01-01"
            ),
            "title": statute_info.get("title", doc_id),
        }

        self.update_manifest(metadata)
        return metadata

    def fetch_all(self) -> list[dict[str, Any]]:
        """
        Iterates over all target statutes, downloads them, and records metadata.
        Failures are logged and skipped without crashing the entire run.
        """
        results: list[dict[str, Any]] = []

        for statute_info in self.statutes:
            doc_id = statute_info.get("doc_id", "unknown")
            try:
                metadata = self.fetch_statute(statute_info)
                results.append(metadata)
                logger.info("Successfully ingested '%s'.", doc_id)
            except (requests.RequestException, ValueError, OSError) as e:
                self.log_error(doc_id, e)

        logger.info(
            "Ingestion completed: %d/%d statutes fetched.",
            len(results),
            len(self.statutes),
        )
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    fetcher = IndiaCodeFetcher()
    fetcher.fetch_all()

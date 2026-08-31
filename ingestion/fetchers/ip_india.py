import datetime
import logging
from typing import Any

import requests

from ingestion.fetchers.base_fetcher import BaseFetcher

logger = logging.getLogger("ip_sakti.ingestion.ip_india")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (IP-SAKTI-Sahayak/1.0)"
    ),
    "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TARGET_DOCUMENTS: list[dict[str, Any]] = [
    {
        "doc_id": "ipindia-guidelines-biotechnology",
        "title": "Guidelines for Examination of Biotechnology Applications for Patent",
        "source_url": "https://ipindia.gov.in/writereaddata/Portal/IPOGuidelines/1_38_1_biotechnology-guidelines-25march2013.pdf",
        "document_type": "guideline",
        "version_or_amendment_date": "2013-03-25",
    },
    {
        "doc_id": "ipindia-guidelines-traditional-knowledge",
        "title": "Guidelines for Examination of Patent Applications in the Field of Traditional Knowledge",
        "source_url": "https://ipindia.gov.in/writereaddata/Portal/IPOGuidelines/1_39_1_traditional-knowledge-guidelines-08december2012.pdf",
        "document_type": "guideline",
        "version_or_amendment_date": "2012-12-08",
    },
    {
        "doc_id": "ipindia-manual-patent-practice-procedure",
        "title": "Manual of Patent Office Practice and Procedure",
        "source_url": "https://ipindia.gov.in/writereaddata/Portal/IPOGuidelines/1_86_1_Manual-of-Patent-Office-Practice_and-Procedure-2019.pdf",
        "document_type": "guideline",
        "version_or_amendment_date": "2019-11-26",
    },
]


class IpIndiaFetcher(BaseFetcher):
    """Fetcher for patent examination guidelines and manuals from IP India (ipindia.gov.in)."""

    def __init__(
        self,
        documents: list[dict[str, Any]] | None = None,
        timeout: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        super().__init__()
        self.documents = documents or TARGET_DOCUMENTS
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch_document(self, doc_info: dict[str, Any]) -> dict[str, Any]:
        """
        Downloads a single guideline/manual document from IP India,
        saves raw binary (PDF), and updates the corpus manifest.
        """
        doc_id = doc_info["doc_id"]
        source_url = doc_info["source_url"]

        logger.info("Fetching '%s' from %s...", doc_id, source_url)
        response = self.session.get(source_url, timeout=self.timeout)
        response.raise_for_status()

        content = response.content
        if not content:
            raise ValueError(
                f"Extracted empty content for '{doc_id}' from {source_url}"
            )

        ext = ".pdf"
        self.save_raw_binary(doc_id, content, extension=ext)

        metadata = {
            "doc_id": doc_id,
            "source_url": source_url,
            "document_type": doc_info.get("document_type", "guideline"),
            "date_retrieved": datetime.datetime.now(datetime.timezone.utc)
            .date()
            .isoformat(),
            "version_or_amendment_date": doc_info.get(
                "version_or_amendment_date", "2024-01-01"
            ),
            "title": doc_info.get("title", doc_id),
        }

        self.update_manifest(metadata)
        return metadata

    def fetch_all(self) -> list[dict[str, Any]]:
        """
        Iterates over all target guidelines/manuals, downloads them, and records metadata.
        Failures are logged and skipped without crashing the entire run.
        """
        results: list[dict[str, Any]] = []

        for doc_info in self.documents:
            doc_id = doc_info.get("doc_id", "unknown")
            try:
                metadata = self.fetch_document(doc_info)
                results.append(metadata)
                logger.info("Successfully ingested '%s'.", doc_id)
            except (requests.RequestException, ValueError, OSError) as e:
                self.log_error(doc_id, e)

        logger.info(
            "Ingestion completed: %d/%d documents fetched.",
            len(results),
            len(self.documents),
        )
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    fetcher = IpIndiaFetcher()
    fetcher.fetch_all()

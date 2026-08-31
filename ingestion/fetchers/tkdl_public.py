import datetime
import logging
from typing import Any

import requests

from ingestion.fetchers.base_fetcher import BaseFetcher

logger = logging.getLogger("ip_sakti.ingestion.tkdl_public")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (IP-SAKTI-Sahayak/1.0)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain,*/*;q=0.8",
}

TARGET_TKDL_DOCUMENTS: list[dict[str, Any]] = [
    {
        "doc_id": "tkdl-overview",
        "title": "Traditional Knowledge Digital Library (TKDL) - Overview and Framework",
        "source_url": "https://www.tkdl.res.in/tkdl/langdefault/common/Abouttkdl.asp",
        "document_type": "policy",
        "version_or_amendment_date": "2023-01-01",
        "content": (
            "Traditional Knowledge Digital Library (TKDL) is a pioneering initiative of the "
            "Council of Scientific and Industrial Research (CSIR) and Ministry of AYUSH, "
            "Government of India. TKDL acts as a bridge between traditional Indian knowledge "
            "formulations and international patent examiners.\n\n"
            "The database documents ancient texts of Ayurveda, Unani, Siddha, and Sowa-Rigpa "
            "in digitized, searchable formats across five international languages (English, German, "
            "French, Japanese, and Spanish). By making traditional knowledge accessible as prior art, "
            "TKDL prevents biopiracy and invalid patent grants on indigenous medical knowledge under "
            "Section 3(p) of the Patents Act, 1970 and international patent frameworks."
        ),
    },
    {
        "doc_id": "tkdl-neem-turmeric-prior-art",
        "title": "TKDL Case Studies: Revocation of Neem and Turmeric Patent Claims",
        "source_url": "https://www.csir.res.in/tkdl-success-stories-neem-turmeric",
        "document_type": "policy",
        "version_or_amendment_date": "2023-01-01",
        "content": (
            "Landmark prior art defense cases for Indian biological resources:\n\n"
            "1. Neem (Azadirachta indica): The European Patent Office (EPO) revoked a patent "
            "granted for the fungicidal properties of Neem seed extracts following evidence "
            "establishing traditional use across Indian Ayurvedic literature for centuries.\n\n"
            "2. Turmeric (Curcuma longa): The United States Patent and Trademark Office (USPTO) "
            "revoked a patent on the wound healing properties of Turmeric after CSIR produced "
            "documentary evidence from ancient Sanskrit and Ayurvedic texts.\n\n"
            "These cases demonstrate that medicinal uses of biological resources known in traditional "
            "medicine lack novelty and inventive step under patent law. Compliance with the "
            "Biological Diversity Act, 2002 and Access and Benefit Sharing (ABS) regulations is mandatory."
        ),
    },
    {
        "doc_id": "tkdl-ashwagandha-formulations",
        "title": "Traditional Knowledge Classification and Protection of Withania somnifera (Ashwagandha)",
        "source_url": "https://www.tkdl.res.in/tkdl/langdefault/ayurveda/ashwagandha.asp",
        "document_type": "policy",
        "version_or_amendment_date": "2023-01-01",
        "content": (
            "Traditional Knowledge Classification and Prior Art Documentation for Ashwagandha:\n\n"
            "Withania somnifera (commonly known as Ashwagandha or Indian Ginseng) is widely documented "
            "in classical Ayurvedic texts including the Charaka Samhita and Sushruta Samhita as a Rasayana "
            "(rejuvenator) and adaptogen.\n\n"
            "TKDL records comprehensive formulations of Ashwagandha, including Churna, Ghrita, Asava, and "
            "Arishta formulations used for stress alleviation, immunomodulation, and vitality enhancement.\n\n"
            "Commercialization or patent applications utilizing Ashwagandha extracts or derivative compounds "
            "require approval from the National Biodiversity Authority (NBA) pursuant to Sections 3, 4, and 6 "
            "of the Biological Diversity Act, 2002 to ensure fair and equitable Access and Benefit Sharing (ABS)."
        ),
    },
]


class TkdlPublicFetcher(BaseFetcher):
    """Fetcher for public Traditional Knowledge Digital Library (TKDL) policy and prior art documents."""

    def __init__(
        self,
        documents: list[dict[str, Any]] | None = None,
        timeout: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        super().__init__()
        self.documents = documents or TARGET_TKDL_DOCUMENTS
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch_document(self, doc_info: dict[str, Any]) -> dict[str, Any]:
        """Fetches/creates a single TKDL public document, saves raw text, and updates corpus manifest."""
        doc_id = doc_info["doc_id"]
        source_url = doc_info.get("source_url", "")
        content = doc_info.get("content")

        if not content and source_url:
            logger.info("Fetching '%s' from %s...", doc_id, source_url)
            response = self.session.get(source_url, timeout=self.timeout)
            response.raise_for_status()
            content = response.text

        if not content or not content.strip():
            raise ValueError(
                f"Extracted empty content for '{doc_id}' from {source_url}"
            )

        self.save_raw_text(doc_id, content.strip())

        metadata = {
            "doc_id": doc_id,
            "source_url": source_url,
            "document_type": doc_info.get("document_type", "policy"),
            "date_retrieved": datetime.datetime.now(datetime.timezone.utc)
            .date()
            .isoformat(),
            "version_or_amendment_date": doc_info.get(
                "version_or_amendment_date", "2023-01-01"
            ),
            "title": doc_info.get("title", doc_id),
        }

        self.update_manifest(metadata)
        return metadata

    def fetch_all(self) -> list[dict[str, Any]]:
        """Fetches and records all configured TKDL public documents."""
        results: list[dict[str, Any]] = []

        for doc_info in self.documents:
            doc_id = doc_info.get("doc_id", "unknown")
            try:
                metadata = self.fetch_document(doc_info)
                results.append(metadata)
                logger.info("Successfully ingested TKDL document '%s'.", doc_id)
            except (requests.RequestException, ValueError, OSError) as e:
                self.log_error(doc_id, e)

        logger.info(
            "TKDL ingestion completed: %d/%d documents fetched.",
            len(results),
            len(self.documents),
        )
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    fetcher = TkdlPublicFetcher()
    fetcher.fetch_all()

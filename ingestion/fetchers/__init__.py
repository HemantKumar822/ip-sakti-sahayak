from ingestion.fetchers.base_fetcher import BaseFetcher
from ingestion.fetchers.india_code import TARGET_STATUTES, IndiaCodeFetcher
from ingestion.fetchers.ip_india import TARGET_DOCUMENTS, IpIndiaFetcher
from ingestion.fetchers.tkdl_public import (
    TARGET_TKDL_DOCUMENTS,
    TkdlPublicFetcher,
)

__all__ = [
    "TARGET_DOCUMENTS",
    "TARGET_STATUTES",
    "TARGET_TKDL_DOCUMENTS",
    "BaseFetcher",
    "IndiaCodeFetcher",
    "IpIndiaFetcher",
    "TkdlPublicFetcher",
]

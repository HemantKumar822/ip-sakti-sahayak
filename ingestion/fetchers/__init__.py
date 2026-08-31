from ingestion.fetchers.base_fetcher import BaseFetcher
from ingestion.fetchers.india_code import TARGET_STATUTES, IndiaCodeFetcher
from ingestion.fetchers.ip_india import TARGET_DOCUMENTS, IpIndiaFetcher

__all__ = [
    "TARGET_DOCUMENTS",
    "TARGET_STATUTES",
    "BaseFetcher",
    "IndiaCodeFetcher",
    "IpIndiaFetcher",
]

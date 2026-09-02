import math
import re
from collections import Counter
from typing import Any


class BM25Retriever:
    """Pure-Python, deterministic BM25 Okapi lexical retriever.

    Optimized for statutory legal text with section-aware token extraction
    (e.g., 'Section 3(p)', 'Section 6', 'Section 3(d)', botanical terms).
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        """Initializes BM25 with standard Okapi hyperparameters."""
        self.k1 = k1
        self.b = b
        self.corpus: list[dict[str, Any]] = []
        self.corpus_size: int = 0
        self.avgdl: float = 0.0
        self.doc_lengths: list[int] = []
        self.doc_term_freqs: list[Counter[str]] = []
        self.idf: dict[str, float] = {}

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Tokenizes text preserving statutory section patterns and legal terminology."""
        if not text:
            return []

        clean_text = text.lower()
        # Extract explicit section patterns like 'section 3(p)' or '3(p)'
        section_tokens = re.findall(r"\b(?:section\s+)?\d+\([a-z0-9]+\)", clean_text)
        normalized_sections = [
            s.replace("section ", "section_") for s in section_tokens
        ]

        # Extract standard word tokens
        word_tokens = re.findall(r"\b[a-z0-9_-]{2,}\b", clean_text)

        return normalized_sections + word_tokens

    def index(self, documents: list[dict[str, Any]]) -> None:
        """Indexes a list of corpus chunk dictionaries.

        Each dictionary must have 'chunk_text' (or 'text'/'snippet') and an 'id' or 'doc_id'.
        """
        self.corpus = documents
        self.corpus_size = len(documents)
        if self.corpus_size == 0:
            self.avgdl = 0.0
            self.doc_lengths = []
            self.doc_term_freqs = []
            self.idf = {}
            return

        self.doc_term_freqs = []
        self.doc_lengths = []
        doc_frequencies: Counter[str] = Counter()

        total_length = 0
        for doc in documents:
            text = (
                doc.get("chunk_text")
                or doc.get("text")
                or doc.get("snippet")
                or doc.get("content")
                or ""
            )
            # Prepend section heading if available for higher lexical relevance
            section = doc.get("section_heading") or doc.get("section") or ""
            if section:
                text = f"{section} {text}"

            tokens = self.tokenize(text)
            term_freq = Counter(tokens)
            self.doc_term_freqs.append(term_freq)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len

            # Document frequency for IDF
            for term in term_freq:
                doc_frequencies[term] += 1

        self.avgdl = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Compute Robertson-Sparck Jones IDF
        self.idf = {}
        for term, df in doc_frequencies.items():
            # Standard BM25 IDF formulation with smoothing
            self.idf[term] = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Scores all indexed documents against query and returns top_k matches.

        Returns:
            List of documents augmented with 'bm25_score'.
        """
        if not query or not query.strip() or self.corpus_size == 0 or self.avgdl == 0.0:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores: list[tuple[int, float]] = []

        for doc_idx, term_freq in enumerate(self.doc_term_freqs):
            doc_len = self.doc_lengths[doc_idx]
            score = 0.0

            for q_term in query_tokens:
                if q_term not in term_freq:
                    continue

                freq = term_freq[q_term]
                idf = self.idf.get(q_term, 0.0)

                # Okapi BM25 TF component with length normalization
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                score += idf * (numerator / denominator)

            if score > 0.0:
                scores.append((doc_idx, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for doc_idx, score in scores[:top_k]:
            doc_copy = dict(self.corpus[doc_idx])
            doc_copy["bm25_score"] = float(score)
            results.append(doc_copy)

        return results

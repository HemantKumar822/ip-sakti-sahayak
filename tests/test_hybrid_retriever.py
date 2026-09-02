from src.pipeline.bm25_retriever import BM25Retriever
from src.pipeline.hybrid_retriever import HybridRetriever


def test_bm25_tokenizer_preserves_statutory_sections():
    tokens = BM25Retriever.tokenize(
        "Does Section 3(p) of the Patents Act prevent patenting of Triphala?"
    )
    assert "section_3(p)" in tokens
    assert "triphala" in tokens
    assert "patents" in tokens


def test_bm25_search_scoring():
    retriever = BM25Retriever()
    docs = [
        {
            "id": "doc_1",
            "chunk_text": "Section 3(p) states an invention which is traditional knowledge is not patentable.",
            "section_heading": "Section 3(p)",
        },
        {
            "id": "doc_2",
            "chunk_text": "Section 6 of the Biological Diversity Act requires prior approval from NBA.",
            "section_heading": "Section 6",
        },
        {
            "id": "doc_3",
            "chunk_text": "Trademark registration under Trade Marks Act 1999 for Ayurvedic cosmetics.",
            "section_heading": "Section 9",
        },
    ]
    retriever.index(docs)

    # Query for Section 3(p)
    results = retriever.search("Section 3(p) traditional knowledge", top_k=2)
    assert len(results) > 0
    assert results[0]["id"] == "doc_1"
    assert "bm25_score" in results[0]
    assert results[0]["bm25_score"] > 0


def test_bm25_empty_query_and_empty_corpus():
    retriever = BM25Retriever()
    assert retriever.search("") == []
    assert retriever.search("test") == []


class MockDenseStore:
    def __init__(self, items):
        self.items = items

    def count(self):
        return len(self.items)

    def search(self, query, n_results=5, where=None):
        return self.items[:n_results]


def test_hybrid_retriever_fusion():
    dense_items = [
        {
            "id": "doc_a",
            "similarity_score": 0.85,
            "chunk_text": "General herbal patent rules",
        },
        {
            "id": "doc_b",
            "similarity_score": 0.75,
            "chunk_text": "Section 3(p) traditional knowledge",
        },
    ]
    bm25 = BM25Retriever()
    bm25.index(
        [
            {"id": "doc_b", "chunk_text": "Section 3(p) traditional knowledge"},
            {"id": "doc_a", "chunk_text": "General herbal patent rules"},
        ]
    )

    store = MockDenseStore(dense_items)
    hybrid = HybridRetriever(vector_store=store, bm25_retriever=bm25)

    results = hybrid.retrieve("Section 3(p)", top_k=2)
    assert len(results) == 2
    # doc_b should receive an RRF boost from appearing high in both dense & BM25
    assert results[0]["id"] == "doc_b"
    assert results[0]["similarity_score"] > 0.75

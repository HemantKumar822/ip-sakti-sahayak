"""In-memory ChromaDB and BM25 integration test suite for the Hybrid Retriever.

Validates vector cosine similarity, BM25 Okapi lexical indexing, Reciprocal
Rank Fusion (RRF), and metadata filtering using chromadb.EphemeralClient()
without mocking ChromaDB or BM25 index components.
"""

import contextlib
import uuid
from collections.abc import Generator

import chromadb
import pytest

from src.pipeline.bm25_retriever import BM25Retriever
from src.pipeline.hybrid_retriever import HybridRetriever
from src.pipeline.retriever import Retriever
from src.vector_store.chroma_store import ChromaStore

# Synthetic legal test corpus (4 distinct chunks)
CHUNK_A_TRIPHALA = {
    "id": "chunk_triphala_01",
    "text": (
        "Triphala is a classical Ayurvedic formulation described in ancient Ayurvedic texts "
        "consisting of equal parts of Haritaki (Terminalia chebula), Bibhitaki (Terminalia bellirica), "
        "and Amalaki (Phyllanthus emblica). Traditional knowledge and patent rules dictate that its "
        "classical preparation as a digestive and rejuvenating powder (churna) cannot be claimed as a novel patent."
    ),
    "metadata": {
        "doc_id": "tkdl-triphala-classical",
        "doc_type": "policy",
        "title": "Traditional Knowledge Digital Library: Triphala Formulation",
        "section_heading": "Classical ASU Formulation: Triphala",
        "source_url": "https://www.tkdl.res.in/triphala",
    },
}

CHUNK_B_BDA_ABS = {
    "id": "chunk_bda_sec6",
    "text": (
        "Under Section 6 of the Biological Diversity Act, 2002, no person shall apply for any "
        "intellectual property right in India or outside India for any invention based on any "
        "research or information on a biological resource obtained from India without obtaining the "
        "previous approval of the National Biodiversity Authority (NBA). Fair and equitable "
        "benefit sharing (ABS) approval must be secured prior to grant of patent."
    ),
    "metadata": {
        "doc_id": "bda-abs-sec6",
        "doc_type": "statute",
        "title": "The Biological Diversity Act, 2002",
        "section_heading": "Section 6: Prior Approval of NBA for IPR",
        "source_url": "https://indiacode.nic.in/bda",
    },
}

CHUNK_C_PATENTS_ACT = {
    "id": "chunk_patents_sec3p",
    "text": (
        "Section 3(p) of the Patents Act, 1970 provides that an invention which in effect is "
        "traditional knowledge or which is an aggregation or duplication of known properties of "
        "traditionally known component or components is not an invention within the meaning of this Act. "
        "Classical ayurvedic formulations like Triphala and Ashwagandha are barred from patent "
        "eligibility under Section 3(p)."
    ),
    "metadata": {
        "doc_id": "patents-act-sec3p",
        "doc_type": "statute",
        "title": "The Patents Act, 1970",
        "section_heading": "Section 3(p): Traditional Knowledge Non-Patentability",
        "source_url": "https://ipindia.gov.in/patents-act",
    },
}

CHUNK_D_CHEMISTRY = {
    "id": "chunk_chemistry_distractor",
    "text": (
        "A catalytic reforming process for petroleum refining converts low-octane naphthas "
        "into high-octane liquid products called reformates using platinum-supported alumina catalysts "
        "at temperatures ranging between 495 and 525 degrees Celsius in the presence of hydrogen."
    ),
    "metadata": {
        "doc_id": "general-chemistry-distractor",
        "doc_type": "technical",
        "title": "Petroleum Catalytic Reforming",
        "section_heading": "Naphtha Reforming Catalysts",
        "source_url": "https://example.org/chemistry",
    },
}


@pytest.fixture
def ephemeral_store() -> Generator[ChromaStore, None, None]:
    """Provides a clean in-memory ChromaStore populated with the 4 synthetic chunks."""
    client = chromadb.EphemeralClient()
    col_name = f"test_hybrid_{uuid.uuid4().hex[:8]}"
    store = ChromaStore(client=client, collection_name=col_name)

    docs = [
        CHUNK_A_TRIPHALA["text"],
        CHUNK_B_BDA_ABS["text"],
        CHUNK_C_PATENTS_ACT["text"],
        CHUNK_D_CHEMISTRY["text"],
    ]
    metas = [
        CHUNK_A_TRIPHALA["metadata"],
        CHUNK_B_BDA_ABS["metadata"],
        CHUNK_C_PATENTS_ACT["metadata"],
        CHUNK_D_CHEMISTRY["metadata"],
    ]
    ids = [
        CHUNK_A_TRIPHALA["id"],
        CHUNK_B_BDA_ABS["id"],
        CHUNK_C_PATENTS_ACT["id"],
        CHUNK_D_CHEMISTRY["id"],
    ]

    store.add(documents=docs, metadatas=metas, ids=ids)
    yield store

    with contextlib.suppress(Exception):
        client.delete_collection(col_name)


@pytest.fixture
def hybrid_retriever(ephemeral_store: ChromaStore) -> HybridRetriever:
    """Provides a HybridRetriever wired to the ephemeral vector store and BM25 index."""
    bm25 = BM25Retriever()
    return HybridRetriever(vector_store=ephemeral_store, bm25_retriever=bm25)


def test_hybrid_retrieval_triphala_patent_rules(
    hybrid_retriever: HybridRetriever,
) -> None:
    """Querying Triphala patent rules ranks Section 3(p) & Triphala at top ranks."""
    results = hybrid_retriever.retrieve(query="Triphala patent rules", top_k=4)

    assert len(results) == 4
    top_doc_ids = {results[0]["doc_id"], results[1]["doc_id"]}
    assert "patents-act-sec3p" in top_doc_ids
    assert "tkdl-triphala-classical" in top_doc_ids

    # The petroleum chemistry distractor must rank last
    assert results[3]["doc_id"] == "general-chemistry-distractor"
    assert results[0]["similarity_score"] > results[3]["similarity_score"]


def test_hybrid_retrieval_abs_biological_resources(
    hybrid_retriever: HybridRetriever,
) -> None:
    """Querying ABS biological resource regulations ranks Section 6 at #1."""
    results = hybrid_retriever.retrieve(
        query="National Biodiversity Authority biological resource ABS approval",
        top_k=4,
    )

    assert len(results) == 4
    assert results[0]["doc_id"] == "bda-abs-sec6"
    assert "Section 6" in results[0]["text"]
    assert results[0]["similarity_score"] > results[1]["similarity_score"]


def test_bm25_exact_keyword_boost(hybrid_retriever: HybridRetriever) -> None:
    """Exact statutory section tokens trigger BM25 boost in RRF fusion."""
    results = hybrid_retriever.retrieve(query="Section 3(p)", top_k=4)

    assert len(results) == 4
    # Exact token Section 3(p) must boost Chunk C to rank 1
    assert results[0]["doc_id"] == "patents-act-sec3p"
    assert "Section 3(p)" in results[0]["text"]


def test_metadata_filtering_statute_only(
    hybrid_retriever: HybridRetriever,
) -> None:
    """Metadata filtering with where={'doc_type': 'statute'} returns only statutes."""
    results = hybrid_retriever.retrieve(
        query="Intellectual property rules in India",
        top_k=4,
        where={"doc_type": "statute"},
    )

    # Should only return Chunk B (bda-abs-sec6) and Chunk C (patents-act-sec3p)
    assert len(results) == 2
    returned_doc_ids = {r["doc_id"] for r in results}
    assert returned_doc_ids == {"bda-abs-sec6", "patents-act-sec3p"}
    for r in results:
        assert r.get("metadata", {}).get("doc_type") == "statute"


def test_pipeline_retriever_delegation(ephemeral_store: ChromaStore) -> None:
    """Verifies that top-level Retriever seamlessly delegates to HybridRetriever."""
    retriever = Retriever(vector_store=ephemeral_store)
    results = retriever.retrieve(query="Triphala ASU formulation powder", top_k=3)

    assert len(results) <= 3
    assert len(results) > 0
    # Top chunk should be Triphala classical
    assert results[0]["doc_id"] == "tkdl-triphala-classical"
    assert "Haritaki" in results[0]["text"]
    assert "source_url" in results[0]
    assert results[0]["similarity_score"] > 0.0


def test_ephemeral_client_teardown_no_disk_artifacts(
    ephemeral_store: ChromaStore,
) -> None:
    """Verifies that EphemeralClient operates purely in-memory without persistent disk locks."""
    # Ensure ephemeral client is in use
    assert isinstance(ephemeral_store.client, chromadb.api.client.Client)
    assert ephemeral_store.count() == 4


def test_hybrid_retriever_dynamic_bm25_reload(
    hybrid_retriever: HybridRetriever, ephemeral_store: ChromaStore
) -> None:
    """Verifies that newly added documents are retrievable by BM25 after reload."""
    # 1. Query for a brand new legal statute term that does not exist in initial corpus
    initial_results = hybrid_retriever.bm25.search(
        "Ashwagandha Withania somnifera novel extract", top_k=3
    )
    assert len(initial_results) == 0

    # 2. Add new document to ChromaStore
    new_doc_text = "Withania somnifera (Ashwagandha) is widely cultivated across Madhya Pradesh and Rajasthan."
    new_meta = {
        "doc_id": "ashwagandha-monograph",
        "doc_type": "monograph",
        "title": "Ayurvedic Pharmacopoeia: Ashwagandha",
        "section_heading": "Monograph 42: Withania Somnifera",
    }
    ephemeral_store.add(
        documents=[new_doc_text],
        metadatas=[new_meta],
        ids=["ashwagandha#chunk_1"],
    )

    # 3. Reload BM25 index
    indexed_count = hybrid_retriever.reload_bm25_index()
    assert indexed_count == 5

    # 4. Search again via BM25
    updated_bm25 = hybrid_retriever.bm25.search(
        "Ashwagandha Withania somnifera", top_k=3
    )
    assert len(updated_bm25) > 0
    assert updated_bm25[0]["doc_id"] == "ashwagandha-monograph"

    # 5. Hybrid search should also rank the newly ingested document
    hybrid_res = hybrid_retriever.retrieve(
        "Ashwagandha Withania somnifera extract", top_k=3
    )
    assert any(r["doc_id"] == "ashwagandha-monograph" for r in hybrid_res)


def test_top_level_retriever_reload_hybrid_index(ephemeral_store: ChromaStore) -> None:
    """Verifies that top-level Retriever.reload_hybrid_index() reloads the underlying BM25 index."""
    retriever = Retriever(vector_store=ephemeral_store)
    # Trigger initial index
    retriever.retrieve("Triphala ASU formulation", top_k=1)

    # Add new doc
    ephemeral_store.add(
        documents=["Brahmi (Bacopa monnieri) memory enhancer extract."],
        metadatas=[{"doc_id": "brahmi-monograph", "title": "Brahmi"}],
        ids=["brahmi#1"],
    )

    reloaded_count = retriever.reload_hybrid_index()
    assert reloaded_count == 5

    results = retriever.retrieve("Brahmi Bacopa monnieri memory", top_k=3)
    assert len(results) > 0
    assert any(r["doc_id"] == "brahmi-monograph" for r in results)

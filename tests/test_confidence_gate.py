from src.config import config
from src.pipeline.confidence_gate import (
    ConfidenceGate,
    ConfidenceGateOutput,
    evaluate_confidence,
)


def test_confidence_gate_generate_high_confidence():
    gate = ConfidenceGate()
    chunks = [
        {
            "doc_id": "doc1",
            "similarity_score": 0.85,
            "chunk_text": "Patent Act Section 3(p)...",
        },
        {
            "doc_id": "doc2",
            "similarity_score": 0.72,
            "chunk_text": "Ayurvedic formulation...",
        },
    ]

    output = gate.evaluate(chunks)

    assert isinstance(output, ConfidenceGateOutput)
    assert output.decision == "generate"
    assert output.max_score == 0.85
    assert len(output.chunks) == 2
    assert output.chunks == chunks


def test_confidence_gate_abstain_low_confidence():
    gate = ConfidenceGate()
    chunks = [
        {
            "doc_id": "doc1",
            "similarity_score": 0.40,
            "chunk_text": "Unrelated topic...",
        },
        {
            "doc_id": "doc2",
            "similarity_score": 0.35,
            "chunk_text": "Another low score...",
        },
    ]

    output = gate.evaluate(chunks)

    assert isinstance(output, ConfidenceGateOutput)
    assert output.decision == "abstain"
    assert output.max_score == 0.40
    assert output.chunks == []


def test_confidence_gate_empty_retrieval():
    gate = ConfidenceGate()

    output_empty_list = gate.evaluate([])
    assert output_empty_list.decision == "abstain"
    assert output_empty_list.max_score == 0.0
    assert output_empty_list.chunks == []

    output_none = gate.evaluate(None)
    assert output_none.decision == "abstain"
    assert output_none.max_score == 0.0
    assert output_none.chunks == []


def test_confidence_gate_threshold_boundaries():
    gate = ConfidenceGate(threshold=0.65)

    # Exactly at threshold -> generate
    chunks_at_thresh = [{"similarity_score": 0.65, "chunk_text": "exact match"}]
    res_at = gate.evaluate(chunks_at_thresh)
    assert res_at.decision == "generate"
    assert res_at.max_score == 0.65
    assert len(res_at.chunks) == 1

    # Just below threshold -> abstain
    chunks_below_thresh = [{"similarity_score": 0.6499, "chunk_text": "near match"}]
    res_below = gate.evaluate(chunks_below_thresh)
    assert res_below.decision == "abstain"
    assert res_below.max_score == 0.6499
    assert res_below.chunks == []


def test_confidence_gate_uses_config_threshold(monkeypatch):
    monkeypatch.setattr(config, "CONFIDENCE_THRESHOLD", 0.75)
    gate = ConfidenceGate()
    assert gate.threshold == 0.75

    chunks = [{"similarity_score": 0.70, "chunk_text": "score 0.70"}]
    # 0.70 is < 0.75 threshold
    output = gate.evaluate(chunks)
    assert output.decision == "abstain"
    assert output.max_score == 0.70


def test_confidence_gate_various_score_keys_and_edge_cases():
    gate = ConfidenceGate(threshold=0.60)

    # Test "score" key
    chunks_score = [{"score": 0.80, "chunk_text": "sample"}]
    assert gate.evaluate(chunks_score).decision == "generate"
    assert gate.evaluate(chunks_score).max_score == 0.80

    # Test "relevance_score" key
    chunks_rel = [{"relevance_score": 0.75, "chunk_text": "sample"}]
    assert gate.evaluate(chunks_rel).decision == "generate"
    assert gate.evaluate(chunks_rel).max_score == 0.75

    # Test invalid / string / non-numeric score handling
    chunks_invalid = [
        {"similarity_score": "invalid", "chunk_text": "bad"},
        {"similarity_score": 0.50, "chunk_text": "low"},
    ]
    res_inv = gate.evaluate(chunks_invalid)
    assert res_inv.decision == "abstain"
    assert res_inv.max_score == 0.50


def test_evaluate_confidence_functional_helper():
    chunks = [{"similarity_score": 0.90, "chunk_text": "excellent match"}]
    output = evaluate_confidence(chunks, threshold=0.80)
    assert output.decision == "generate"
    assert output.max_score == 0.90
    assert len(output.chunks) == 1

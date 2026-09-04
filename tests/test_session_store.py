"""Unit test suite for SQLiteSessionStore."""

import tempfile
from pathlib import Path

from src.session.sqlite_store import SQLiteSessionStore


def test_session_store_memory_crud():
    store = SQLiteSessionStore(":memory:")
    session_id = "test-sess-001"

    # Non-existent session initially
    assert store.get_session(session_id) is None
    assert store.get_session_turns(session_id) == []
    assert store.count_turns(session_id) == 0

    # Save user turn
    t1_id = store.save_turn(
        session_id=session_id,
        role="user",
        content="Is Ashwagandha extract patentable in India?",
    )
    assert t1_id > 0
    assert store.count_turns(session_id) == 1
    assert store.count_turns(session_id, role="user") == 1
    assert store.count_turns(session_id, role="assistant") == 0

    # Save assistant turn with citations and metadata
    citations = [
        {
            "doc_id": "patents-act-1970",
            "section": "Section 3(p)",
            "source_url": "https://indiacode.nic.in",
        }
    ]
    metadata = {
        "confidence_score": 0.92,
        "abs_flag": True,
        "status": "answered",
    }
    t2_id = store.save_turn(
        session_id=session_id,
        role="assistant",
        content="Under Section 3(p) of the Patents Act, 1970, traditional knowledge is not patentable.",
        citations=citations,
        response_metadata=metadata,
    )
    assert t2_id > t1_id
    assert store.count_turns(session_id) == 2
    assert store.count_turns(session_id, role="assistant") == 1

    # Retrieve turns
    turns = store.get_session_turns(session_id, limit=10)
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[0]["content"] == "Is Ashwagandha extract patentable in India?"
    assert turns[0]["citations"] is None
    assert turns[1]["role"] == "assistant"
    assert turns[1]["citations"] == citations
    assert turns[1]["response_metadata"]["confidence_score"] == 0.92
    assert turns[1]["response_metadata"]["abs_flag"] is True

    # Retrieve session details
    sess = store.get_session(session_id)
    assert sess is not None
    assert sess["session_id"] == session_id
    assert sess["total_turns"] == 2
    assert sess["created_at"] is not None
    assert sess["updated_at"] is not None

    # Limit parameter in get_session_turns
    limited_turns = store.get_session_turns(session_id, limit=1)
    assert len(limited_turns) == 1
    assert limited_turns[0]["id"] == turns[0]["id"]

    # Delete session
    assert store.delete_session(session_id) is True
    assert store.get_session(session_id) is None
    assert store.get_session_turns(session_id) == []
    assert store.count_turns(session_id) == 0
    assert store.delete_session(session_id) is False

    store.close()


def test_session_store_disk_persistence_and_wal():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_sessions.db"
        store1 = SQLiteSessionStore(db_path)
        session_id = "disk-sess-100"

        store1.save_turn(session_id=session_id, role="user", content="Question 1")
        store1.save_turn(session_id=session_id, role="assistant", content="Answer 1")
        assert store1.count_turns(session_id) == 2
        store1.close()

        # Re-open with new store instance pointing to same file
        store2 = SQLiteSessionStore(db_path)
        sess = store2.get_session(session_id)
        assert sess is not None
        assert sess["total_turns"] == 2

        turns = store2.get_session_turns(session_id)
        assert len(turns) == 2
        assert turns[0]["content"] == "Question 1"
        assert turns[1]["content"] == "Answer 1"
        store2.close()

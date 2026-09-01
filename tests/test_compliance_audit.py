from pathlib import Path

from src.config import config
from src.models.response import QueryResponse


def test_no_hardcoded_model_in_src():
    """Confirms 'gemini-1.5-flash' does not exist in src/ code."""
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert (
            "gemini-1.5-flash" not in content
        ), f"Found hardcoded 'gemini-1.5-flash' in {py_file}"


def test_no_hardcoded_collection_name_in_src():
    """Confirms 'ip_sakti_corpus' does not exist in src/ code."""
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert (
            "ip_sakti_corpus" not in content
        ), f"Found hardcoded 'ip_sakti_corpus' in {py_file}"


def test_no_hardcoded_confidence_in_src_pipeline():
    """Confirms 0.65 is not hardcoded in src/pipeline/ files (must come from config.py)."""
    pipeline_dir = Path("src/pipeline")
    for py_file in pipeline_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "0.65" not in content, f"Found hardcoded 0.65 in {py_file}"


def test_no_getattr_config_with_fallbacks_in_src():
    """Confirms getattr(config, ...) is not used in src/ modules."""
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert (
            "getattr(config" not in content
        ), f"Found getattr(config, ...) fallback anti-pattern in {py_file}"


def test_query_response_has_exact_disclaimer():
    """Confirms every QueryResponse contains the exact legal disclaimer from config."""
    resp_answered = QueryResponse(
        status="answered",
        category="Classical Ayurveda",
        answer="Sample answer",
    )
    assert resp_answered.disclaimer == config.DISCLAIMER_TEXT
    assert "does not constitute legal advice" in resp_answered.disclaimer

    resp_abstained = QueryResponse(
        status="abstained",
        abstention_message=config.ABSTENTION_MESSAGE,
    )
    assert resp_abstained.disclaimer == config.DISCLAIMER_TEXT


def test_env_example_all_variables_commented():
    """Confirms every variable in .env.example has an explanatory comment."""
    env_example_path = Path(".env.example")
    assert env_example_path.exists(), ".env.example must exist"

    lines = env_example_path.read_text(encoding="utf-8").splitlines()
    has_preceding_comment = False

    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            has_preceding_comment = False
            continue
        if stripped.startswith("#"):
            has_preceding_comment = True
            continue
        if "=" in stripped:
            var_name = stripped.split("=")[0].strip()
            assert (
                has_preceding_comment
            ), f"Variable '{var_name}' on line {line_idx + 1} in .env.example has no preceding comment."

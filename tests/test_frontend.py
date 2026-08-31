import ast
from pathlib import Path


def test_styles_css_exists_and_contains_all_design_tokens():
    css_path = Path("src/frontend/styles.css")
    assert css_path.exists(), "src/frontend/styles.css must exist"

    css_content = css_path.read_text(encoding="utf-8")

    # Verify colors
    required_colors = [
        "--color-canvas",
        "--color-surface",
        "--color-border",
        "--color-text-primary",
        "--color-text-secondary",
        "--color-accent",
        "--color-success",
        "--color-warning",
    ]
    for color in required_colors:
        assert color in css_content, f"CSS variable {color} missing from styles.css"

    # Verify typography
    required_typography = [
        "--font-sans",
        "--font-mono",
        "--text-xs",
        "--text-sm",
        "--text-base",
        "--text-lg",
        "--text-xl",
    ]
    for typo in required_typography:
        assert typo in css_content, f"CSS variable {typo} missing from styles.css"

    # Verify spacing
    required_spacing = [
        "--space-1",
        "--space-2",
        "--space-3",
        "--space-4",
        "--space-6",
        "--space-8",
        "--space-12",
    ]
    for space in required_spacing:
        assert space in css_content, f"CSS variable {space} missing from styles.css"

    # Verify radius
    required_radius = ["--radius-sm", "--radius-md", "--radius-lg"]
    for radius in required_radius:
        assert radius in css_content, f"CSS variable {radius} missing from styles.css"


def test_design_system_doc_exists_and_documents_tokens():
    doc_path = Path("src/frontend/design_system.md")
    assert doc_path.exists(), "src/frontend/design_system.md must exist"

    content = doc_path.read_text(encoding="utf-8")
    assert "--color-canvas" in content
    assert "--color-text-primary" in content
    assert "--space-4" in content
    assert "--radius-sm" in content


def test_app_py_syntax_and_css_loading():
    app_path = Path("src/frontend/app.py")
    assert app_path.exists(), "src/frontend/app.py must exist"

    app_content = app_path.read_text(encoding="utf-8")
    # Verify Python syntax validity
    ast.parse(app_content)

    # Verify CSS loading logic and key UI text
    assert "styles.css" in app_content
    assert "IP-SAKTI Sahayak" in app_content
    assert "Ayurveda IP Advisory" in app_content
    assert "INDIA JURISDICTION" in app_content
    assert "category-badge" in app_content
    assert "callout-abs" in app_content
    assert "callout-abstain" in app_content
    assert "session_id" in app_content

    # Verify no personal data collection fields exist
    assert "email" not in app_content.lower()
    assert "phone" not in app_content.lower()
    assert "full_name" not in app_content.lower()


def test_styles_css_contains_category_badge_and_card_header():
    css_path = Path("src/frontend/styles.css")
    css_content = css_path.read_text(encoding="utf-8")
    assert ".category-badge" in css_content
    assert ".card-header-row" in css_content
    assert ".callout-abs" in css_content
    assert ".callout-abstain" in css_content

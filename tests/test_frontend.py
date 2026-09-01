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
        "--color-error",
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
    assert "Ask your Ayurveda IP question" in app_content
    assert "India 🇮🇳" in app_content
    assert "category-badge" in app_content
    assert "card-metadata-bar" in app_content
    assert "citation-marker" in app_content
    assert "citation-target" in app_content
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
    assert ".card-metadata-bar" in css_content
    assert ".citation-marker" in css_content
    assert ".citation-target" in css_content
    assert ".callout-abs" in css_content
    assert ".callout-abstain" in css_content


def test_styles_css_contains_abs_callout_and_citations_accordion_styles():
    css_path = Path("src/frontend/styles.css")
    css_content = css_path.read_text(encoding="utf-8")

    # Issue #28 ABS Callout styling rules
    assert "#FFF3CD" in css_content
    assert "#92400E" in css_content
    assert ".callout-abs-header" in css_content
    assert ".callout-abs-title" in css_content
    assert ".callout-abs-body" in css_content
    assert ".callout-abs-source" in css_content

    # Issue #27 Citations Accordion styling rules
    assert "details.citations-accordion" in css_content
    assert "summary.citations-summary" in css_content
    assert ".summary-arrow" in css_content
    assert "transform: rotate(90deg)" in css_content
    assert ".citations-list" in css_content
    assert ".citation-row" in css_content
    assert "border-left: 3px solid var(--color-border)" in css_content
    assert ".citation-title" in css_content
    assert ".citation-snippet" in css_content
    assert ".citation-url" in css_content
    assert ".citation-meta" in css_content


def test_app_py_contains_notion_abs_and_citations_accordion_elements():
    app_path = Path("src/frontend/app.py")
    app_content = app_path.read_text(encoding="utf-8")

    # Issue #28 ABS Callout elements
    assert "ABS Compliance Note" in app_content
    assert "⚠️" in app_content
    assert "callout-abs-header" in app_content
    assert "callout-abs-title" in app_content
    assert "callout-abs-body" in app_content

    # Issue #27 Citations Accordion elements
    assert 'details class="citations-accordion"' in app_content
    assert 'summary class="citations-summary"' in app_content
    assert "summary-arrow" in app_content
    assert "citations-list" in app_content
    assert "citation-row" in app_content
    assert "citation-title" in app_content
    assert "citation-meta" in app_content


def test_inline_citation_regex_formatting():
    import re

    def format_inline_citations(text: str) -> str:
        def replace_citation(match: re.Match) -> str:
            raw_nums = match.group(1).split(",")
            links = []
            for n in raw_nums:
                num = n.strip()
                if num.isdigit():
                    links.append(
                        f'<a href="#citation-{num}" class="citation-marker" target="_self">[{num}]</a>'
                    )
            return "".join(links) if links else match.group(0)

        processed = re.sub(r"\[(\d+(?:\s*,\s*\d+)*)\]", replace_citation, text)
        paragraphs = [p.strip() for p in processed.split("\n\n") if p.strip()]
        if not paragraphs:
            return f"<p>{processed}</p>"
        return "".join(f"<p>{p.replace(chr(10), '<br/>')}</p>" for p in paragraphs)

    sample = "Under Section 3(p) of the Patents Act 1970 [1], inventions are non-patentable [2, 3]."
    res = format_inline_citations(sample)
    assert '<a href="#citation-1" class="citation-marker" target="_self">[1]</a>' in res
    assert '<a href="#citation-2" class="citation-marker" target="_self">[2]</a>' in res
    assert '<a href="#citation-3" class="citation-marker" target="_self">[3]</a>' in res
    assert res.startswith("<p>")
    assert res.endswith("</p>")


def test_abs_detail_source_formatting():
    import re

    def format_abs_detail(text: str) -> tuple[str, str]:
        source_match = re.search(r"\[Source:\s*([^\]]+)\]", text)
        if source_match:
            src_url = source_match.group(1).strip()
            clean_abs_msg = text[: source_match.start()].strip()
            source_html = f'<div class="callout-abs-source"><strong>Source:</strong> <a href="{src_url}" target="_blank" rel="noopener noreferrer">{src_url} ↗</a></div>'
            return clean_abs_msg, source_html
        return text, ""

    sample_with_source = "Ashwagandha is a biological resource. [Source: https://indiacode.nic.in/handle/123]"
    clean_msg, src_html = format_abs_detail(sample_with_source)
    assert clean_msg == "Ashwagandha is a biological resource."
    assert 'href="https://indiacode.nic.in/handle/123"' in src_html
    assert 'target="_blank"' in src_html

    sample_without_source = "Ashwagandha is a biological resource."
    clean_msg2, src_html2 = format_abs_detail(sample_without_source)
    assert clean_msg2 == "Ashwagandha is a biological resource."
    assert src_html2 == ""

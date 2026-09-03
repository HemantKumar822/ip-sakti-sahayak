"""Frontend test suite for IP-SAKTI Sahayak React/Vite workbench."""

import re
from pathlib import Path


def test_design_tokens_css_exists_and_contains_all_tokens():
    css_path = Path("src/web/src/styles/design_tokens.css")
    assert css_path.exists(), "src/web/src/styles/design_tokens.css must exist"

    css_content = css_path.read_text(encoding="utf-8")

    # Verify color palette and semantic tokens
    required_tokens = [
        "--color-bg-primary",
        "--color-bg-secondary",
        "--color-text-primary",
        "--color-text-secondary",
        "--color-border",
        "--color-accent",
        "--color-success",
        "--color-warning",
        "--color-warning-bg",
        "--color-error",
        "--color-error-bg",
        "--color-info",
        "--color-info-bg",
    ]
    for token in required_tokens:
        assert (
            token in css_content
        ), f"Design token {token} missing from design_tokens.css"

    # Verify typography, shadows, and animations
    assert "--font-family" in css_content
    assert "@keyframes slideUpFadeIn" in css_content
    assert ".animate-fade-in" in css_content
    assert ".glass" in css_content


def test_design_system_doc_exists_and_documents_tokens():
    doc_path = Path("src/web/design_system.md")
    assert doc_path.exists(), "src/web/design_system.md must exist"

    content = doc_path.read_text(encoding="utf-8")
    assert "--color-bg-primary" in content
    assert "--color-text-primary" in content
    assert "--color-warning-bg" in content
    assert "StatutoryBadge.tsx" in content
    assert "Callout.tsx" in content
    assert "PipelineStepper.tsx" in content


def test_react_app_structure_and_components_exist():
    required_files = [
        Path("src/web/src/App.tsx"),
        Path("src/web/src/index.css"),
        Path("src/web/src/api/client.ts"),
        Path("src/web/src/components/ChatInterface.tsx"),
        Path("src/web/src/components/StatutoryBadge.tsx"),
        Path("src/web/src/components/Callout.tsx"),
        Path("src/web/src/components/PipelineStepper.tsx"),
        Path("src/web/src/components/Topbar.tsx"),
        Path("src/web/src/components/HeroState.tsx"),
        Path("src/web/src/components/CitationsDrawer.tsx"),
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Required React file {file_path} must exist"


def test_app_and_chat_interface_content_and_privacy():
    app_content = Path("src/web/src/App.tsx").read_text(encoding="utf-8")
    topbar_content = Path("src/web/src/components/Topbar.tsx").read_text(
        encoding="utf-8"
    )
    chat_content = Path("src/web/src/components/ChatInterface.tsx").read_text(
        encoding="utf-8"
    )

    # Header and Brand
    assert "IP-SAKTI Sahayak" in topbar_content
    assert "India" in topbar_content

    # Key chat features
    assert "Ask your Ayurveda IP question" in chat_content
    assert "PipelineStepper" in chat_content
    assert "Callout" in chat_content
    assert "StatutoryBadge" in chat_content
    assert "session_id" in chat_content

    # Strict Privacy Check (DPDP compliance: no personal data fields)
    assert "email" not in app_content.lower()
    assert "phone" not in app_content.lower()
    assert "full_name" not in app_content.lower()
    assert "email" not in chat_content.lower()
    assert "phone" not in chat_content.lower()
    assert "full_name" not in chat_content.lower()
    assert "email" not in topbar_content.lower()
    assert "phone" not in topbar_content.lower()


def test_callout_component_and_styles():
    callout_tsx = Path("src/web/src/components/Callout.tsx").read_text(encoding="utf-8")
    callout_css = Path("src/web/src/components/Callout.css").read_text(encoding="utf-8")

    assert "callout" in callout_tsx
    assert "callout-abs" in callout_css
    assert "callout-tkdl" in callout_css
    assert "callout-error" in callout_css
    assert "callout-abstain" in callout_css


def test_statutory_badge_component_and_styles():
    badge_tsx = Path("src/web/src/components/StatutoryBadge.tsx").read_text(
        encoding="utf-8"
    )
    badge_css = Path("src/web/src/components/StatutoryBadge.css").read_text(
        encoding="utf-8"
    )

    assert "statutory-badge" in badge_tsx
    assert 'target="_blank"' in badge_tsx
    assert 'rel="noopener noreferrer"' in badge_tsx
    assert ".statutory-badge" in badge_css
    assert ".statutory-badge:hover" in badge_css


def test_pipeline_stepper_component_and_styles():
    stepper_tsx = Path("src/web/src/components/PipelineStepper.tsx").read_text(
        encoding="utf-8"
    )
    stepper_css = Path("src/web/src/components/PipelineStepper.css").read_text(
        encoding="utf-8"
    )

    assert "PII Scrubbed" in stepper_tsx
    assert "Gate Verified" in stepper_tsx
    assert ".pipeline-stepper" in stepper_css
    assert ".stepper-pill" in stepper_css


def test_exact_disclaimer_text_in_react_app():
    app_content = Path("src/web/src/App.tsx").read_text(encoding="utf-8")
    expected_disclaimer = (
        "This information is provided for general awareness and does not constitute legal advice. "
        "Consult a qualified IP attorney for decisions specific to your situation."
    )
    assert expected_disclaimer in app_content


def test_inline_citation_regex_formatting():
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

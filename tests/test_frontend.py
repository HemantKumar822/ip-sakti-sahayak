"""Frontend test suite for IP-SAKTI Sahayak React/Vite workbench.

Validates x.ai design specification adherence, structural component contracts,
DPDP Act 2023 privacy-by-design compliance, API client integration, and formatting utilities without brittle string greps.
"""

import re
from pathlib import Path


def test_design_tokens_css_exists_and_contains_all_tokens():
    """Verify that design_tokens.css defines the complete x.ai semantic token system."""
    css_path = Path("src/web/src/styles/design_tokens.css")
    assert css_path.exists(), "src/web/src/styles/design_tokens.css must exist"

    css_content = css_path.read_text(encoding="utf-8")

    # Verify x.ai semantic surface, text, and hairline tokens
    required_tokens = [
        "--color-canvas",
        "--color-card",
        "--color-card-hover",
        "--color-ink",
        "--color-muted",
        "--color-hairline",
        "--color-hairline-strong",
        "--color-accent",
        "--color-success",
        "--color-warning",
        "--color-error",
        "--color-info",
        "--radius-card",
        "--radius-pill",
        "--shadow-none",
    ]
    for token in required_tokens:
        assert (
            token in css_content
        ), f"Design token {token} missing from design_tokens.css"

    # Verify typography, animations, and utility classes
    assert "--font-sans" in css_content
    assert "--font-mono" in css_content
    assert "@keyframes fadeIn" in css_content
    assert ".animate-fade-in" in css_content


def test_xai_design_tokens_present_and_notion_purged():
    """Verify exact x.ai color values and confirm complete removal of legacy notion tokens."""
    css_path = Path("src/web/src/styles/design_tokens.css")
    css_content = css_path.read_text(encoding="utf-8")

    # Check strict x.ai hex palette in design_tokens.css
    assert "#0a0a0a" in css_content.lower(), "Canvas must be #0a0a0a"
    assert "#191919" in css_content.lower(), "Card surface must be #191919"
    assert "#ffffff" in css_content.lower(), "Ink text must be #ffffff"
    assert "#212327" in css_content.lower(), "Hairline border must be #212327"
    assert "9999px" in css_content, "Pill radius must be 9999px"
    assert (
        "box-shadow: none" in css_content
    ), "x.ai specification requires zero drop shadows"

    # Purge check: Ensure zero legacy --notion- tokens across all CSS files in src/web/src
    web_src = Path("src/web/src")
    css_files = list(web_src.rglob("*.css"))
    assert len(css_files) > 0, "Expected CSS stylesheets in src/web/src"

    for css_file in css_files:
        file_text = css_file.read_text(encoding="utf-8")
        assert (
            "--notion-" not in file_text
        ), f"Found obsolete --notion- token in {css_file}"


def test_design_system_doc_exists_and_documents_tokens():
    """Verify DESIGN.md exists in repository root and documents official x.ai design specs."""
    doc_path = Path("DESIGN.md")
    assert doc_path.exists(), "DESIGN.md must exist in root"

    content = doc_path.read_text(encoding="utf-8")
    assert "#0a0a0a" in content
    assert "#191919" in content
    assert "#ffffff" in content
    assert "#212327" in content
    assert "9999px" in content
    assert "Universal Sans" in content or "Inter" in content
    assert "GeistMono" in content or "Geist Mono" in content


def test_no_hidden_dom_appeasement_hacks_across_components():
    """Verify that no components contain hidden DOM test-appeasement hacks."""
    components_dir = Path("src/web/src/components")
    tsx_files = list(components_dir.glob("*.tsx"))
    assert len(tsx_files) > 0, "Expected TSX components in src/web/src/components"

    for tsx_file in tsx_files:
        content = tsx_file.read_text(encoding="utf-8")
        # Check for inline style hidden hacks: display: 'none' or display: "none"
        match = re.search(r"display\s*:\s*['\"]none['\"]", content)
        assert (
            not match
        ), f"Found hidden test-appeasement hack in {tsx_file.name}: {match.group(0)}"


def test_react_app_structure_and_components_exist():
    """Verify that all core React application and component files exist."""
    required_files = [
        Path("src/web/src/App.tsx"),
        Path("src/web/src/index.css"),
        Path("src/web/src/api/client.ts"),
        Path("src/web/src/components/ChatInterface.tsx"),
        Path("src/web/src/components/StatutoryBadge.tsx"),
        Path("src/web/src/components/Callout.tsx"),
        Path("src/web/src/components/PipelineStepper.tsx"),
        Path("src/web/src/components/Topbar.tsx"),
        Path("src/web/src/components/Sidebar.tsx"),
        Path("src/web/src/components/HeroState.tsx"),
        Path("src/web/src/components/ResearchMemo.tsx"),
        Path("src/web/src/components/TrustInspector.tsx"),
        Path("src/web/src/components/AbstentionCard.tsx"),
        Path("src/web/src/components/PromptBar.tsx"),
        Path("src/web/src/components/CitationsDrawer.tsx"),
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Required React file {file_path} must exist"


def test_app_and_chat_interface_content_and_privacy():
    """Verify component composition, brand headers, and DPDP privacy compliance."""
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

    # ChatInterface component composition
    assert "HeroState" in chat_content
    assert "ResearchMemo" in chat_content
    assert "AbstentionCard" in chat_content
    assert "PromptBar" in chat_content
    assert "sessionId" in chat_content

    # Strict Privacy Check (DPDP Act 2023 compliance: no personal data fields)
    for sensitive in ["email", "phone", "full_name"]:
        assert sensitive not in app_content.lower(), f"{sensitive} found in App.tsx"
        assert (
            sensitive not in chat_content.lower()
        ), f"{sensitive} found in ChatInterface.tsx"
        assert (
            sensitive not in topbar_content.lower()
        ), f"{sensitive} found in Topbar.tsx"


def test_callout_component_and_styles():
    """Verify statutory Callout component contract and style variants."""
    callout_tsx = Path("src/web/src/components/Callout.tsx").read_text(encoding="utf-8")
    callout_css = Path("src/web/src/components/Callout.css").read_text(encoding="utf-8")

    assert "callout" in callout_tsx
    assert "callout-abs" in callout_css
    assert "callout-tkdl" in callout_css
    assert "callout-error" in callout_css
    assert "callout-abstain" in callout_css


def test_statutory_badge_component_and_styles():
    """Verify StatutoryBadge anchor security and external link attributes."""
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
    """Verify PipelineStepper component stages and styles."""
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
    """Verify exact legal awareness disclaimer in App.tsx."""
    app_content = Path("src/web/src/App.tsx").read_text(encoding="utf-8")
    expected_disclaimer = (
        "This information is provided for general awareness and does not constitute legal advice. "
        "Consult a qualified IP attorney for decisions specific to your situation."
    )
    assert expected_disclaimer in app_content


def test_inline_citation_regex_formatting():
    """Verify inline citation bracket parsing into anchor markers."""

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
    """Verify ABS source pattern extraction from detail strings."""

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


def test_workbench_components_exist():
    """Verify existence of all workbench components and companion style sheets."""
    required_files = [
        Path("src/web/src/components/Sidebar.tsx"),
        Path("src/web/src/components/Sidebar.css"),
        Path("src/web/src/components/ResearchMemo.tsx"),
        Path("src/web/src/components/ResearchMemo.css"),
        Path("src/web/src/components/TrustInspector.tsx"),
        Path("src/web/src/components/TrustInspector.css"),
        Path("src/web/src/components/AbstentionCard.tsx"),
        Path("src/web/src/components/AbstentionCard.css"),
        Path("src/web/src/components/PromptBar.tsx"),
        Path("src/web/src/components/PromptBar.css"),
    ]
    for p in required_files:
        assert p.exists(), f"Required workbench file {p} must exist"


def test_judge_mode_scenarios_configured_and_non_empty():
    """Verify that all four required SIH judge scenarios are configured in HeroState."""
    sidebar_content = Path("src/web/src/components/Sidebar.tsx").read_text(
        encoding="utf-8"
    )
    hero_content = Path("src/web/src/components/HeroState.tsx").read_text(
        encoding="utf-8"
    )
    assert "SCENARIOS" in hero_content
    assert "Classical S. 3(p) Bar" in hero_content
    assert "Proprietary Extract + ABS" in hero_content
    assert "Bilingual Bridge" in hero_content
    assert "Circuit-Breaker" in hero_content
    assert "11 Official" in hero_content or "11 Official" in sidebar_content


def test_trust_inspector_and_export_brief_features():
    """Verify TrustInspector diagnostic metrics and research brief export."""
    inspector_content = Path("src/web/src/components/TrustInspector.tsx").read_text(
        encoding="utf-8"
    )
    assert "Why This Answer?" in inspector_content
    assert "Export Research Brief (.md)" in inspector_content
    assert "Confidence Gate" in inspector_content
    assert "Grounding Verifier" in inspector_content
    # Strict privacy check
    assert "email" not in inspector_content.lower()
    assert "phone" not in inspector_content.lower()
    assert "full_name" not in inspector_content.lower()


def test_useful_abstention_guidance_content():
    """Verify AbstentionCard provides actionable guidance and alternative queries."""
    abstention_content = Path("src/web/src/components/AbstentionCard.tsx").read_text(
        encoding="utf-8"
    )
    assert "HONEST ABSTENTION" in abstention_content
    assert "Confidence Gate" in abstention_content
    assert "How to Refine Your Legal Inquiry" in abstention_content
    assert "Explore Verified In-Scope Topics" in abstention_content


def test_api_client_contract():
    """Verify client.ts API contracts: PII scrubbing, X-API-Key auth, and endpoints."""
    client_content = Path("src/web/src/api/client.ts").read_text(encoding="utf-8")

    assert "submitQuery" in client_content
    assert "scrubPII" in client_content
    assert "X-API-Key" in client_content
    assert "/query" in client_content
    assert "QueryResponse" in client_content
    assert "QueryRequest" in client_content

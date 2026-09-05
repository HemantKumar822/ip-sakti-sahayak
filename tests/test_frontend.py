"""Frontend contract suite for the IP-SAKTI Sahayak workbench.

Protects the single `sk-` design vocabulary, the three-view information
architecture (Overview / Clearance Desk / Corpus), memo-based results,
evidence-rail verification, corpus admin contracts, and privacy guarantees.

Deliberately avoids asserting exact DOM structure or snapshot markup so the
implementation stays evolvable.
"""

import re
import subprocess
from pathlib import Path

WEB = Path("src/web/src")
COMP = WEB / "components"
STYLES = WEB / "styles"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_design_tokens_define_terminal_identity():
    css = read(STYLES / "tokens.css")
    for token in [
        "--canvas",
        "--canvas-card",
        "--ink",
        "--mute",
        "--hairline",
        "--accent-sunset",
        "--status-success",
        "--status-error",
        "--radius-sm",
        "--radius-pill",
        "--shadow-none",
        "--font-sans",
        "--font-mono",
    ]:
        assert token in css, f"token {token} missing from tokens.css"
    assert "#0a0a0a" in css.lower()
    assert "#191919" in css.lower()
    assert "9999px" in css


def test_single_design_vocabulary_no_legacy_systems():
    """One vocabulary (`sk-`): no notion- classes, no per-component CSS, no dead token file."""
    assert not (
        STYLES / "design_tokens.css"
    ).exists(), "dead --color-* token file must stay deleted"
    assert (WEB / "index.css").exists()
    style_files = sorted(p.name for p in STYLES.glob("*.css"))
    assert style_files == ["layout.css", "primitives.css", "tokens.css"], style_files
    for tsx in COMP.glob("*.tsx"):
        text = read(tsx)
        assert "--notion-" not in text, f"legacy notion token in {tsx.name}"
        assert "notion-" not in text, f"legacy notion class in {tsx.name}"
        assert (
            ".css'" not in text and '.css"' not in text
        ), f"per-component CSS import in {tsx.name}"
    primitives = read(STYLES / "primitives.css")
    layout = read(STYLES / "layout.css")
    for cls in [
        ".sk-btn",
        ".sk-btn-primary",
        ".sk-card",
        ".sk-tag",
        ".sk-eyebrow",
        ".sk-input",
        ".sk-table",
        ".sk-meter",
        ".sk-alert",
    ]:
        assert cls in primitives, f"{cls} missing from primitives.css"
    for cls in [
        ".sk-shell",
        ".sk-shell-locked",
        ".sk-topbar",
        ".sk-portal",
        ".sk-hero",
        ".sk-section-head",
        ".sk-preview",
        ".sk-cta-band",
        ".sk-notice",
        ".sk-wb",
        ".sk-history",
        ".sk-evidence",
        ".sk-admin",
        ".sk-memo",
        ".sk-dock-chat",
        ".sk-dock-scroll",
        ".sk-dock-inquiry",
        ".sk-drawer",
    ]:
        assert cls in layout, f"{cls} missing from layout.css"


def test_no_emoji_chrome_in_components():
    """Lucide icons only — emoji are content (scenario text), never UI chrome."""
    emoji = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")
    for tsx in COMP.glob("*.tsx"):
        for i, line in enumerate(read(tsx).splitlines(), 1):
            if emoji.search(line):
                assert False, f"emoji chrome in {tsx.name}:{i}: {line.strip()}"


def test_no_hidden_dom_hacks():
    for tsx in COMP.glob("*.tsx"):
        assert not re.search(
            r"display\s*:\s*['\"]none['\"]\s*(?=[,}])", read(tsx)
        ), f"hidden hack in {tsx.name}"


def test_app_shell_three_views_and_providers():
    app = read(WEB / "App.tsx")
    assert "LandingPage" in app and "ChatInterface" in app and "CorpusConsole" in app
    assert "TrustInspector" in app and "CitationModal" in app
    assert "ErrorBoundary" in app and "<ErrorBoundary" in app
    assert "ToastContainer" in app and "<ToastContainer />" in app
    assert "pendingQuery" in app, "portal CTA query must hand off exactly once"
    assert "sk-shell-locked" in app, "workbench must lock the viewport (no page scroll)"
    assert "sk-notice" in app, "auth failure must render the actionable notice"
    assert "restart the frontend" in app, "notice must explain the Vite env restart"
    assert "Retry" in app
    assert (
        "This information is provided for general awareness and does not constitute legal advice. "
        in app
    )
    assert (
        "Consult a qualified IP attorney for decisions specific to your situation."
        in app
    )
    # Session IDs are state plumbing — they must never be rendered as UI text
    assert "Session:" not in app


def test_topbar_navigation_and_live_indicator():
    topbar = read(COMP / "Topbar.tsx")
    assert "Overview" in topbar and "Clearance Desk" in topbar and "Corpus" in topbar
    assert "aria-current" in topbar
    assert "fetchCorpusStats" in topbar
    assert "gazettes" in topbar and "chunks" in topbar
    assert "fetchSessions" not in topbar


def test_landing_answers_what_who_how_and_limits():
    landing = read(COMP / "LandingPage.tsx")
    assert "Know before you file" in landing
    assert "Start a clearance check" in landing
    assert "Inspect the corpus" in landing
    assert (
        "AYUSH formulator" in landing
        and "Patent attorney" in landing
        and "NBA / SBB officer" in landing
    )
    assert "What an answer looks like" in landing, "preview must show the memo shape"
    assert "sk-preview" in landing and "sk-cta-band" in landing
    assert "Bring your formulation" in landing, "closing CTA band must exist"
    assert "How a clearance works" in landing or "clearance works" in landing
    assert (
        "refus" in landing.lower()
    ), "honesty/abstention story must be on the landing page"
    assert (
        "not legal advice" in landing.lower()
        or "Not legal advice" in landing
        or "not a lawyer" in landing
    )
    assert "11 official gazettes" in landing and "296" in landing and "0.65" in landing
    assert "onEnterWorkbench" in landing and "onEnterAdmin" in landing


def test_workbench_is_memo_stream_not_chatbot():
    chat = read(COMP / "ChatInterface.tsx")
    assert "HeroState" in chat and "ResearchMemo" in chat and "AbstentionCard" in chat
    assert "PromptBar" in chat and "FormulationDeconstructor" in chat
    assert "inputMode" not in chat, "mode-tab switcher must stay removed"
    assert "Direct Inquiry" not in chat
    assert "pendingQuery" in chat
    assert (
        "sk-dock-chat" in chat
        and "sk-dock-scroll" in chat
        and "sk-dock-inquiry" in chat
    )
    assert "6" in chat and ("turn" in chat.lower())
    assert "message bubble" not in chat.lower()
    assert "onCitationClick" in chat and "onOpenEvidence" in chat


def test_empty_state_scenarios_cover_four_gates():
    hero = read(COMP / "HeroState.tsx")
    assert "SCENARIOS" in hero
    assert "Classical S. 3(p) Bar" in hero
    assert "Proprietary Extract + ABS" in hero
    assert "Bilingual Bridge" in hero or "Devanagari" in hero
    assert "Circuit-Breaker" in hero or "Abstention Gate" in hero
    assert "11 official gazettes" in hero and "0.65" in hero


def test_inquiry_bar_and_deconstructor_are_structured():
    prompt = read(COMP / "PromptBar.tsx")
    assert "<form" in prompt and 'type="submit"' in prompt
    assert "sk-inquiry-bar" in prompt
    dec = read(COMP / "FormulationDeconstructor.tsx")
    assert "ASU FORMULATION DECONSTRUCTION" in dec
    assert "3(p)" in dec and "3(e)" in dec and "Form I" in dec
    assert "htmlFor" in dec and "Sourced in India" in dec
    assert "onSubmitDeconstruction" in dec


def test_memo_verdict_citations_and_export():
    memo = read(COMP / "ResearchMemo.tsx")
    assert "Verdict" in memo
    assert "sk-cite-marker" in memo
    assert "Authorities" in memo
    assert "Copy" in memo and ("Print" in memo or "print" in memo)
    assert "Official source" in memo
    assert 'target="_blank"' in memo and 'rel="noopener noreferrer"' in memo
    assert "Section 3(p)" in memo and "Section 6" in memo


def test_abstention_refuses_with_next_steps():
    card = read(COMP / "AbstentionCard.tsx")
    assert "No confident answer" in card
    assert 'role="alert"' in card
    assert "Verified in-scope topics" in card
    assert "How to get an answerable inquiry" in card
    assert "65%" in card or "0.65" in card


def test_evidence_rail_telemetry_and_export():
    insp = read(COMP / "TrustInspector.tsx")
    assert "Why this answer?" in insp
    assert "Export Research Brief (.md)" in insp
    assert "Confidence" in insp
    assert "Authorities" in insp
    assert "3(p)" in insp and "Section 6" in insp
    assert "email" not in insp.lower() and "phone" not in insp.lower()
    sidebar = read(COMP / "Sidebar.tsx")
    assert "New inquiry" in sidebar and "History" in sidebar


def test_callout_badge_stepper_contracts():
    callout = read(COMP / "Callout.tsx")
    assert "sk-alert" in callout
    assert "sk-alert-warn" in read(STYLES / "primitives.css")
    badge = read(COMP / "StatutoryBadge.tsx")
    assert 'target="_blank"' in badge and 'rel="noopener noreferrer"' in badge
    stepper = read(COMP / "PipelineStepper.tsx")
    assert "PII scrubbed" in stepper and "Gate verified" in stepper
    drawer = read(COMP / "CitationsDrawer.tsx")
    assert "cited" in drawer.lower() and "Official source" in drawer
    modal = read(COMP / "CitationModal.tsx")
    assert (
        'role="dialog"' in modal and 'aria-modal="true"' in modal and "Escape" in modal
    )


def test_privacy_by_design():
    client = read(WEB / "api" / "client.ts")
    assert "scrubPII" in client and "X-API-Key" in client
    assert "submitQuery" in client and "/query" in client
    assert "QueryResponse" in client and "QueryRequest" in client
    for f in ["App.tsx", "components/ChatInterface.tsx", "components/Topbar.tsx"]:
        text = read(WEB / f)
        assert (
            "email" not in text.lower()
            or "VITE_API_KEY" in text
            or "scrub" in text.lower()
        )


def test_error_boundary_and_toast_contracts():
    eb = read(COMP / "ErrorBoundary.tsx")
    assert "class ErrorBoundary" in eb
    assert "getDerivedStateFromError" in eb and "componentDidCatch" in eb
    assert "Reset Workspace" in eb and "Reload Page" in eb
    assert "SYSTEM FAULT // RECOVERY WORKBENCH" in eb and 'role="alert"' in eb
    toast_tsx = read(COMP / "ToastContainer.tsx")
    assert 'role="region"' in toast_tsx and 'aria-live="polite"' in toast_tsx
    assert "window.addEventListener('offline'" in toast_tsx
    assert "window.addEventListener('online'" in toast_tsx
    util = read(WEB / "utils" / "toast.ts")
    assert "export const toast" in util
    assert (
        "response.status === 429" in client_text()
        and "response.status === 503" in client_text()
    )


def client_text() -> str:
    return read(WEB / "api" / "client.ts")


def test_corpus_console_telemetry_table_and_ingest():
    tsx = read(COMP / "CorpusConsole.tsx")
    client = client_text()
    assert "fetchCorpusStatus" in client and "CorpusStatusResponse" in client
    assert "DocumentBreakdown" in client
    assert "ingestCorpusDocument" in client and "/admin/corpus/ingest" in client
    assert "296" in tsx and "ChromaDB" in tsx and "ip_sakti_legal_corpus" in tsx
    assert "sk-dropzone" in tsx and "handleDragOver" in tsx and "handleDrop" in tsx
    assert (
        "doc_id" in tsx
        and "doc_title" in tsx
        and "document_type" in tsx
        and "source_url" in tsx
    )
    assert "isSubmitting" in tsx and "toast.success" in tsx
    assert (
        "Document Title" in tsx
        and "Chunks" in tsx
        and "Retrieved" in tsx
        and "Source" in tsx
    )
    assert "Admin access restricted" in tsx and "VITE_API_KEY" in tsx
    assert "VALID_ADMIN_API_KEYS" in tsx, "403 copy must name the admin key list"
    assert (
        "Admin privileges required" in client
    ), "client must surface 403 distinctly from 401"
    assert "296 baseline" in tsx
    app = read(WEB / "App.tsx")
    assert "CorpusConsole" in app


def test_gitignore_hygiene_and_no_tracked_artifacts():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in [
        ".coverage",
        "coverage.xml",
        "htmlcov/",
        "src/web/dist/",
        "**/dist/",
        "__pycache__/",
        "*.pptx",
    ]:
        assert pattern in gitignore, f"Expected {pattern} in .gitignore"
    res = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    )
    tracked = res.stdout.splitlines()
    forbidden = [
        re.compile(r"(^|/)\.coverage(\..*)?$"),
        re.compile(r"(^|/)coverage\.xml$"),
        re.compile(r"(^|/)htmlcov(/|$)"),
        re.compile(r"(^|/)src/web/dist(/|$)"),
        re.compile(r"(^|/)__pycache__(/|$)"),
        re.compile(r"\.py[cod]$"),
        re.compile(r"\.pptx$"),
    ]
    for f in tracked:
        for pat in forbidden:
            assert not pat.search(f), f"Forbidden tracked artifact: {f}"

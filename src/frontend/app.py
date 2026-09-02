import os
import re
import uuid
from pathlib import Path

import requests
import streamlit as st

# Set page config with centered layout
st.set_page_config(
    page_title="IP-SAKTI Sahayak",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load external design system CSS
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
if API_HOST == "0.0.0.0":
    # Windows cannot route HTTP requests to 0.0.0.0, use localhost loopback
    API_HOST = "127.0.0.1"
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}"

# Session State Initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Top Bar
st.markdown(
    """
    <div class="top-bar">
        <span class="top-bar-title">🏛️ IP-SAKTI Sahayak</span>
        <span class="top-bar-badge">India 🇮🇳</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Check API Health silently for status indicator
api_online = False
try:
    health_resp = requests.get(f"{API_URL}/health", timeout=2)
    if health_resp.status_code == 200:
        api_online = True
except requests.RequestException:
    api_online = False

with st.sidebar:
    st.markdown("### System Status")
    if api_online:
        st.success("🟢 Backend API Connected")
    else:
        st.warning("🟠 Backend API Offline (Run `python run.py`)")
    st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`")
    st.markdown("---")
    st.markdown(
        "**Guarantees:**\n"
        "- 🛡️ Zero Hallucinations\n"
        "- 🧬 ABS & TKDL Detection\n"
        "- 🔒 Privacy by Design (DPDP Act)"
    )

# Adaptive Page Heading
if not st.session_state.messages:
    st.markdown(
        """
        <div class="page-title">Ask your Ayurveda IP question</div>
        <div class="page-subtitle">Citation-grounded Intellectual Property advisory for Traditional Knowledge & Biological Resources</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="quick-action-header">⚡ Quick-Launch Legal Verification Scenarios</div>',
        unsafe_allow_html=True,
    )
    qcol1, qcol2 = st.columns(2)
    with qcol1:
        if st.button(
            "🌿 Classical: Triphala Patentability",
            use_container_width=True,
            help="Test Section 3(p) Traditional Knowledge Bar",
        ):
            st.session_state.pending_query = "Can a formulation of Triphala and Honey be patented under Indian patent law?"
            st.rerun()
        if st.button(
            "🏷️ Trademark: Chyawanprash Brand",
            use_container_width=True,
            help="Test Trade Marks Act 1999 Section 9 distinctiveness",
        ):
            st.session_state.pending_query = "Can a company register 'Chyawanprash' as an exclusive trademark under Trade Marks Act 1999?"
            st.rerun()
    with qcol2:
        if st.button(
            "🧬 Extraction: Curcumin Process Patent",
            use_container_width=True,
            help="Test Biological Diversity Act Section 6 ABS approval",
        ):
            st.session_state.pending_query = "Can an improved solvent extraction process of Curcumin from Turmeric be patented under Section 3(p)?"
            st.rerun()
        if st.button(
            "🚫 Out-of-Scope: Foreign Trademark",
            use_container_width=True,
            help="Test Jurisdiction Router immediate abstention",
        ):
            st.session_state.pending_query = "What are the legal requirements for registering a corporate trademark in Germany?"
            st.rerun()
else:
    # Compact consultation banner with reset action
    head_col1, head_col2 = st.columns([5, 2])
    with head_col1:
        turn_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        turn_label = "inquiry" if turn_count == 1 else "inquiries"
        st.markdown(
            f"""
            <div class="compact-chat-header">
                <span class="compact-chat-title">🏛️ Active Legal Consultation</span>
                <span style="font-size: 12px; color: #787774;">{turn_count} verified {turn_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with head_col2:
        if st.button(
            "🔄 New Inquiry", use_container_width=True, help="Start a new consultation"
        ):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()


# Format inline citations like [1] or [1, 2] into superscript anchor links
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

    processed = re.sub(
        r"\[(\d+(?:\s*,\s*\d+)*)\]",
        replace_citation,
        text,
    )
    paragraphs = [p.strip() for p in processed.split("\n\n") if p.strip()]
    if not paragraphs:
        return f"<p>{processed}</p>"
    return "".join(f"<p>{p.replace(chr(10), '<br/>')}</p>" for p in paragraphs)


# Render Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        elif message["role"] == "assistant":
            status = message.get("status", "answered")

            if status == "abstained":
                abstain_text = message.get(
                    "content", "Our corpus doesn't contain sufficient evidence..."
                )
                st.markdown(
                    f"""
                    <div class="callout-abstain">
                        <div class="callout-abstain-header">
                            <span class="callout-abstain-icon">💭</span>
                            <span class="callout-abstain-title">We don't have enough information</span>
                        </div>
                        <div class="callout-abstain-body">
                            {abstain_text}
                        </div>
                        <div class="callout-abstain-suggestions">
                            <strong>Try asking about:</strong> Ayurveda patents, ABS compliance, traditional knowledge, or Ayurveda trademarks.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif status == "error":
                st.markdown(
                    f"""
                    <div class="callout-error">
                        <div class="callout-error-header">
                            <span class="callout-error-icon">⚡</span>
                            <span class="callout-error-title">Service temporarily unavailable</span>
                        </div>
                        <div class="callout-error-body">
                            {message.get("content", "Please wait a moment and try again.")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                data = message.get("data", {})
                category = data.get("category", "")
                answer_text = message.get("content", "No answer text returned.")
                jurisdiction = data.get("jurisdiction", "India")
                response_time_ms = data.get("response_time_ms", 0)
                conf_score = data.get("confidence_score", 0.0)

                # 1. Pipeline Stepper HTML
                stepper_html = f"""
                <div class="pipeline-stepper">
                    <span class="stepper-pill completed">🔒 PII Scrubbed</span>
                    <span class="stepper-separator">➔</span>
                    <span class="stepper-pill completed">🏷️ {category or "Categorized"}</span>
                    <span class="stepper-separator">➔</span>
                    <span class="stepper-pill completed">⚖️ {jurisdiction}</span>
                    <span class="stepper-separator">➔</span>
                    <span class="stepper-pill completed">⚡ Hybrid Search (RRF)</span>
                    <span class="stepper-separator">➔</span>
                    <span class="stepper-pill completed">🛡️ Anti-Hallucination Gate</span>
                </div>
                """

                # 2. ABS Callout HTML
                abs_callout_html = ""
                if data.get("abs_flag"):
                    abs_msg = data.get(
                        "abs_detail",
                        "This query involves biological resources. ABS compliance under the Biological Diversity Act 2002 may apply.",
                    )
                    source_match = re.search(r"\[Source:\s*([^\]]+)\]", abs_msg)
                    if source_match:
                        src_url = source_match.group(1).strip()
                        clean_abs_msg = abs_msg[: source_match.start()].strip()
                        source_html = f'<div class="callout-abs-source"><strong>Source:</strong> <a href="{src_url}" target="_blank" rel="noopener noreferrer">{src_url} ↗</a></div>'
                    else:
                        clean_abs_msg = abs_msg
                        source_html = ""

                    abs_callout_html = f"""
                    <div class="callout-abs">
                        <div class="callout-abs-header">
                            <span class="callout-abs-icon">⚠️</span>
                            <span class="callout-abs-title">ABS Compliance Note</span>
                        </div>
                        <div class="callout-abs-body">
                            <div class="callout-abs-text">{clean_abs_msg}</div>
                            {source_html}
                        </div>
                    </div>
                    """

                # 3. TKDL Callout HTML
                tkdl_callout_html = ""
                if data.get("tkdl_flag"):
                    tkdl_msg = data.get(
                        "tkdl_detail",
                        "Traditional Knowledge Prior Art Notice: Inventions based on traditional knowledge or known aggregation of properties are non-patentable under Section 3(p) of the Patents Act, 1970 and subject to TKDL prior art verification.",
                    )
                    tkdl_callout_html = f"""
                    <div class="callout-tkdl">
                        <div class="callout-tkdl-header">
                            <span class="callout-tkdl-icon">🏛️</span>
                            <span class="callout-tkdl-title">Traditional Knowledge & TKDL Prior Art Notice</span>
                        </div>
                        <div class="callout-tkdl-body">
                            {tkdl_msg}
                        </div>
                    </div>
                    """

                # 4. Formatted Answer HTML
                formatted_answer_html = format_inline_citations(answer_text)

                # 5. Statutory Citation Badges HTML
                citations = data.get("citations", [])
                statutory_badges = []
                for cit in citations:
                    c_title = cit.get("title") or cit.get("doc_id", "Statute")
                    c_sec = cit.get("section")
                    c_url = cit.get("source_url")
                    c_label = f"{c_title} (S. {c_sec})" if c_sec else c_title
                    if c_url:
                        statutory_badges.append(
                            f'<a href="{c_url}" target="_blank" rel="noopener noreferrer" class="statutory-citation-badge">📜 {c_label} ↗</a>'
                        )

                statutory_badges_html = ""
                if statutory_badges:
                    statutory_badges_html = f"""
                    <div class="statutory-badge-wrap">
                        {''.join(statutory_badges[:4])}
                    </div>
                    """

                # 6. Citations Accordion HTML
                citations_accordion_html = ""
                if citations:
                    count = len(citations)
                    source_label = "Source" if count == 1 else "Sources"

                    citation_rows = []
                    for idx, cit in enumerate(citations, 1):
                        doc_id = cit.get("doc_id", "Document")
                        section = cit.get("section")
                        snippet = cit.get("snippet", "")
                        source_url = cit.get("source_url")
                        doc_type = cit.get("doc_type") or "Statute"
                        date_retrieved = cit.get("date_retrieved") or "2026-08-01"

                        section_display = (
                            f" — Section: <code>{section}</code>" if section else ""
                        )
                        title_html = f'<div class="citation-title"><strong>[{idx}] {doc_id}</strong>{section_display}</div>'

                        snippet_html = (
                            f'<div class="citation-snippet">"{snippet}"</div>'
                            if snippet
                            else ""
                        )
                        url_html = (
                            f'<div class="citation-url-wrap"><a href="{source_url}" target="_blank" rel="noopener noreferrer" class="citation-url">{source_url} ↗</a></div>'
                            if source_url
                            else ""
                        )
                        meta_html = f'<div class="citation-meta">Retrieved: {date_retrieved} · {doc_type}</div>'

                        citation_rows.append(f"""
                            <div id="citation-{idx}" class="citation-row citation-target">
                                {title_html}
                                {snippet_html}
                                {url_html}
                                {meta_html}
                            </div>
                            """)

                    citation_rows_joined = "".join(citation_rows)
                    citations_accordion_html = f"""
                    <details class="citations-accordion">
                        <summary class="citations-summary">
                            <span class="summary-arrow">▶</span>
                            <span class="summary-title">📄 {count} {source_label}</span>
                        </summary>
                        <div class="citations-list">
                            {citation_rows_joined}
                        </div>
                    </details>
                    """

                # 7. Telemetry Inspector HTML
                telemetry_html = f"""
                <details class="tech-inspector-drawer">
                    <summary>
                        ⚙️ Technical Telemetry & Verification Cockpit
                    </summary>
                    <div class="inspector-grid">
                        <div class="inspector-card">
                            <div class="inspector-label">Anti-Hallucination Score</div>
                            <div class="inspector-val">{conf_score * 100:.1f}%</div>
                        </div>
                        <div class="inspector-card">
                            <div class="inspector-label">Retrieval Mode</div>
                            <div class="inspector-val">Dense + BM25 (RRF)</div>
                        </div>
                        <div class="inspector-card">
                            <div class="inspector-label">End-to-End Latency</div>
                            <div class="inspector-val">{response_time_ms} ms</div>
                        </div>
                        <div class="inspector-card">
                            <div class="inspector-label">DPDP Privacy Hash</div>
                            <div class="inspector-val">{st.session_state.session_id[:8]}...</div>
                        </div>
                    </div>
                </details>
                """

                # Metadata calculations
                category_badge_html = (
                    f'<span class="category-badge">🏷️ {category}</span>'
                    if category
                    else '<span class="category-badge">🏷️ Advisory</span>'
                )
                time_display = (
                    f"Answered in {response_time_ms / 1000:.1f}s"
                    if response_time_ms >= 1000
                    else f"Answered in {response_time_ms} ms"
                )

                # RENDER UNIFIED DOSSIER CARD
                st.markdown(
                    f"""
                    <div class="card">
                        <div class="card-metadata-bar">
                            <div class="card-header-row" style="width: 100%; margin-bottom: 0;">
                                <div>
                                    {category_badge_html}
                                    <span class="meta-separator">•</span>
                                    <span class="meta-item">{jurisdiction}</span>
                                    <span class="meta-separator">•</span>
                                    <span class="meta-item">{time_display}</span>
                                </div>
                                <div style="font-size: 12px; font-weight: 600; color: #10b981;">
                                    🛡️ {conf_score * 100:.0f}% Grounded
                                </div>
                            </div>
                        </div>
                        {stepper_html}
                        {abs_callout_html}
                        {tkdl_callout_html}
                        <div class="card-body">
                            {formatted_answer_html}
                        </div>
                        {statutory_badges_html}
                        {citations_accordion_html}
                        {telemetry_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# Query Input Form (ChatGPT style)
chat_input_val = st.chat_input("Ask your Ayurveda IP question", disabled=not api_online)
prompt = None
if "pending_query" in st.session_state and st.session_state.pending_query:
    prompt = st.session_state.pending_query
    del st.session_state.pending_query
elif chat_input_val:
    prompt = chat_input_val

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        loading_placeholder = st.empty()
        loading_placeholder.markdown(
            """
            <div class="skeleton-card">
                <div class="skeleton" style="width: 25%; height: 20px; border-radius: 9999px; margin-bottom: var(--space-4);"></div>
                <div class="skeleton" style="width: 100%;"></div>
                <div class="skeleton" style="width: 82%;"></div>
                <div class="skeleton" style="width: 95%;"></div>
                <div class="skeleton" style="width: 60%; margin-bottom: 0;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Build conversation history from prior messages (last 6 turns, oldest first)
        history = []
        for m in st.session_state.messages[-6:]:
            role = m["role"]
            if role == "user":
                history.append({"role": "user", "content": m["content"]})
            elif role == "assistant" and m.get("status") == "answered":
                history.append({"role": "assistant", "content": m.get("content", "")})

        payload = {
            "query_text": prompt.strip(),
            "session_id": st.session_state.session_id,
            "conversation_history": history,
        }

        try:
            response = requests.post(
                f"{API_URL}/api/v1/query",
                json=payload,
                timeout=20,
            )
            loading_placeholder.empty()

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "answered")

                if status == "abstained":
                    msg = {
                        "role": "assistant",
                        "status": "abstained",
                        "content": data.get(
                            "abstention_message",
                            "Our corpus doesn't contain sufficient evidence to answer this question accurately. Rather than guess, we prefer to be honest about our limitations.",
                        ),
                    }
                    st.session_state.messages.append(msg)
                    st.rerun()
                else:
                    msg = {
                        "role": "assistant",
                        "status": "answered",
                        "content": data.get("answer", "No answer text returned."),
                        "data": data,
                    }
                    st.session_state.messages.append(msg)
                    st.rerun()
            else:
                msg = {
                    "role": "assistant",
                    "status": "error",
                    "content": f"Please wait a moment and try again. (Status: {response.status_code})",
                }
                st.session_state.messages.append(msg)
                st.rerun()

        except requests.RequestException:
            loading_placeholder.empty()
            msg = {
                "role": "assistant",
                "status": "error",
                "content": "Cannot connect to Backend API. Please ensure the API server is running and try again.",
            }
            st.session_state.messages.append(msg)
            st.rerun()

# Disclaimer Footer
st.markdown(
    """
    <div class="disclaimer-footer">
        This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.
    </div>
    """,
    unsafe_allow_html=True,
)

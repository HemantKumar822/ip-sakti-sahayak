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

if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

# Notion-style Top Bar
st.markdown(
    """
    <div class="top-bar">
        <span class="top-bar-title">🏛️ IP-SAKTI Sahayak</span>
        <span class="top-bar-badge">India 🇮🇳</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Page Heading
st.markdown(
    """
    <div class="page-title">Ask your Ayurveda IP question</div>
    <div class="page-subtitle">Citation-grounded Intellectual Property advisory for Traditional Knowledge & Biological Resources</div>
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
        st.warning("🟠 Backend API Offline (Run `./run_api.sh`)")
    st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`")
    st.markdown("---")
    st.markdown(
        "**Guarantees:**\n"
        "- 🛡️ Zero Hallucinations\n"
        "- 🧬 ABS & TKDL Detection\n"
        "- 🔒 Privacy by Design (DPDP Act)"
    )

# Query Input Form (Notion-style input + Action button)
with st.form(key="query_form", clear_on_submit=False):
    query_input = st.text_area(
        label="Ask your Ayurveda IP question",
        placeholder="e.g. Can I patent an Ayurveda formulation containing Ashwagandha?",
        height=90,
        disabled=st.session_state.is_loading,
    )

    col_note, col_btn = st.columns([4, 1])
    with col_note:
        st.markdown(
            '<div class="jurisdiction-note">This system only covers India jurisdiction (MVP).</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        submit_button = st.form_submit_button(
            label="Ask →",
            disabled=st.session_state.is_loading,
            use_container_width=True,
        )

# Form Submission Processing
if submit_button:
    if not query_input.strip():
        st.warning("Please enter a question before submitting.")
    elif not api_online:
        st.error(
            f"Cannot connect to Backend API at {API_URL}. Please ensure the API server (`./run_api.sh`) is running."
        )
    else:
        with st.spinner("Analyzing legal corpus and validating citations..."):
            payload = {
                "query_text": query_input.strip(),
                "session_id": st.session_state.session_id,
            }
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/query",
                    json=payload,
                    timeout=20,
                )
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "answered")

                    # 1. ABS Detection Alert Callout (Notion Callout Style)
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

                        st.markdown(
                            f"""
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
                            """,
                            unsafe_allow_html=True,
                        )

                    # 2. Abstention vs Answered State
                    if status == "abstained":
                        abstain_text = data.get(
                            "abstention_message",
                            "We don't have enough information in our corpus to answer this accurately. Please consult a qualified IP attorney.",
                        )
                        st.markdown(
                            f"""
                            <div class="callout-abstain">
                                <strong>⚠️ Honest Abstention Notice</strong><br/>
                                {abstain_text}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        category = data.get("category", "")
                        answer_text = data.get("answer", "No answer text returned.")
                        jurisdiction = data.get("jurisdiction", "India")
                        response_time_ms = data.get("response_time_ms", 0)

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
                            paragraphs = [
                                p.strip() for p in processed.split("\n\n") if p.strip()
                            ]
                            if not paragraphs:
                                return f"<p>{processed}</p>"
                            return "".join(
                                f"<p>{p.replace(chr(10), '<br/>')}</p>"
                                for p in paragraphs
                            )

                        formatted_answer_html = format_inline_citations(answer_text)

                        st.markdown(
                            f"""
                            <div class="card">
                                <div class="card-metadata-bar">
                                    {category_badge_html}
                                    <span class="meta-separator">•</span>
                                    <span class="meta-item">{jurisdiction}</span>
                                    <span class="meta-separator">•</span>
                                    <span class="meta-item">{time_display}</span>
                                </div>
                                <div class="card-body">
                                    {formatted_answer_html}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # 3. Citations Accordion (Notion Toggle Style)
                    citations = data.get("citations", [])
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
                        st.markdown(
                            f"""
                            <details class="citations-accordion">
                                <summary class="citations-summary">
                                    <span class="summary-arrow">▶</span>
                                    <span class="summary-title">📄 {count} {source_label}</span>
                                </summary>
                                <div class="citations-list">
                                    {citation_rows_joined}
                                </div>
                            </details>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except requests.RequestException as e:
                st.error(f"Failed to communicate with API server: {e!s}")

# Disclaimer Footer
st.markdown(
    """
    <div class="disclaimer-footer">
        ⚖️ <strong>Legal Disclaimer:</strong> IP-SAKTI Sahayak is an automated informational tool developed for SIH 2026.
        It is provided for general awareness only and does not constitute formal legal advice.
    </div>
    """,
    unsafe_allow_html=True,
)

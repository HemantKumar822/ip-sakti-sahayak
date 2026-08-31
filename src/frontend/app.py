import os
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
        st.warning("🟠 Backend API Offline (Run `run_api.bat`)")
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
            f"Cannot connect to Backend API at {API_URL}. Please ensure `run_api.bat` is running."
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

                    # 1. ABS Detection Alert Callout
                    if data.get("abs_flag"):
                        abs_msg = data.get(
                            "abs_detail",
                            "This query involves biological resources. ABS compliance under the Biological Diversity Act 2002 may apply.",
                        )
                        st.markdown(
                            f"""
                            <div class="callout-abs">
                                <strong>🧬 Access and Benefit Sharing (ABS) Alert</strong><br/>
                                {abs_msg}
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
                        jurisdiction = data.get("jurisdiction", "India (MVP)")
                        response_time = data.get("response_time_ms", 0)

                        category_badge_html = (
                            f'<span class="category-badge">🏷️ {category}</span>'
                            if category
                            else ""
                        )

                        st.markdown(
                            f"""
                            <div class="card">
                                <div class="card-header-row">
                                    <div class="card-title">Advisory Guidance</div>
                                    {category_badge_html}
                                </div>
                                <div class="card-body">{answer_text}</div>
                                <div class="card-meta">
                                    <span>Jurisdiction: <strong>{jurisdiction}</strong></span> &nbsp;•&nbsp;
                                    <span>Response time: <strong>{response_time} ms</strong></span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # 3. Citations Accordion
                    citations = data.get("citations", [])
                    if citations:
                        with st.expander(
                            f"📄 Citations ({len(citations)})",
                            expanded=True,
                        ):
                            for idx, cit in enumerate(citations, 1):
                                doc_id = cit.get("doc_id", "Document")
                                section = cit.get("section", "General")
                                snippet = cit.get("snippet", "")
                                source_url = cit.get("source_url")

                                st.markdown(
                                    f"**{idx}. [{doc_id}]** — Section: `{section}`"
                                )
                                if snippet:
                                    st.caption(f'> "{snippet}"')
                                if source_url:
                                    st.markdown(
                                        f"[View Official Source ↗]({source_url})"
                                    )
                                st.divider()
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

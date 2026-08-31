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

# Top Bar
st.markdown(
    """
    <div class="top-bar">
        <span class="top-bar-title">🏛️ IP-SAKTI Sahayak</span>
        <span class="top-bar-badge">INDIA JURISDICTION</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Page Heading
st.markdown(
    """
    <div class="page-title">Ayurveda IP Advisory</div>
    <div class="page-subtitle">A citation-grounded advisory tool for evaluating prior art, patentability, and compliance under India's Patents Act and Biological Diversity Act.</div>
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

# Query Input Form
with st.form(key="query_form", clear_on_submit=False):
    query_input = st.text_area(
        label="Describe the formulation or patent concept",
        placeholder="Describe the Ayurvedic formulation or patent concept (e.g. Can I patent a formulation containing Ashwagandha and Turmeric?)",
        height=110,
        disabled=st.session_state.is_loading,
    )

    col_note, col_btn = st.columns([4, 1.2])
    with col_note:
        st.markdown(
            '<div class="jurisdiction-note"><span style="font-size: 16px;">🔐</span> All analysis is strictly confidential and anonymized.</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        submit_button = st.form_submit_button(
            label="Generate Advisory",
            disabled=st.session_state.is_loading,
            use_container_width=True,
        )

# Form Submission Processing
if submit_button:
    if not query_input.strip():
        st.warning("Please enter a question or concept before generating the advisory.")
    elif not api_online:
        st.error(
            f"Cannot connect to Backend API at {API_URL}. Please ensure the API server is running."
        )
    else:
        with st.spinner("Analyzing TKDL corpus and evaluating statutory compliance..."):
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
                            "This formulation involves Indian biological resources. Compliance under the Biological Diversity Act 2002 (ABS mechanisms) applies.",
                        )
                        st.markdown(
                            f"""
                            <div class="callout-abs">
                                <strong>🧬 Access and Benefit Sharing (ABS) Alert</strong>
                                {abs_msg}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # 2. Abstention vs Answered State
                    if status == "abstained":
                        abstain_text = data.get(
                            "abstention_message",
                            "The provided concept falls outside the indexed corpus of traditional knowledge and statutory definitions. We cannot confidently evaluate its patentability. Please consult a qualified patent attorney.",
                        )
                        st.markdown(
                            f"""
                            <div class="callout-abstain">
                                <strong>⚠️ Advisory Abstained</strong>
                                {abstain_text}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        category = data.get("category", "")
                        answer_text = data.get("answer", "No advisory generated.")
                        jurisdiction = data.get("jurisdiction", "India (MVP)")
                        response_time = data.get("response_time_ms", 0)

                        category_badge_html = (
                            f'<span class="category-badge">{category}</span>'
                            if category
                            else ""
                        )

                        st.markdown(
                            f"""
                            <div class="card">
                                <div class="card-header-row">
                                    <h2 class="card-title">Advisory Brief</h2>
                                    {category_badge_html}
                                </div>
                                <div class="card-body">{answer_text}</div>
                                <div class="card-meta">
                                    <span>Jurisdiction: <strong>{jurisdiction}</strong></span>
                                    <span>Latency: <strong>{response_time}ms</strong></span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # 3. Citations Accordion
                    citations = data.get("citations", [])
                    if citations:
                        with st.expander(
                            f"📑 Source Citations ({len(citations)})",
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
                                        f"[View Official Record ↗]({source_url})"
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
        <strong>Legal Disclaimer</strong><br>
        IP-SAKTI Sahayak is an automated informational tool. 
        It is provided for general awareness only and does not constitute formal legal advice or clearance.
    </div>
    """,
    unsafe_allow_html=True,
)

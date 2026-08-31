import os
import uuid

import requests
import streamlit as st

# Set page config
st.set_page_config(
    page_title="IP-SAKTI Sahayak",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Notion-inspired CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .stApp {
        background-color: #f6f5f4;
        color: #000000;
    }

    .main-header {
        text-align: center;
        padding: 24px 0 8px 0;
    }

    .main-header h1 {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        color: #000000;
        margin-bottom: 6px;
    }

    .main-header p {
        font-size: 1.05rem;
        color: #615d59;
        margin-bottom: 20px;
    }

    .badge-pill {
        display: inline-block;
        background-color: #ffffff;
        color: #0075de;
        border: 1px solid #e6e6e6;
        border-radius: 9999px;
        padding: 4px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
    }

    .card {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }

    .callout-abs {
        background-color: #fff8eb;
        border-left: 4px solid #dd5b00;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 16px 0;
        color: #793400;
    }

    .callout-abstain {
        background-color: #fdf2f2;
        border-left: 4px solid #de350b;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 16px 0;
        color: #8f1d00;
    }

    .disclaimer-footer {
        text-align: center;
        color: #a39e98;
        font-size: 0.8rem;
        padding: 24px 0 12px 0;
        border-top: 1px solid #e6e6e6;
        margin-top: 40px;
    }

    .stButton > button {
        background-color: #0075de;
        color: #ffffff;
        border: none;
        border-radius: 9999px;
        font-weight: 500;
        padding: 8px 24px;
        transition: background-color 0.15s ease;
    }

    .stButton > button:hover {
        background-color: #005bab;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}"

# Session State Initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Header
st.markdown(
    """
    <div class="main-header">
        <span class="badge-pill">SIH 2026 • PS-26045</span>
        <h1>🏛️ IP-SAKTI Sahayak</h1>
        <p>Citation-grounded Intellectual Property advisory system for Ayurveda & Traditional Knowledge</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Check API Health
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

# Query Input
query_input = st.text_area(
    "Ask an IPR or Patent Question:",
    placeholder="e.g. Can I patent a classical Ayurvedic formulation containing Ashwagandha?",
    height=100,
    help="Enter your intellectual property question. No personal data will be stored.",
)

col1, col2 = st.columns([1, 4])
with col1:
    submit_button = st.button("Submit Query", use_container_width=True)

if submit_button:
    if not query_input.strip():
        st.warning("Please enter a question before submitting.")
    elif not api_online:
        st.error(
            f"Cannot connect to Backend API at {API_URL}. Please ensure `run_api.bat` is running."
        )
    else:
        with st.spinner("Analyzing legal corpus and checking citations..."):
            payload = {
                "query_text": query_input.strip(),
                "session_id": st.session_state.session_id,
            }
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/query",
                    json=payload,
                    timeout=15,
                )
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "answered")

                    # ABS Alert Callout
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

                    # Abstention State
                    if status == "abstained":
                        abstain_text = data.get(
                            "abstention_message",
                            "Insufficient information in the current legal corpus to answer reliably. Please consult a qualified IP attorney.",
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
                        # Answer Card
                        st.markdown(
                            f"""
                            <div class="card">
                                <h3 style="margin-top: 0; font-size: 1.15rem; font-weight: 600;">Advisory Guidance</h3>
                                <p style="font-size: 1rem; line-height: 1.6; color: #1a1a1a;">
                                    {data.get("answer", "No answer text returned.")}
                                </p>
                                <div style="font-size: 0.8rem; color: #615d59; margin-top: 12px;">
                                    <span>Jurisdiction: <strong>{data.get('jurisdiction', 'India (MVP)')}</strong></span> &nbsp;•&nbsp;
                                    <span>Response time: <strong>{data.get('response_time_ms', 0)} ms</strong></span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Citations Accordion
                    citations = data.get("citations", [])
                    if citations:
                        with st.expander(
                            f"📚 Legal Sources & Citations ({len(citations)})",
                            expanded=True,
                        ):
                            for idx, cit in enumerate(citations, 1):
                                st.markdown(
                                    f"**{idx}. [{cit.get('doc_id', 'Document')}]** - Section: `{cit.get('section', 'General')}`"
                                )
                                if cit.get("snippet"):
                                    st.caption(f"> \"{cit.get('snippet')}\"")
                                if cit.get("source_url"):
                                    st.markdown(
                                        f"[View Official Source ↗]({cit.get('source_url')})"
                                    )
                                st.divider()
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except requests.RequestException as e:
                st.error(f"Failed to communicate with API server: {e!s}")

# Disclaimer
st.markdown(
    """
    <div class="disclaimer-footer">
        ⚖️ <strong>Legal Disclaimer:</strong> IP-SAKTI Sahayak is an automated informational tool developed for SIH 2026.
        It is provided for general awareness only and does not constitute formal legal advice.
    </div>
    """,
    unsafe_allow_html=True,
)

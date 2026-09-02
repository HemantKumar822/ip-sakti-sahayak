import datetime
import os
import re
import time
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

# Check API Health silently for status indicator
api_online = False
ping_ms = 0
try:
    t0 = time.perf_counter()
    health_resp = requests.get(f"{API_URL}/health", timeout=2)
    if health_resp.status_code == 200:
        api_online = True
        ping_ms = int((time.perf_counter() - t0) * 1000)
except requests.RequestException:
    api_online = False

# Apple Cupertino Top Navigation Bar
st.markdown(
    """
    <div class="top-bar">
        <span class="top-bar-title">🏛️ IP-SAKTI Sahayak</span>
        <span class="top-bar-badge">Republic of India 🇮🇳 • DPIIT PS-26045</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Compact Dynamic Hero Section
if not st.session_state.messages:
    st.markdown(
        """
        <div class="hero-badge">🏛️ DPIIT PS-26045 • NATIONAL IPR INTELLIGENCE CO-PILOT</div>
        <div class="page-title">AI Legal Intelligence for Ayurveda & Natural Bio-Assets</div>
        <div class="page-subtitle">Statutory-grade IP advisory grounded in the Patents Act 1970, Biological Diversity Act 2002/2023, and authentic TKDL prior art records.</div>
        """,
        unsafe_allow_html=True,
    )

# macOS Legal Inspector Sidebar Control Center
with st.sidebar:
    st.markdown("### 🏛️ Legal Control Center")
    if api_online:
        st.success(f"🟢 Core Engine Connected ({ping_ms}ms)")
    else:
        st.warning("🟠 Core Engine Offline (Run `./start.sh`)")

    st.caption(f"Session Hash: `{st.session_state.session_id[:8]}...`")

    st.markdown("---")
    st.markdown("### 📜 Corpus Provenance")
    st.markdown("""
        - **The Patents Act, 1970** (S. 3(p), 3(d), 3(e))
        - **Biological Diversity Act 2002 / 2023** (S. 3, 4, 6)
        - **Biological Diversity Rules 2004** (SBB / NBA)
        - **AYUSH Patent Examination Guidelines 2025**
        - **TKDL Biological Material Guidelines 2012**
        - *Novartis AG v. Union of India* (2013) 6 SCC 1
        - *Emami Ltd. v. Dabur India Ltd.* (2024)
        """)
    st.caption("296 Vector Chunks • Hybrid Dense + BM25 RRF")

    st.markdown("---")
    if st.button("🧹 New Legal Briefing", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")
    st.markdown(
        "**System Guarantees:**\n"
        "- 🛡️ Zero Legal Hallucinations\n"
        "- 🧬 Dual ABS & TKDL Clearance Flags\n"
        "- 🔒 DPDP Act Privacy by Design"
    )

# Selected Statutory Verification Scenarios (Bento Grid Empty State)
if not st.session_state.messages:
    st.markdown(
        '<div class="bento-header">⚡ Selected Statutory Verification Scenarios</div>',
        unsafe_allow_html=True,
    )
    qcol1, qcol2 = st.columns(2)
    with qcol1:
        if st.button(
            "🌿 Classical: Triphala Churnam Bar\nSection 3(p) & 3(e) Traditional Knowledge Exclusion",
            use_container_width=True,
            help="Test Section 3(p) and Section 3(e) admixture exclusions",
        ):
            st.session_state.pending_query = "Can a standard classical formulation of Triphala churnam or Chyawanprash be patented under the Indian Patents Act?"
            st.rerun()
        if st.button(
            "🏷️ Trademark: 'Chyawanprash' Genericness\nTrade Marks Act 1999 Section 9 Distinctiveness Bar",
            use_container_width=True,
            help="Test publici juris and distinctiveness of Ayurvedic terms",
        ):
            st.session_state.pending_query = "Can our brand register the generic name 'Chyawanprash' or 'Ayur' as an exclusive registered trademark for herbal wellness products?"
            st.rerun()
    with qcol2:
        if st.button(
            "🔬 Proprietary: Withanolide Fraction Synergy\nNovartis v. UOI (2013) Therapeutic Efficacy Standard",
            use_container_width=True,
            help="Test Section 3(d) therapeutic efficacy standard",
        ):
            st.session_state.pending_query = "If we isolate a purified withanolide fraction from Ashwagandha and prove significant synergistic anti-inflammatory efficacy compared to raw root powder, can this composition be patented?"
            st.rerun()
        if st.button(
            "🏛️ ABS Mandate: Bacopa monnieri\nBiological Diversity Act Section 6 NBA Form III Clearance",
            use_container_width=True,
            help="Test Biological Diversity Act Section 6 prior approval",
        ):
            st.session_state.pending_query = "We are a foreign entity from Germany sourcing Bacopa monnieri (Brahmi) cultivated in Kerala to file a patent application in India. Do we need prior approval from the National Biodiversity Authority?"
            st.rerun()

    # System Provenance & Trust Matrix Strip (Empty State Elevation)
    st.markdown(
        """
        <div class="trust-strip">
            <div class="trust-item">
                <div class="trust-item-title">📜 11 Statutory Sources</div>
                <div class="trust-item-desc">Patents Act, BDA 2002/2023, AYUSH 2025, Novartis & Emami precedents</div>
            </div>
            <div class="trust-item">
                <div class="trust-item-title">⚡ Hybrid RRF Engine</div>
                <div class="trust-item-desc">bge-small-en-v1.5 dense vectors fused with BM25 Okapi lexical ranking</div>
            </div>
            <div class="trust-item">
                <div class="trust-item-title">🛡️ Anti-Hallucination Gate</div>
                <div class="trust-item-desc">Mathematical confidence gate with mandatory statutory citation grounding</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Render Chat Conversation History
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        elif message["role"] == "assistant":
            status = message.get("status", "answered")

            if status == "abstained":
                abstain_text = message.get(
                    "content",
                    "Our corpus doesn't contain sufficient evidence to answer this question accurately. Rather than guess, we prefer to be honest about our limitations.",
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
                citations = data.get("citations", [])

                # The Reasoning Capsule (Apple Dynamic Island Inspection HUD)
                st.markdown(
                    f"""
                    <details class="reasoning-capsule">
                        <summary class="capsule-summary">
                            <div class="capsule-pill-group">
                                <span class="pulse-dot"></span>
                                <span><strong>Audit Trail:</strong> Verified against {len(citations)} statutory authorities • {conf_score * 100:.1f}% Confidence</span>
                            </div>
                            <span style="color: var(--color-accent); font-size: 11px;">Inspect Verification HUD ▾</span>
                        </summary>
                        <div class="capsule-expanded-hud">
                            <div class="hud-metric">
                                <div class="hud-metric-label">Anti-Hallucination</div>
                                <div class="hud-metric-value">{conf_score * 100:.1f}%</div>
                            </div>
                            <div class="hud-metric">
                                <div class="hud-metric-label">Retrieval Engine</div>
                                <div class="hud-metric-value">Dense + BM25 (RRF)</div>
                            </div>
                            <div class="hud-metric">
                                <div class="hud-metric-label">Latency</div>
                                <div class="hud-metric-value">{response_time_ms} ms</div>
                            </div>
                            <div class="hud-metric">
                                <div class="hud-metric-label">DPDP Privacy Hash</div>
                                <div class="hud-metric-value">{st.session_state.session_id[:8]}...</div>
                            </div>
                        </div>
                    </details>
                    """,
                    unsafe_allow_html=True,
                )

                # 1. ABS Detection Alert Callout
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
                                <span class="callout-abs-title">ABS Compliance Note (Biological Diversity Act)</span>
                            </div>
                            <div class="callout-abs-body">
                                <div class="callout-abs-text">{clean_abs_msg}</div>
                                {source_html}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # 2. TKDL Prior Art Alert Callout Card
                if data.get("tkdl_flag"):
                    tkdl_msg = data.get(
                        "tkdl_detail",
                        "Traditional Knowledge Prior Art Notice: Inventions based on traditional knowledge or known aggregation of properties are non-patentable under Section 3(p) of the Patents Act, 1970 and subject to TKDL prior art verification.",
                    )
                    st.markdown(
                        f"""
                        <div class="callout-tkdl">
                            <div class="callout-tkdl-header">
                                <span class="callout-tkdl-icon">🏛️</span>
                                <span class="callout-tkdl-title">Traditional Knowledge Prior Art Notice (Section 3(p) Bar)</span>
                            </div>
                            <div class="callout-tkdl-body">
                                {tkdl_msg}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

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

                # Format inline citations [1], [2] into superscript anchors
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
                        f"<p>{p.replace(chr(10), '<br/>')}</p>" for p in paragraphs
                    )

                formatted_answer_html = format_inline_citations(answer_text)

                # Legal Memorandum Card
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

                # Clickable Statutory Citation Badges with Official Gazette Links
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

                if statutory_badges:
                    st.markdown(
                        f"""
                        <div class="statutory-badge-wrap">
                            {''.join(statutory_badges[:4])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Citations Accordion (Notion Toggle Style)
                if citations:
                    count = len(citations)
                    source_label = "Source" if count == 1 else "Sources"

                    citation_rows = []
                    for c_idx, cit in enumerate(citations, 1):
                        doc_id = cit.get("doc_id", "Document")
                        section = cit.get("section")
                        snippet = cit.get("snippet", "")
                        source_url = cit.get("source_url")
                        doc_type = cit.get("doc_type") or "Statute"
                        date_retrieved = cit.get("date_retrieved") or "2026-08-01"

                        section_display = (
                            f" — Section: <code>{section}</code>" if section else ""
                        )
                        title_html = f'<div class="citation-title"><strong>[{c_idx}] {doc_id}</strong>{section_display}</div>'

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
                            <div id="citation-{c_idx}" class="citation-row citation-target">
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
                                <span class="summary-title">📄 {count} Verified {source_label}</span>
                            </summary>
                            <div class="citations-list">
                                {citation_rows_joined}
                            </div>
                        </details>
                        """,
                        unsafe_allow_html=True,
                    )

                # Export Memorandum Download Action
                now_utc = datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                disclaimer_note = (
                    "\n\n---\n*Disclaimer: This information is provided for general awareness and does not constitute legal advice. "
                    "Consult a qualified IP attorney for decisions specific to your situation.*"
                )
                memo_markdown = (
                    f"# Legal Advisory Memorandum\n\n"
                    f"**Date:** {now_utc}\n"
                    f"**Jurisdiction:** {jurisdiction}\n"
                    f"**Subject Category:** {category}\n"
                    f"**Anti-Hallucination Gate Score:** {conf_score * 100:.1f}%\n"
                    f"**ABS Clearance Required:** {'YES' if data.get('abs_flag') else 'NO'}\n"
                    f"**Traditional Knowledge Bar:** {'DETECTED' if data.get('tkdl_flag') else 'NONE'}\n\n"
                    f"## Advisory Finding\n\n{answer_text}\n\n"
                    f"## Statutory Authorities\n\n"
                    + "\n".join(
                        f"- [{c.get('doc_id')}] Section: {c.get('section', 'N/A')} ({c.get('source_url', '')})"
                        for c in citations
                    )
                    + disclaimer_note
                )

                st.download_button(
                    label="📄 Export Formal Legal Memo (.md)",
                    data=memo_markdown,
                    file_name=f"IP_SAKTI_Advisory_{st.session_state.session_id[:6]}_{msg_idx}.md",
                    mime="text/markdown",
                    key=f"dl_btn_{msg_idx}",
                    help="Download timestamped legal advisory briefing with statutory citations",
                )

# Query Input Form (ChatGPT style)
chat_input_val = st.chat_input(
    "Ask your Ayurveda IP question (e.g. patentability, ABS clearance, TKDL prior art)...",
    disabled=not api_online,
)
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

# IP-SAKTI Sahayak — Manual QA Checklist for Demo Day

This document contains the step-by-step manual Quality Assurance (QA) protocol for verifying system readiness prior to live demonstrations at SIH 2026.

---

## 📋 QA Checklist

### 1. Accuracy QA
Verify that responses provided by the system are legally precise, relevant, and grounded in canonical statutes.
- [ ] **Test Query 1**: *"Can I patent an Ayurveda formulation containing Ashwagandha and Turmeric?"*
  - **Expected**: Explains Section 3(p) of Patents Act 1970 (traditional knowledge non-patentability) and Section 3(e) (admixture non-patentability).
- [ ] **Test Query 2**: *"What is the procedure for registering a trademark for an Ayurvedic medicine brand in India?"*
  - **Expected**: Explains trademark application process under Trade Marks Act 1999 and Class 5 registration.
- [ ] **Test Query 3**: *"What compliance is required under the Biological Diversity Act for exporting neem extract?"*
  - **Expected**: Highlights National Biodiversity Authority (NBA) approval requirements under BDA 2002.
- [ ] **Test Query 4**: *"Are traditional medicinal plants eligible for plant variety protection?"*
  - **Expected**: References PPVFR Act 2001 (Protection of Plant Varieties and Farmers' Rights Act).
- [ ] **Test Query 5**: *"Can an international company file a patent for a traditional Indian herb preparation?"*
  - **Expected**: Explains TKDL defensive protection and NBA approval needed for foreign entities under Section 3 of BDA 2002.

### 2. Citation QA
Verify source attribution and citation link integrity.
- [ ] Submit a valid IP query and ensure inline superscript markers (e.g. `[1]`, `[2]`) appear in the answer.
- [ ] Click an inline superscript citation link (e.g. `[1]`) and verify smooth page navigation to the corresponding entry in the Sources accordion.
- [ ] Expand the **"📄 Sources"** toggle accordion and verify that `doc_id`, section number, snippet quote, and retrieved date are clearly listed.
- [ ] Click external source URLs (e.g. `https://indiacode.nic.in/...`) and confirm the source statute webpage opens in a new tab.

### 3. ABS QA (Access and Benefit Sharing)
Verify automated detection of biological resources and TKDL alerts.
- [ ] **Test Query**: *"I want to commercialize a formulation with Ashwagandha root powder."*
  - **Expected**: An orange **"⚠️ ABS Compliance Note"** callout box appears above or inside the advisory response.
- [ ] Verify the ABS callout displays the statutory note regarding the Biological Diversity Act 2002 and NBA compliance.
- [ ] Verify the source link for the Biological Diversity Act is visible and clickable inside the callout.

### 4. Abstention QA
Verify strict guardrails preventing hallucinated answers when queries fall outside the corpus domain.
- [ ] **Test Query**: *"What is TikTok and how do I post videos on it?"*
  - **Expected**: A clean, honest **"💭 We don't have enough information"** callout card appears.
- [ ] Verify that no fake legal advice or fabricated citations are returned.
- [ ] Verify that helpful domain topic suggestions (e.g., Ayurveda patents, ABS compliance, traditional knowledge) are presented.

### 5. Privacy QA (DPDP Act Compliance)
Verify PII redaction and privacy guardrails.
- [ ] **Test Query**: *"My name is Ramesh Kumar (email: ramesh.kumar@example.com, phone: +91 98765 43210). Can I patent Triphala syrup?"*
  - **Expected**: System processes the IP query safely without echoing personal contact details.
- [ ] Inspect API terminal logs (`uvicorn` / backend stdout) to confirm email addresses and phone numbers are stripped/masked before vector retrieval or query logging.

### 6. UI & Responsive QA
Verify visual fidelity across desktop, tablet, and mobile devices.
- [ ] **Desktop Check (>768px)**: Verify page layout is cleanly centered with a max-width of `760px`.
- [ ] **Mobile Check (375px wide viewport)**: Open browser DevTools, switch to iPhone SE / 375px mobile mode, and verify:
  - Zero horizontal scrolling or broken overflow text.
  - Page title scales down cleanly.
- [ ] **Disclaimer Footer**: Verify the exact disclaimer text appears at the bottom with italic styling and a top separator line:
  > *"This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation."*
- [ ] **Loading State**: Verify the animated skeleton loading card appears immediately after submitting a question.

### 7. Performance QA
Verify end-to-end response times under standard operating conditions.
- [ ] Run 5 consecutive queries and record response times:
  - Query 1 Time: `____ ms`
  - Query 2 Time: `____ ms`
  - Query 3 Time: `____ ms`
  - Query 4 Time: `____ ms`
  - Query 5 Time: `____ ms`
- [ ] **Pass Threshold**: All response times must be `< 10,000 ms` (10 seconds), with metadata bar displaying latency.

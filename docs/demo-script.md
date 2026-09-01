# IP-SAKTI Sahayak — 5-Minute SIH Demo Script

This script provides a minute-by-minute walkthrough for presenting **IP-SAKTI Sahayak** live to Smart India Hackathon (SIH) judges.

---

## ⏱️ Timeline & Presentation Flow

### 0:00 – 1:00 | Introduction & Problem Context
- **Presenter Says:**
  > *"Respected Judges, India is home to centuries of traditional knowledge and rich biological resources, particularly in Ayurveda. However, researchers, startups, and practitioners face a major barrier: navigating complex Indian Intellectual Property laws, TKDL protections, and Access and Benefit Sharing (ABS) compliance under the Biological Diversity Act 2002.*
  >
  > *Presenting **IP-SAKTI Sahayak** — a citation-grounded, zero-hallucination AI advisor engineered specifically for Indian IP jurisdiction."*
- **Visual:**
  - Screen displays the clean, Notion-inspired UI with the top bar badge (*"India 🇮🇳"*), page title (*"Ask your Ayurveda IP question"*), and system guarantees in the sidebar.

---

### 1:00 – 2:30 | Core Citation-Grounded Advisory & ABS Alert
- **Presenter Says:**
  > *"Let's test a realistic scenario: A startup founder wants to know if they can patent an Ayurvedic formulation containing Ashwagandha."*
- **Action (Type in Chat):**
  > `Can I patent an Ayurveda formulation containing Ashwagandha?`
- **Presenter Highlights as Screen Updates:**
  1. **Skeleton Loader**: *"Notice the immediate animated loading state giving instant feedback."*
  2. **ABS Compliance Callout**: *"Notice this orange alert box — IP-SAKTI Sahayak automatically detected Ashwagandha as a protected biological resource under the Biological Diversity Act 2002, prompting the user to seek NBA approval."*
  3. **Statutory Answer & Superscript Citations**: *"The answer cites Section 3(p) of the Patents Act 1970 regarding traditional knowledge. Every legal statement has an inline superscript citation `[1]`, `[2]`."*
  4. **Interactive Accordion**: *"Clicking `📄 Sources` expands the exact statute snippets, document IDs, section numbers, and India Code source URLs."*

---

### 2:30 – 3:30 | Guardrails & Abstention Handling
- **Presenter Says:**
  > *"A critical requirement for legal AI is hallucination prevention. When asked a question outside its corpus, IP-SAKTI Sahayak refuses to guess."*
- **Action (Type in Chat):**
  > `What is TikTok and how do I post videos on it?`
- **Presenter Highlights as Screen Updates:**
  - **Abstention Card**: *"Instead of hallucinating fake statutes, it returns a clear callout explaining that the question falls outside its legal corpus, along with suggested Ayurveda IP topics."*

---

### 3:30 – 4:15 | Privacy by Design (DPDP Act) & Mobile Responsiveness
- **Presenter Says:**
  > *"We take privacy and legal safety seriously.*
  > *1. **DPDP Act Compliance**: Personal identifiers such as emails or phone numbers typed into queries are automatically stripped prior to vector search and logging.*
  > *2. **Legal Disclaimer**: As required, our exact legal disclaimer footer is permanently anchored at the bottom across all screens."*
- **Visual / Demonstration:**
  - Resize browser or toggle mobile device view (375px width) to demonstrate fluid responsive layout without horizontal scrolling.

---

### 4:15 – 5:00 | Conclusion & Q&A
- **Presenter Says:**
  > *"IP-SAKTI Sahayak empowers Indian innovators to preserve traditional knowledge while navigating patenting compliance cleanly, deterministically, and instantly. Thank you, and we are ready for your questions!"*

---

## 🎯 Key Prompts Cheatsheet for Presenter

| Demo Stage | Prompt to Type | Key Feature Demonstrated |
|---|---|---|
| **Primary Query** | `Can I patent an Ayurveda formulation containing Ashwagandha?` | Citation-grounded answer, ABS warning, inline superscript citations, sources accordion |
| **Abstention Query** | `What is TikTok?` | Zero hallucination abstention card & domain suggestions |
| **Privacy Check** | `My email is user@example.com. Can I register a trademark for herbal oil?` | PII stripping & trademark advisory |

---
title: "IP-SAKTI Sahayak — Product Requirements Document"
status: final
created: 2026-08-28
updated: 2026-08-28
version: 1.0
sih_ps_id: "PS-26045"
domain: "MedTech / BioTech / HealthTech"
team: "SIH26"
---

# IP-SAKTI Sahayak — Product Requirements Document (PRD)

## 1. Overview

**Product:** IP-SAKTI Sahayak (Intelligent Patent and Scholarly Knowledge for Ayurveda and Traditional Indian Knowledge)
**Problem Statement:** SIH 2026 PS-26045 — AI-powered IPR guidance system for Ayurveda innovations
**Compliance Frame:** 100% DPDP-compliant, India Code sourced, no PII, no personal data collection, disclaimer-mandatory

### Vision Statement

IP-SAKTI Sahayak is a free, accessible, web-based AI guidance tool that helps Ayurveda practitioners, startups, and researchers understand their IP rights under Indian law — without hallucinating legal answers, without collecting personal data, and without pretending to be a lawyer.

---

## 2. User Segments & Journeys

### Primary Users

**UJ-1: The Ayurveda Startup Founder (Ananya)**
Ananya runs a small MSME that manufactures a proprietary Ayurveda formulation. She wants to know if she can patent it. She types: *"Can I patent my proprietary herbal oil blend for joint pain?"*
→ System classifies as "Proprietary Ayurveda," routes to Patents Act + Biological Diversity Act corpus, retrieves Section 3(p) and ABS requirement information, and responds with citations + disclaimer. She learns she needs an ABS clearance before filing.

**UJ-2: The Traditional Practitioner (Rajan)**
Rajan is a vaidya whose family has used a classical formulation for generations. He asks: *"Is my family's Ashwagandha preparation patentable?"*
→ System classifies as "Classical Ayurveda," retrieves relevant TKDL prior art context and Section 3(p) bar, informs him that traditional knowledge is specifically excluded from patent protection, cites TKDL and Patents Act Section 3(p).

**UJ-3: The Student Researcher (Priya)**
Priya is researching regulatory requirements for a college project. She asks a question about product registration categories.
→ System classifies, retrieves Drugs and Cosmetics Act Schedule E details, responds with a structured, cited answer.

**UJ-4: The Out-of-Scope Query (Any user)**
A user asks about a pharmaceutical drug that is not in the Ayurveda category.
→ System detects out-of-scope (not in current corpus + category mismatch), returns clean abstention message: "This query is outside the current scope of IP-SAKTI Sahayak. Please consult a qualified IP attorney or contact a government IP facilitator."

### Secondary Users

- **Government IP Facilitators:** Use the system as a triage and education tool for their clients before human consultation sessions.

---

## 3. Functional Requirements

### FR-1: Product Category Classifier

| ID | Requirement |
|---|---|
| FR-1.1 | System SHALL classify any incoming Ayurveda IPR query into one of the supported categories: Classical/Generic Ayurveda, Proprietary Ayurveda, or Unclassifiable/Out-of-Scope |
| FR-1.2 | Classifier SHALL use a narrowly-prompted LLM call — not free-form generation — with a constrained output schema (category label + confidence) |
| FR-1.3 | If the classifier returns Unclassifiable, the system SHALL immediately enter abstention flow (FR-5) without proceeding to retrieval |
| FR-1.4 | The classifier prompt SHALL be version-controlled alongside the codebase |
| FR-1.5 | Classifier SHALL ask the minimum clarifying question if query is genuinely ambiguous (1 question max, not a quiz) |

### FR-2: Jurisdiction Router

| ID | Requirement |
|---|---|
| FR-2.1 | For MVP, jurisdiction is fixed to India — no International routing |
| FR-2.2 | System SHALL clearly label every response with "Jurisdiction: India" |
| FR-2.3 | Architecture SHALL include a jurisdiction toggle hook for Phase 2 (International) without requiring retrieval layer changes |
| FR-2.4 | If a user query clearly involves international IP (PCT, Madrid, etc.), system SHALL explicitly note this is out-of-scope for MVP and recommend appropriate international IP resources |

### FR-3: Retriever (Simple RAG)

| ID | Requirement |
|---|---|
| FR-3.1 | System SHALL retrieve document chunks ONLY from the curated, version-tracked corpus — never from model memory or internet |
| FR-3.2 | Retrieval SHALL use vector similarity search over pre-computed embeddings |
| FR-3.3 | Retrieval SHALL be scoped to the corpus slice matching the classified product category and jurisdiction |
| FR-3.4 | Retriever SHALL return the top-K chunks (configurable, default K=5) along with their manifest metadata: source_url, doc_id, date_retrieved, doc_type |
| FR-3.5 | Retriever SHALL NOT return chunks without associated manifest metadata — ingestion pipeline enforces this |
| FR-3.6 | Corpus SHALL cover Phase 1 scope: Patents Act 1970 + 2024 Rules (Sections 3(p), 3(d)), Biological Diversity Act 2002 (ABS provisions), Drugs and Cosmetics Act Schedule E, India Code statutes, TKDL publicly available excerpts |

### FR-4: ABS / TKDL Prior Art Checker

| ID | Requirement |
|---|---|
| FR-4.1 | System SHALL run an ABS/TKDL prior art check as a parallel sub-check for any query that touches a biological resource or traditional formulation |
| FR-4.2 | If the check returns a positive flag (query involves a biodiversity resource or TKDL-documented prior art), the response SHALL include a distinct ABS/TKDL flag section |
| FR-4.3 | The flag SHALL cite the specific TKDL reference or ABS obligation trigger — not a generic warning |
| FR-4.4 | The ABS check SHALL be a deterministic rule-based check + retrieval, not a free-form LLM judgment |

### FR-5: Confidence Gate and Abstention

| ID | Requirement |
|---|---|
| FR-5.1 | System SHALL compute a similarity confidence score from retrieval results |
| FR-5.2 | If maximum chunk similarity score < configurable threshold (default: 0.65), system SHALL enter abstention mode |
| FR-5.3 | In abstention mode, system SHALL return a standardized message: "Insufficient information in current corpus to answer this query reliably. Please consult a qualified IP attorney or government IP facilitator." — no partial answer, no guess |
| FR-5.4 | Abstention SHALL log: query text (PII-stripped), timestamp, confidence score, retrieved doc IDs (if any) |
| FR-5.5 | Confidence threshold SHALL be configurable via environment variable without code change |

### FR-6: Answer Generator

| ID | Requirement |
|---|---|
| FR-6.1 | System SHALL generate an answer using ONLY the chunks returned by the retriever — the generation prompt SHALL explicitly prohibit use of model knowledge |
| FR-6.2 | Every factual claim in the generated answer SHALL have an inline citation: [Source: doc_id, section, source_url] |
| FR-6.3 | Answer SHALL include a structured citations list at the end with full manifest metadata for each cited document |
| FR-6.4 | Answer SHALL include the mandatory disclaimer: "This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation." |
| FR-6.5 | Answer SHALL include the jurisdiction label: "Jurisdiction: India (MVP)" |
| FR-6.6 | Answer SHALL include the product category classification used |
| FR-6.7 | If ABS/TKDL flag was triggered, it SHALL appear as a clearly demarcated section in the answer |
| FR-6.8 | Generation SHALL use a structured output schema — not free-form text — to enforce citations and disclaimer presence |

### FR-7: Corpus Ingestion Pipeline

| ID | Requirement |
|---|---|
| FR-7.1 | Ingestion script SHALL accept documents from: TKDL (public excerpts), India Code (indiacode.nic.in), IP India databases (ipindia.gov.in), NBA/ABS guidance (nbaindia.org) |
| FR-7.2 | Every ingested document SHALL be recorded in corpus/manifest.json with required fields: source_url, date_retrieved, document_type, version_or_amendment_date, doc_id |
| FR-7.3 | Ingestion script SHALL REJECT any document missing required manifest fields — hard failure, not warning |
| FR-7.4 | Ingestion pipeline SHALL be runnable as a standalone batch process (not coupled to the API server) |
| FR-7.5 | Corpus SHALL be version-controlled (corpus manifest committed to git) |
| FR-7.6 | Re-ingestion of an updated document version SHALL create a new doc_id and preserve the old entry — no silent overwrite |
| FR-7.7 | Embeddings SHALL be computed during ingestion and stored in the vector DB alongside manifest metadata |

### FR-8: Web Interface

| ID | Requirement |
|---|---|
| FR-8.1 | Interface SHALL provide a single query input field |
| FR-8.2 | Interface SHALL display the jurisdiction label (India, MVP) as a non-interactive label — toggle is a Phase 2 hook, not yet functional |
| FR-8.3 | Interface SHALL display: classified category, answer text with inline citations, full citations list, ABS/TKDL flag if triggered, mandatory disclaimer |
| FR-8.4 | Interface SHALL display abstention message (FR-5.3) in place of an answer when confidence gate fails |
| FR-8.5 | Interface SHALL display response time for transparency |
| FR-8.6 | Interface SHALL NOT collect any personal data — no login, no signup, no name/email/phone fields |
| FR-8.7 | Session state SHALL use anonymous session IDs only |
| FR-8.8 | Interface SHALL be functional on desktop browsers (Chrome, Firefox, Edge latest) |

### FR-9: Privacy and Logging

| ID | Requirement |
|---|---|
| FR-9.1 | Query logs SHALL capture only: anonymous session ID, query text (PII-stripped), classified category, retrieved doc IDs, confidence score, timestamp |
| FR-9.2 | PII stripping SHALL apply a regex filter to remove patterns matching phone numbers, email addresses, Aadhaar-format numbers before logging |
| FR-9.3 | No personal data SHALL be stored — DPDP compliance by architecture, not policy |
| FR-9.4 | Logs SHALL NOT be sent to any third-party analytics service for MVP |

---

## 4. Non-Functional Requirements

### NFR-1: Accuracy
- **NFR-1.1:** System SHALL correctly classify ≥90% of test queries in the golden test set (20 queries across Classical and Proprietary categories)
- **NFR-1.2:** System SHALL produce ≥2 accurate citations per answered query for ≥80% of answerable queries
- **NFR-1.3:** System SHALL produce zero hallucinated legal citations (a citation to a document not in the manifest is a P0 bug)

### NFR-2: Performance
- **NFR-2.1:** End-to-end response time (query received → answer displayed) SHALL be ≤10 seconds on demo hardware
- **NFR-2.2:** Vector similarity search SHALL complete in ≤2 seconds

### NFR-3: Privacy & Compliance
- **NFR-3.1:** DPDP Act 2023 compliant — no personal data processing
- **NFR-3.2:** All data sources SHALL be publicly available official government sources
- **NFR-3.3:** No cookies collecting personal data — session cookies (anonymous ID) only

### NFR-4: Reliability (Demo Day)
- **NFR-4.1:** System SHALL be runnable locally via Docker Compose without external dependencies (for demo resilience)
- **NFR-4.2:** System SHALL degrade gracefully on LLM API failure (return "Service temporarily unavailable" — not crash)

### NFR-5: Maintainability
- **NFR-5.1:** Corpus update (adding a new document) SHALL NOT require code changes — only running the ingestion script
- **NFR-5.2:** Confidence threshold, K (top-K chunks), and LLM model name SHALL all be configurable via environment variables

---

## 5. Out of Scope (MVP)

Explicitly excluded to prevent scope creep:

| Item | Reason | Phase |
|---|---|---|
| International jurisdiction (TRIPS, PCT, Nagoya, Madrid, Hague, Budapest) | Scope cut for demo timeline | Phase 2 |
| Product categories: New Drug, Phytopharmaceutical, Ayurveda-Aahar, Cosmetic | Scope cut | Phase 2 |
| Graph RAG / knowledge graph | Staged after RAG accuracy is proven | Phase 2 |
| Agentic orchestration | Staged after fixed pipeline works | Phase 2 |
| Bhashini multilingual | Architecture hook in, feature deferred | Phase 2 |
| User accounts / authentication | No personal data for MVP | Phase 2 |
| Paid subscription access | Complex auth + logging requirement | Phase 2 |
| Real-time statute update automation | Manual re-ingestion for MVP | Phase 2 |
| Mobile app | Web only | Phase 3 |

---

## 6. Compliance Requirements

| Requirement | Source | Implementation |
|---|---|---|
| "Information, not legal advice" disclaimer | PS-26045 mandatory | Every response — FR-6.4 |
| No personal data collection | DPDP Act 2023 | Architecture (FR-9.1, FR-8.6) |
| Real government data only | PS-26045 + ethics | Corpus manifest enforcement (FR-7.3) |
| ABS/TKDL prior art check | PS-26045 feature req | FR-4 |
| Safe abstention on uncertain queries | PS-26045 safety req | FR-5 |
| Citation grounding on every claim | PS-26045 anti-hallucination | FR-6.1, FR-6.2 |
| Version-tracked corpus | PS-26045 data integrity | FR-7.5, FR-7.6 |

---

## 7. Success Metrics

| Metric | Target | How Measured |
|---|---|---|
| Classifier accuracy | ≥90% | Golden test set (20 queries), manual evaluation |
| Citation accuracy | ≥2 correct citations per answer, 80% of answers | Manual review of demo responses |
| Hallucination rate | 0% | P0 — any citation to non-manifest document |
| Abstention correctness | 100% on out-of-corpus queries | Deliberate test with 3 out-of-corpus questions |
| Response time | ≤10s | Measured on demo hardware |
| ABS flag trigger | Correct on 1 biodiversity test case | Manual test |

**Counter-metrics (guard rails):**
- Abstention rate must NOT exceed 40% on valid in-corpus queries (system is too conservative if so)
- Classifier must NOT require >1 clarifying question per query on average

---

## 8. Milestones (High-Level)

| Milestone | Deliverable |
|---|---|
| M0 — Foundation | Repo setup, corpus ingestion pipeline, manifest schema, CI skeleton |
| M1 — Retrieval Core | Classifier + Retriever + Confidence Gate working end-to-end on test corpus |
| M2 — Full Pipeline | Answer Generator + ABS/TKDL checker + Frontend connected |
| M3 — Demo Ready | Golden test set passing, Docker compose working, all NFRs validated |

---

## 9. Open Questions (Resolved)

All key questions from the Claude conversation have been resolved and locked in this PRD:

| Question | Decision |
|---|---|
| Simple RAG vs Graph RAG? | Simple RAG for MVP. Graph RAG is Phase 2. |
| Fixed pipeline vs Agent? | Fixed pipeline for MVP. Agentic is Phase 2. |
| India only vs full jurisdiction? | India only for MVP. |
| All 6 categories vs subset? | Classical + Proprietary only for MVP. |
| Multilingual? | English only. Bhashini hook deferred to Phase 2. |
| User accounts? | None. Anonymous sessions only. |
| Embeddings: local vs API? | TBD in Architecture step — decision gates corpus build. |
| Frontend: Streamlit vs Next.js? | TBD in Architecture step. |
| Vector DB: ChromaDB vs Qdrant? | TBD in Architecture step. |

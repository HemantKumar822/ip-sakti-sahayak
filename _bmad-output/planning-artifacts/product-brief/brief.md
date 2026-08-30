---
title: "IP-SAKTI Sahayak — Product Brief"
status: final
created: 2026-08-28
updated: 2026-08-28
authors: ["John (PM)", "Hemant Kumar (Team Lead)"]
sih_ps_id: "PS-26045"
sih_domain: "MedTech / BioTech / HealthTech"
---

# IP-SAKTI Sahayak — Product Brief

## The Problem

Ayurveda innovators, small manufacturers, traditional practitioners, and startups face a dense, multi-jurisdictional IP landscape. The intersection of Patents Act, Biological Diversity Act, TKDL, FSSAI Ayurveda-Aahar rules, DPMR Act, and international treaties (TRIPS, Nagoya Protocol, WIPO GRATK, PCT, Madrid, Hague, Budapest) is impossible to navigate without expensive legal counsel. Mistakes — filing a patent on existing TKDL prior art, bypassing ABS requirements, misclassifying a product under the wrong regulatory regime — are costly and irreversible.

Existing tools are either general-purpose legal search engines (no Ayurveda domain model), raw document repositories (no guidance), or paid services inaccessible to small players.

**Root cause:** There is no free, accessible, accurate, citation-grounded guidance tool that (a) correctly classifies an Ayurveda product into its legal category before generating legal guidance, (b) retrieves only verified Indian IP law, and (c) abstains when uncertain rather than hallucinating an answer.

## The Product

**IP-SAKTI Sahayak** is a web-based AI guidance system for Ayurveda IPR queries. A user describes their product or asks an IP question; the system classifies the product, routes to the correct legal corpus slice, retrieves relevant law passages with full citations, and generates a grounded answer — or safely abstains and recommends escalation to a human IP facilitator.

**What it is NOT:** A legal advice service. Every response carries a mandatory disclaimer. The system provides information, not legal counsel.

## Target Users

| User Segment | Pain Point |
|---|---|
| Ayurveda startups & MSMEs | Can't afford IP lawyers; risk costly filing errors |
| Traditional practitioners | Don't know if/how to protect a formulation |
| Students & researchers | Need to understand the regulatory landscape for academic or pre-commercialization work |
| IP facilitators (government) | Need a tool to pre-triage and educate clients before human consultation |

## MVP Scope (Locked)

### In Scope
- **Jurisdiction:** India only
- **Product categories:** Classical / Generic Ayurveda + Proprietary Ayurveda (the two highest-volume categories)
- **Legal corpus (Phase 1 subset):**
  - Patents Act 1970 + 2024 Rules (relevant sections — Section 3(p), 3(d))
  - Biological Diversity Act 2002 (ABS provisions)
  - TKDL prior art database (accessible excerpts via tkdl.res.in)
  - Drugs and Cosmetics Act 1940 — Schedule E rules for classical Ayurveda
  - India Code statutes (indiacode.nic.in) — relevant acts
- **Language:** English only
- **Interface:** Web UI (single page — query input, jurisdiction label, categorized response with citations, abstention message, disclaimer)
- **Pipeline:** Fixed deterministic pipeline (Classify → Route → Retrieve → Confidence-gate → Generate/Abstain)
- **RAG type:** Simple vector RAG (no graph RAG for MVP)
- **Auth / accounts:** None — anonymous sessions only, no PII collected

### Explicitly Out of Scope (MVP)
- International jurisdiction (TRIPS, PCT, Nagoya — Phase 2)
- Remaining 4 product categories: New Drug, Phytopharmaceutical, Ayurveda-Aahar, Cosmetic (Phase 2)
- Graph RAG / agentic orchestration (Phase 2)
- Multilingual via Bhashini (Phase 2 — architecture allows hook-in)
- User accounts, personal data, paid subscription access (Phase 2)
- ABS workflow facilitation (the ABS/TKDL check is in MVP as a compliance flag, not a full workflow)

## Core Non-Negotiables (from PS + DPDP)

1. **No hallucinated law.** Every factual claim must cite a retrieved document ID from the corpus manifest. Zero tolerance.
2. **Safe abstention.** If retrieval confidence is below threshold → the system says "insufficient information, escalate to human IP facilitator." Not a guess.
3. **Disclaimer on every response.** "This is information, not legal advice."
4. **No personal data collection.** Anonymous session IDs only. Query logs stripped of any PII before storage.
5. **Version-tracked corpus.** Every ingested document carries source_url, date_retrieved, doc_type, version. Ingestion script rejects entries missing these fields.
6. **Real data only.** TKDL, India Code, IP India, NBA — no synthetic or fabricated legal text in the corpus.

## Why This Wins (Differentiation)

- **Domain specificity:** Classifier understands Ayurveda product categories — no generic legal tool does this
- **Anti-hallucination architecture:** Retrieval-grounded generation with citation enforcement and abstention gate — not a chatbot bolted onto a law PDF
- **ABS/TKDL prior art check:** Catches the specific risk category (Section 3(p) bar, biopiracy risk) that Ayurveda IP queries most commonly miss
- **Designed for Indian compliance from day 1:** DPDP-compliant, India Code sourced, government-aligned data stack

## Success Criteria (Demo Day)

- System correctly classifies 5 test queries across Classical and Proprietary categories
- Correct answer with ≥2 citations per query for 4 of 5 questions
- Clean abstention on 1 deliberately out-of-corpus question (no hallucination)
- Sub-10-second end-to-end response time on demo hardware
- ABS/TKDL flag correctly triggered on 1 biodiversity-touching test case

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| TKDL data not accessible programmatically | High | Use publicly available excerpts + India Code for MVP; flag TKDL as Phase 1.5 |
| Corpus ingestion takes longer than expected | Medium | Start ingestion Sprint 1, Day 1 — it gates everything else |
| Classifier misclassifies edge cases | Medium | Golden test set of 20 queries built before MVP goes live |
| Team unfamiliar with vector DB setup | Medium | Assign 1 person as "corpus lead" with setup ownership from day 1 |
| Embeddings API cost overrun | Low | Use open-source sentence-transformers locally; API call only for generation |

## Tech Stack Direction (to be finalized in Architecture step)

- **Backend:** Python (FastAPI)
- **Embeddings:** sentence-transformers (local, free) or text-embedding-3-small (OpenAI)
- **Vector DB:** ChromaDB (local for dev) → Qdrant (hosted for demo)
- **LLM:** Gemini 1.5 Flash via Google AI API (free tier sufficient for demo volume)
- **Frontend:** Streamlit (speed) or Next.js (polish) — TBD in Architecture
- **Deployment:** Docker container, Render free tier or local demo
- **Corpus storage:** JSON manifest + raw text files in `/corpus/` directory, version-controlled

## Phase 2 Preview (not building now, but architecture must allow)

- Graph RAG over legal relationship network
- International jurisdiction (TRIPS, PCT, Nagoya, Madrid, Hague, Budapest)
- All 6 product categories
- Bhashini multilingual
- Agentic multi-source orchestration
- User accounts + paid subscription access with explicit logged consent

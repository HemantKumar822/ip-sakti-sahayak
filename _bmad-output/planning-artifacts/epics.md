---
title: "IP-SAKTI Sahayak — Epics and Stories"
project: SIH26
status: final
created: 2026-08-28
updated: 2026-08-28
inputDocuments:
  - _bmad-output/planning-artifacts/prd/prd.md
  - _bmad-output/planning-artifacts/architecture/ARCHITECTURE-SPINE.md
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
---

# IP-SAKTI Sahayak — Epics and Stories

## Overview

**Project:** IP-SAKTI Sahayak
**SIH PS:** 26045
**Jurisdiction:** India (MVP)
**Product Categories in scope:** Classical Ayurveda, Proprietary Ayurveda

---

## Requirements Inventory

### Functional Requirements

- FR-1: Product Category Classifier (FR-1.1 through FR-1.5)
- FR-2: Jurisdiction Router (FR-2.1 through FR-2.4)
- FR-3: Retriever / Simple RAG (FR-3.1 through FR-3.6)
- FR-4: ABS/TKDL Prior Art Checker (FR-4.1 through FR-4.4)
- FR-5: Confidence Gate and Abstention (FR-5.1 through FR-5.5)
- FR-6: Answer Generator (FR-6.1 through FR-6.8)
- FR-7: Corpus Ingestion Pipeline (FR-7.1 through FR-7.7)
- FR-8: Web Interface (FR-8.1 through FR-8.8)
- FR-9: Privacy and Logging (FR-9.1 through FR-9.4)

### Non-Functional Requirements

- NFR-1: Classifier accuracy ≥90%; citation accuracy ≥80%; zero hallucinated citations
- NFR-2: End-to-end response ≤10s; vector search ≤2s
- NFR-3: DPDP Act 2023 compliance; official government data sources only; no personal-data cookies
- NFR-4: Runnable locally via Docker Compose; graceful LLM API failure handling
- NFR-5: Corpus update without code changes; all configurable values via env vars

### Additional Architecture Requirements

- FastAPI server with `POST /api/v1/query` endpoint — structured JSON request/response (AD-3)
- `config.py` is the ONLY place env vars are read — no hardcoding anywhere (AD-9)
- `VectorStore` protocol (interface) must exist so ChromaDB → Qdrant swap is isolated (AD-5)
- Structured Pydantic output schemas for all LLM calls — no free-form parsing (AD-8)
- `corpus/manifest.json` committed to git; ingestion HARD-FAILS on missing metadata (AD-7)
- Docker Compose with `api` + `frontend` services, named ChromaDB volume, corpus mounted (AD-12)
- Embedding model pre-loaded at server startup (FastAPI `lifespan` event) (AD-4)

---

## FR Coverage Map

| FR | Epic | Brief |
|---|---|---|
| FR-7 (all) | Epic 1 | Corpus ingestion pipeline |
| FR-3 (all) | Epic 1 | Vector store + retriever module (built alongside corpus) |
| FR-1 (all) | Epic 2 | Classifier module |
| FR-2 (all) | Epic 2 | Jurisdiction router |
| FR-5 (all) | Epic 2 | Confidence gate |
| FR-4 (all) | Epic 2 | ABS/TKDL checker |
| FR-6 (all) | Epic 3 | Answer generator + citation enforcement |
| FR-8 (all) | Epic 3 | Streamlit frontend |
| FR-9 (all) | Epic 3 | Privacy/logging layer |
| NFR-1 | Epic 4 | Accuracy validation / golden test set |
| NFR-2 | Epic 4 | Performance testing |
| NFR-3,4,5 | Epic 4 | Docker, env config, compliance audit |

---

## Epic List

### Epic 1: Legal Corpus Foundation
Users (and the system) can trust that every answer comes from verified, version-tracked, real Indian legal documents — not model memory. Corpus is ingested, structured, and searchable.
**FRs covered:** FR-7 (all), FR-3 (all)
**Architecture:** AD-4, AD-5, AD-7, AD-9

### Epic 2: Query Processing Pipeline
A user's Ayurveda IPR question is classified, routed to the correct corpus slice, retrieved against verified law chunks, checked for ABS/TKDL relevance, and passed through a confidence gate — before any answer is generated.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5
**Architecture:** AD-1, AD-2, AD-3, AD-8, AD-9

### Epic 3: Answer Delivery and User Interface
The system generates a grounded, cited answer (or clean abstention) and presents it through a web UI with the jurisdiction label, product category, citations, ABS flag (if triggered), disclaimer, and response time.
**FRs covered:** FR-6, FR-8, FR-9
**Architecture:** AD-6, AD-8, AD-10, AD-11

### Epic 4: Demo Readiness and Validation
The system passes the golden test set, runs end-to-end in Docker Compose, meets all NFRs, and is demonstrably hallucination-free.
**FRs covered:** NFR-1, NFR-2, NFR-3, NFR-4, NFR-5

---

## Epic 1: Legal Corpus Foundation

**Goal:** The system has a runnable, validated ingestion pipeline that fetches real Indian legal documents, enforces corpus metadata, computes embeddings, and stores them in ChromaDB. The pipeline is the foundation — nothing else works without this.

---

### Story 1.1: Project Skeleton and Environment Setup

As a developer,
I want the repository skeleton initialized with all configuration and tooling in place,
So that every team member can clone and run the project identically.

**Acceptance Criteria:**

**Given** a developer clones the repository
**When** they copy `.env.example` to `.env` and run `docker-compose up`
**Then** both the API service and frontend service start without errors

**And** `config.py` is the only file that reads environment variables — all other modules import from it
**And** `.env.example` documents every required and optional env var with descriptions
**And** `src/models/request.py` and `src/models/response.py` define the `QueryRequest` and `QueryResponse` Pydantic models from the API contract
**And** the `VectorStore` base protocol (`src/vector_store/base.py`) is defined as an abstract interface
**And** `corpus/manifest.json` exists and is committed (empty array `[]` initially)
**And** `tests/` directory exists with a placeholder test that passes (`test_placeholder.py`)

---

### Story 1.2: Corpus Manifest Validator

As a corpus maintainer,
I want the ingestion script to hard-fail when a document is missing required metadata,
So that no document without full provenance can enter the corpus.

**Acceptance Criteria:**

**Given** a document with all required fields (`source_url`, `date_retrieved`, `document_type`, `version_or_amendment_date`, `doc_id`)
**When** `ingestion/manifest_validator.py` validates it
**Then** validation passes and returns `True`

**Given** a document missing `source_url`
**When** `ingestion/manifest_validator.py` validates it
**Then** validation raises a `ManifestValidationError` with the missing field name — it does NOT emit a warning and continue

**And** the validator checks all five required fields in a single pass
**And** re-ingestion of an updated document version creates a new `doc_id` (e.g., appending `-v2`) and preserves the original entry in `manifest.json` — no silent overwrite

---

### Story 1.3: India Code Corpus Fetcher

As a corpus maintainer,
I want a fetcher that downloads the relevant Indian legal statutes from India Code (indiacode.nic.in),
So that the corpus contains authoritative, dated government law text.

**Acceptance Criteria:**

**Given** `ingestion/fetchers/india_code.py` is run with a list of target statute identifiers (Patents Act 1970, Biological Diversity Act 2002, Drugs and Cosmetics Act 1940 Schedule E)
**When** the fetcher runs
**Then** it downloads each statute and saves the raw text to `corpus/raw/<doc_id>.txt`
**And** it creates a manifest entry for each document with all five required fields correctly populated
**And** `document_type` is set to `"statute"`
**And** the fetcher logs each successful fetch and any failures to stdout
**And** if a fetch fails (network error, 404), it logs the failure and skips that document — it does NOT crash the entire ingestion run

---

### Story 1.4: PDF Parser and Text Chunker

As a corpus maintainer,
I want raw legal documents (PDF or text) to be parsed and split into retrievable chunks,
So that the vector store can find the specific legal passage that answers a question.

**Acceptance Criteria:**

**Given** a raw legal document in `corpus/raw/`
**When** `ingestion/parsers/pdf_parser.py` processes it
**Then** it produces a list of text chunks, each between 300 and 600 tokens
**And** each chunk carries: `doc_id`, `chunk_id` (sequential within document), `chunk_text`, and the source document's manifest metadata
**And** chunks preserve section headings as context (a chunk does not start mid-sentence if avoidable)
**And** an empty document (0 bytes) raises a `ParseError` — it does NOT produce zero chunks silently

---

### Story 1.5: Embedding Computation and ChromaDB Storage

As a corpus maintainer,
I want corpus chunks to be embedded and stored in ChromaDB,
So that the retriever can perform fast vector similarity search over the legal corpus.

**Acceptance Criteria:**

**Given** a list of chunks from Story 1.4
**When** `ingestion/ingest.py` processes them
**Then** each chunk is embedded using `sentence-transformers` with model `BAAI/bge-small-en-v1.5` (configurable via `EMBEDDING_MODEL` env var)
**And** each embedding is stored in the ChromaDB collection named by `CHROMA_COLLECTION_NAME` env var
**And** the ChromaDB entry stores: vector, `doc_id`, `chunk_id`, `source_url`, `doc_type`, `date_retrieved`
**And** `ingestion/ingest.py` rejects chunks from documents not present in `corpus/manifest.json`
**And** after ingestion, `corpus/manifest.json` is updated with chunk count per document
**And** the embedding model is loaded ONCE per ingestion run — not once per chunk

---

### Story 1.6: Retriever Module

As a pipeline stage,
I want a retriever module that takes a query string and returns the top-K most similar corpus chunks with their metadata,
So that the pipeline can use real legal text for answer generation.

**Acceptance Criteria:**

**Given** a query string and the ChromaDB collection is non-empty
**When** `src/pipeline/retriever.py` is called via the `VectorStore` interface
**Then** it returns the top-K chunks (K configurable via `RETRIEVAL_TOP_K`, default 5) sorted by similarity score descending
**And** each returned chunk includes: `chunk_text`, `similarity_score`, `source_url`, `doc_id`, `chunk_id`, `doc_type`, `date_retrieved`
**And** if the collection is empty, the retriever returns an empty list — it does NOT raise an exception
**And** the `ChromaStore` class in `src/vector_store/chroma_store.py` implements the `VectorStore` protocol from `base.py`
**And** `src/pipeline/retriever.py` depends on the `VectorStore` protocol, NOT the concrete `ChromaStore` class directly

---

## Epic 2: Query Processing Pipeline

**Goal:** A user's Ayurveda IPR question flows through the complete deterministic pipeline — classified into a product category, routed to the correct corpus slice, retrieved against law chunks, ABS-checked, and confidence-gated — producing a structured payload ready for the answer generator.

---

### Story 2.1: FastAPI Server Skeleton and Query Endpoint

As a developer,
I want the FastAPI application with the query endpoint wired up (even if pipeline stages are stubs),
So that end-to-end HTTP communication is validated before any pipeline logic is added.

**Acceptance Criteria:**

**Given** the API server is running (`uvicorn src.main:app`)
**When** a `POST /api/v1/query` request is sent with `{"query_text": "test", "session_id": "uuid"}`
**Then** the server returns HTTP 200 with a valid `QueryResponse` JSON body (can be a stub/mock response)
**And** the endpoint validates the `QueryRequest` schema — missing `query_text` returns HTTP 422
**And** the FastAPI app uses a `lifespan` async context manager that loads the embedding model at startup
**And** the app includes a `/health` endpoint returning `{"status": "ok"}`
**And** all routes are in `src/api/routes.py` — `src/main.py` only wires them up

---

### Story 2.2: Product Category Classifier

As a user,
I want the system to classify my Ayurveda question into the correct product category before any legal retrieval,
So that the law retrieved is actually relevant to my product type.

**Acceptance Criteria:**

**Given** a query about a classical Ayurveda formulation
**When** `src/pipeline/classifier.py` processes it via a Gemini API call with structured output
**Then** it returns `{"category": "Classical Ayurveda", "confidence": float, "reason": str}`

**Given** a query that is clearly out of the Ayurveda domain
**When** the classifier processes it
**Then** it returns `{"category": "Unclassifiable", "confidence": float, "reason": str}`

**And** the classifier uses the Pydantic output schema `ClassifierOutput` — no free-form string parsing
**And** if Gemini returns a schema violation, the classifier returns `{"category": "Unclassifiable", "confidence": 0.0, "reason": "schema_error"}`
**And** the classifier prompt is stored in `src/pipeline/classifier.py` as a module-level constant (not hardcoded inline in the function call)
**And** the classifier makes exactly ONE LLM API call per invocation

---

### Story 2.3: Jurisdiction Router

As a pipeline stage,
I want the jurisdiction router to tag the retrieval scope for India,
So that retrieval is scoped only to the correct law corpus and every response is labeled correctly.

**Acceptance Criteria:**

**Given** any query in MVP mode
**When** `src/pipeline/jurisdiction_router.py` processes the classifier output
**Then** it returns `{"jurisdiction": "India", "corpus_tag": "india", "status": "routed"}`

**And** if the user's query text contains explicit references to international IP (PCT, TRIPS, Madrid Protocol), the router returns `{"jurisdiction": "India", "corpus_tag": "india", "status": "out_of_scope_international"}` and sets a flag that will surface in the response
**And** the router reads `DEFAULT_JURISDICTION` from `config.py` — the value "India" is not hardcoded inside the router function
**And** the router does NOT call any external API

---

### Story 2.4: ABS / TKDL Prior Art Checker

As a user with a query touching a biological resource or traditional formulation,
I want the system to flag ABS and TKDL concerns automatically,
So that I am alerted to compliance requirements I might otherwise miss.

**Acceptance Criteria:**

**Given** a query about a formulation containing a named biological resource (e.g., Ashwagandha, Neem, Tulsi)
**When** `src/pipeline/abs_tkdl_checker.py` runs
**Then** it returns `{"abs_flag": true, "abs_detail": "<specific retrieved citation>"}` with a citation from the ABS corpus slice

**Given** a query about an Ayurveda concept not involving a biological resource
**When** the ABS checker runs
**Then** it returns `{"abs_flag": false, "abs_detail": null}`

**And** the checker uses retrieval over the ABS/TKDL corpus slice — it is NOT a hardcoded keyword list
**And** the checker runs as a parallel operation alongside the main retriever — it does NOT block the main retrieval
**And** the checker citation includes `source_url` and `doc_id` from the manifest

---

### Story 2.5: Confidence Gate

As a pipeline stage,
I want the system to abstain when retrieval confidence is too low,
So that users receive a clear "escalate to human" message instead of a hallucinated answer.

**Acceptance Criteria:**

**Given** retrieval returns chunks where the highest similarity score is ≥ `CONFIDENCE_THRESHOLD` (default 0.65)
**When** `src/pipeline/confidence_gate.py` evaluates the results
**Then** it returns `{"decision": "generate", "max_score": float, "chunks": [...]}`

**Given** retrieval returns chunks where the highest similarity score is < `CONFIDENCE_THRESHOLD`
**When** the confidence gate evaluates the results
**Then** it returns `{"decision": "abstain", "max_score": float, "chunks": []}`

**Given** the retriever returns an empty list (corpus was empty)
**When** the confidence gate evaluates
**Then** it returns `{"decision": "abstain", "max_score": 0.0, "chunks": []}`

**And** `CONFIDENCE_THRESHOLD` is read from `config.py` — the float `0.65` is not in the gate function body
**And** the gate logic is a pure function with no side effects

---

## Epic 3: Answer Delivery and User Interface

**Goal:** Users get a structured, cited answer (or a clean abstention) through the web UI — complete with jurisdiction label, product category, inline citations, ABS flag if triggered, mandatory disclaimer, and response time.

---

### Story 3.1: Answer Generator

As a user who submitted a query,
I want a clearly written answer grounded only in the retrieved law,
So that I can trust every claim without wondering if the system made it up.

**Acceptance Criteria:**

**Given** the confidence gate returns `"decision": "generate"` with a list of chunks
**When** `src/pipeline/answer_generator.py` calls Gemini with those chunks
**Then** it returns a `GeneratorOutput` with: `answer` (str), `citations` (list of `Citation`), `abs_flag` (bool), `disclaimer` (str)

**And** the generation prompt explicitly instructs Gemini: "You may ONLY use facts from the provided documents. Do not use your training knowledge."
**And** every `Citation` object contains: `doc_id`, `source_url`, `doc_type`, `section` (str), `date_retrieved`
**And** the answer contains inline citation markers (e.g., `[1]`) that match the citations list
**And** the disclaimer string is always `"This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation."` — it cannot be omitted or paraphrased
**And** the generator uses the `GeneratorOutput` Pydantic schema for structured output — no prose string parsing
**And** if Gemini returns a schema violation, the generator falls back to abstention (`decision: abstain`) — it does NOT return a partial answer

---

### Story 3.2: Privacy / PII Strip and Query Logger

As the system,
I want all queries to be logged after PII stripping,
So that we maintain an audit trail without ever storing personal data.

**Acceptance Criteria:**

**Given** a query text containing an email address (`test@example.com`)
**When** `src/privacy/pii_strip.py` processes it
**Then** it returns the query with the email replaced by `[REDACTED_EMAIL]`

**Given** a query containing a 10-digit phone number
**When** the PII stripper processes it
**Then** it returns the query with the number replaced by `[REDACTED_PHONE]`

**And** the PII strip runs BEFORE the query is logged
**And** the log entry records: `session_id` (UUID, anonymous), `query_text` (stripped), `category` (classifier output), `retrieved_doc_ids` (list), `confidence_score` (float), `decision` (generate/abstain), `timestamp` (ISO 8601)
**And** no field in the log entry contains name, email, phone, Aadhaar-format data
**And** logs are written to stdout (structured JSON) — no external analytics service for MVP

---

### Story 3.3: Full Pipeline Integration (API Route)

As a developer,
I want the `POST /api/v1/query` endpoint to run the complete pipeline end-to-end,
So that an HTTP request to the API produces a real answer or abstention.

**Acceptance Criteria:**

**Given** a valid `POST /api/v1/query` request with a real Ayurveda IPR question
**When** the endpoint processes it
**Then** the response body matches the `QueryResponse` schema with `status: "answered"` and a non-empty `citations` list

**Given** a query about a topic not in the corpus (e.g., semiconductor patents)
**When** the endpoint processes it
**Then** the response body has `status: "abstained"` and `abstention_message` is populated — `answer` is `null`

**And** the pipeline stages run in order: PII-strip → Classify → Route → Retrieve + ABS-check (parallel) → Confidence-gate → Generate/Abstain → Log
**And** `response_time_ms` in the response reflects actual wall-clock time for the full pipeline
**And** if the Gemini API call fails (network error), the endpoint returns HTTP 503 with `{"error": "Service temporarily unavailable"}` — it does NOT return HTTP 500 with a stack trace

---

### Story 3.4: Streamlit Web Interface

As an end user,
I want a clean web UI where I can type my question and receive a structured, cited answer,
So that I can use the system without knowing anything about APIs.

**Acceptance Criteria:**

**Given** the user opens the Streamlit app in a browser
**When** the page loads
**Then** they see: a query input text area, a "Submit" button, and the jurisdiction label ("India (MVP)")

**Given** the user types a question and clicks Submit
**When** the API returns `status: "answered"`
**Then** the UI displays: product category badge, answer text with inline citation markers, a "Citations" expandable section with full citation details, ABS flag section (if `abs_flag: true`), the disclaimer text, and response time

**Given** the API returns `status: "abstained"`
**When** the Streamlit UI renders the response
**Then** it displays only the abstention message and the disclaimer — NOT a partial answer

**And** the UI does NOT have any login, signup, or personal data input fields
**And** a session ID (UUID v4) is generated at session start and sent with every request — it is never displayed to the user
**And** the "Submit" button is disabled while a request is in flight (spinner shown)
**And** the disclaimer is displayed in a visually distinct style (e.g., italic, muted color) on every response

---

## Epic 4: Demo Readiness and Validation

**Goal:** The system passes the golden test set (no hallucinations, correct abstention, ≥2 citations per answer), runs end-to-end in Docker Compose offline, and satisfies all NFRs before demo day.

---

### Story 4.1: Golden Test Set and Accuracy Validation

As the team,
I want a curated set of 20 test queries with expected outcomes,
So that we can measure classifier accuracy, citation accuracy, and hallucination rate objectively before the demo.

**Acceptance Criteria:**

**Given** `tests/golden_queries/test_set.json` contains 20 queries across: Classical Ayurveda (8), Proprietary Ayurveda (8), Out-of-corpus (4)
**When** `tests/test_pipeline_integration.py` runs the full pipeline against each query
**Then** classifier accuracy ≥ 90% (18/20 correctly classified)
**And** for "answered" responses: ≥ 80% have ≥ 2 accurate citations (citation `doc_id` present in `manifest.json`)
**And** hallucinated citations = 0 (any `doc_id` not in `manifest.json` is a test failure, not a warning)
**And** all 4 out-of-corpus queries return `status: "abstained"`
**And** test results are printed as a structured summary: total queries, pass rate per category, hallucination count

---

### Story 4.2: Performance and Docker Compose Validation

As the team,
I want to verify that the system meets response time requirements and runs fully offline in Docker,
So that we are resilient on demo day regardless of network conditions.

**Acceptance Criteria:**

**Given** `docker-compose up` is run on the demo machine with the corpus pre-populated
**When** all services start
**Then** both `api` (port 8000) and `frontend` (port 8501) are accessible and respond correctly
**And** the ChromaDB volume persists between container restarts (corpus does not need to be re-ingested after `docker-compose restart`)
**And** the `corpus/` directory is mounted as a bind mount — not baked into the Docker image

**Given** 5 consecutive queries are submitted via the API
**When** response times are measured
**Then** all 5 complete within 10 seconds end-to-end on the demo hardware
**And** vector search for each query completes within 2 seconds (measured separately by a test that calls the retriever directly)

**And** the API returns HTTP 503 (not a crash) when the Gemini API key is invalid or the API is unreachable

---

### Story 4.3: Compliance and Configuration Audit

As the team,
I want to verify DPDP compliance and that no values are hardcoded,
So that we can confidently claim compliance in front of judges.

**Acceptance Criteria:**

**Given** the full codebase
**When** a grep is run for common hardcoded-value anti-patterns (`0.65`, `gemini-1.5-flash`, `ip_sakti_corpus`, `http://`, any API key pattern)
**Then** zero matches are found in `src/` — all such values are in `.env.example` or `config.py` defaults

**And** `tests/test_privacy.py` confirms: PII stripper removes emails, phone numbers, Aadhaar-format numbers from query text
**And** log output for a test query contains no personal data
**And** the Streamlit UI has no form fields that accept name, email, or phone
**And** the `disclaimer` field in every `QueryResponse` matches the exact string from FR-6.4 — no paraphrase
**And** all environment variables in `.env.example` are documented with a comment explaining their purpose and valid range

---

## Story Dependency Map

```
Epic 1 (Corpus Foundation)
  1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6

Epic 2 (Query Pipeline) — requires Epic 1 complete
  2.1 → 2.2 → 2.3 → 2.4 → 2.5
  (2.4 runs parallel to main retrieval — built after 2.3)

Epic 3 (Answer + UI) — requires Epic 2 complete
  3.1 → 3.2 → 3.3 → 3.4

Epic 4 (Demo Ready) — requires Epic 3 complete
  4.1 → 4.2 → 4.3
```

---

## GitHub Label Scheme

```
component:corpus        → Epic 1 stories
component:pipeline      → Epic 2 stories
component:frontend      → Epic 3 frontend stories
component:api           → Epic 3 API stories
component:privacy       → Story 3.2
component:testing       → Epic 4 stories
component:infra         → Stories 1.1, 4.2
type:feature            → all feature stories
type:validation         → Epic 4 stories
type:bug                → bug reports
priority:p0             → story 4.3 hallucination check, story 2.5 abstention
priority:p1             → all other stories
```

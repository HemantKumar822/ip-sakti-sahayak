---
title: "IP-SAKTI Sahayak — Architecture Spine"
status: final
created: 2026-08-28
updated: 2026-08-28
altitude: initiative
paradigm: deterministic-retrieval-augmented-generation-pipeline
---

# IP-SAKTI Sahayak — Architecture Spine

## Paradigm

**Deterministic Retrieval-Augmented Generation (RAG) Pipeline.**

Every request follows a fixed, ordered sequence of single-responsibility stages. No LLM decides the routing, no tool-calling at runtime, no improvised paths. Determinism is the anti-hallucination property — not a limitation.

---

## Architecture Decisions (AD)

### AD-1: Fixed Pipeline, No Agentic Routing
**Binds:** All pipeline stages are executed in a fixed, coded sequence — Classify → Route → Retrieve → Confidence-Gate → Generate/Abstain
**Prevents:** Any runtime LLM tool-calling, dynamic stage-skipping, or agentic decision-making over the pipeline path
**Rule:** No stage may conditionally call another stage out of sequence. Branch points (YES/NO at confidence gate, abstain/generate) are hard-coded — not LLM decisions.
**[ADOPTED]** — confirmed by PRD + PS-26045 explicit staging

---

### AD-2: Python as the Sole Backend Language
**Binds:** All pipeline stages, ingestion scripts, and API server are Python
**Prevents:** Node.js, Go, or other runtimes for backend logic (frontend may differ)
**Rule:** `src/` directory contains only Python. No mixed-runtime backend.
**Rationale:** Team comfort, ML ecosystem (sentence-transformers, langchain-core, chromadb all native Python), SIH demo pragmatism

---

### AD-3: FastAPI as the HTTP API Layer
**Binds:** The HTTP server exposing the pipeline is a FastAPI application
**Prevents:** Flask, Django, Express for the query endpoint
**Rule:** Single route: `POST /api/v1/query` — returns structured JSON response schema (defined in FR-6.8)
**Rationale:** Async-native, auto-generates OpenAPI schema, type-safe with Pydantic — fits the structured output requirement

---

### AD-4: sentence-transformers for Embeddings (Local, Free)
**Binds:** Embeddings are computed using `sentence-transformers` library with model `BAAI/bge-small-en-v1.5` (or equivalent small, fast model)
**Prevents:** Using OpenAI / Google embedding APIs in the ingestion or retrieval path
**Rule:** No external API call during embedding. Embeddings are computed locally during ingestion and at query time. This keeps the system runnable offline (critical for demo resilience).
**Deferred:** Phase 2 may swap in a larger embedding model — the swap point is the model name in config, not code changes.

---

### AD-5: ChromaDB as Vector Database (Local for MVP)
**Binds:** Vector similarity search uses ChromaDB (persistent local store, file-based)
**Prevents:** FAISS (no metadata support), Pinecone (paid, external), Qdrant (external for demo day)
**Rule:** ChromaDB collection name is configurable via env var. Collection stores: embedding vector + manifest metadata (source_url, doc_id, doc_type, date_retrieved, chunk_id).
**Deferred:** Qdrant for hosted post-demo deployment. The abstraction layer (retriever module) uses a `VectorStore` protocol — swapping implementations requires only a new concrete class, no pipeline changes.

---

### AD-6: Gemini 1.5 Flash as the Generation LLM
**Binds:** All LLM generation calls (classifier + answer generator) use Google Gemini 1.5 Flash via `google-generativeai` SDK
**Prevents:** OpenAI GPT-4, Anthropic Claude, local Ollama models as primary
**Rule:** Model name, temperature, and max_output_tokens are environment variables — not hardcoded.
**Rationale:** Google AI API free tier sufficient for demo volume; aligns with SIH's government-tech context; Gemini has strong structured output support (required for FR-6.8).
**[ASSUMPTION]** — if Gemini free tier rate limits trigger during demo, fallback is `gemini-1.5-flash-8b`. Flag this as a risk in demo prep.

---

### AD-7: Corpus Manifest as the Single Source of Truth for Data Lineage
**Binds:** `corpus/manifest.json` is the authoritative record of every ingested document. Every vector DB entry MUST have a corresponding manifest entry.
**Prevents:** Ingesting documents without metadata, storing embeddings without provenance, any "raw" document in the vector DB without a manifest record
**Rule:** `ingestion/ingest.py` fails hard (raises, does not warn) if a document is missing: `source_url`, `date_retrieved`, `document_type`, `version_or_amendment_date`, `doc_id`. The manifest is committed to git. Re-ingestion of an updated document creates a new `doc_id` and preserves the old entry.
**[ADOPTED]** — defined in FR-7.2, FR-7.3

---

### AD-8: Structured Output Schema for All LLM Calls
**Binds:** Every LLM call in the pipeline MUST use a structured output schema (Pydantic model passed to Gemini's `response_schema` parameter)
**Prevents:** Free-form string parsing of LLM output, regex extraction of citations from prose
**Rule:** Classifier output schema: `{category: str, confidence: float, reason: str}`. Generator output schema: `{answer: str, citations: list[Citation], abs_flag: bool, disclaimer: str}`. If Gemini returns a schema violation, the pipeline treats it as a confidence-gate failure and abstains.

---

### AD-9: Confidence Threshold is Configuration, Not Code
**Binds:** The similarity confidence threshold (below which the system abstains) is read from the environment variable `CONFIDENCE_THRESHOLD` (default: `0.65`)
**Prevents:** Hardcoded float literals in pipeline code
**Rule:** All configurable values (threshold, K, model name, chroma collection name, corpus path) live in `config.py` which reads from environment. `config.py` is the only place that reads env vars.

---

### AD-10: No Personal Data in Any Storage Layer
**Binds:** Query logs, session state, and vector DB metadata contain ZERO personally identifiable information
**Prevents:** Logging user names, emails, phone numbers, Aadhaar-format numbers, or any DPDP-covered personal data
**Rule:** Before any query text is logged, it passes through `privacy/pii_strip.py` which applies regex filters. Session IDs are UUID v4 generated server-side — never correlated with identity.
**[ADOPTED]** — DPDP Act 2023 compliance requirement

---

### AD-11: Frontend — Streamlit (MVP)
**Binds:** The web UI is a Streamlit application
**Prevents:** React/Next.js, Vue, or raw HTML for MVP
**Rule:** Frontend communicates with the FastAPI backend via HTTP (not direct Python import) — even though Streamlit can import Python directly, keeping the boundary clean allows Phase 2 to replace Streamlit without touching the API.
**Rationale:** Fastest path to a working UI for a mixed-skill team; Streamlit handles state, layout, and hot-reload. The API boundary is the architectural invariant; Streamlit is the replaceable leaf.
**Deferred:** Phase 2 frontend can be Next.js. The FastAPI API spec is the contract — frontend is a detail.

---

### AD-12: Docker Compose as the Deployment Unit
**Binds:** The complete application (API + frontend + ChromaDB volume) is runnable via `docker-compose up`
**Prevents:** Separate manual startup scripts, dependence on any cloud service for demo
**Rule:** `docker-compose.yml` defines two services: `api` (FastAPI) and `frontend` (Streamlit). ChromaDB persists via a named volume. The corpus directory is mounted as a volume (not baked into the image) so it can be updated without rebuilding.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│                   (Streamlit Frontend :8501)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │  HTTP POST /api/v1/query
                            │  {query_text, session_id}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Query Server                          │
│                     (Python :8000)                              │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │  1. Classify  │───▶│  2. Route    │───▶│  3. Retrieve    │  │
│  │  (Gemini LLM) │    │  (India MVP) │    │  (ChromaDB)     │  │
│  │  category +   │    │  tags corpus │    │  top-K chunks   │  │
│  │  confidence   │    │  slice       │    │  + metadata     │  │
│  └──────────────┘    └──────────────┘    └────────┬────────┘  │
│                                                    │            │
│                                      ┌─────────────▼──────────┐│
│                                      │  4. ABS/TKDL Check     ││
│                                      │  (parallel sub-check)  ││
│                                      └─────────────┬──────────┘│
│                                                    │            │
│                                      ┌─────────────▼──────────┐│
│                                      │  5. Confidence Gate    ││
│                                      │  score ≥ 0.65?         ││
│                                      └──────┬────────┬────────┘│
│                                            YES       NO        │
│                                             │         │         │
│                                    ┌────────▼──┐ ┌───▼───────┐ │
│                                    │6. Generate│ │6b. Abstain│ │
│                                    │(Gemini LLM│ │standard   │ │
│                                    │structured │ │message    │ │
│                                    │output)    │ └───────────┘ │
│                                    └────────┬──┘               │
│                                             │                  │
│                                    ┌────────▼──────────────┐   │
│                                    │  7. Response          │   │
│                                    │  answer + citations   │   │
│                                    │  + ABS flag (if any)  │   │
│                                    │  + disclaimer         │   │
│                                    │  + jurisdiction label │   │
│                                    └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

OFFLINE BATCH (runs before demo / on corpus update):
┌─────────────────────────────────────────────────────────────────┐
│             Corpus Ingestion Pipeline                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  Fetch docs  │─▶│ Parse + chunk│─▶│ Embed (sentence-trans) │ │
│  │  TKDL,       │  │ validate     │  │ store in ChromaDB      │ │
│  │  India Code, │  │ manifest     │  │ update manifest.json   │ │
│  │  IP India,   │  │ fields       │  │                        │ │
│  │  NBA         │  │ REJECT if    │  │                        │ │
│  └─────────────┘  │ missing      │  └────────────────────────┘ │
│                   └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure (Seed)

```
ip-sakti-sahayak/
├── README.md
├── docker-compose.yml
├── .env.example                   # All configurable env vars documented
├── .env                           # Git-ignored
│
├── corpus/
│   ├── manifest.json              # Authoritative corpus manifest (committed)
│   ├── raw/                       # Raw source documents (gitignored if large)
│   └── embeddings/                # ChromaDB persistent storage (gitignored)
│
├── ingestion/
│   ├── ingest.py                  # Main ingestion script
│   ├── fetchers/
│   │   ├── india_code.py
│   │   ├── tkdl.py
│   │   ├── ip_india.py
│   │   └── nba.py
│   ├── parsers/
│   │   └── pdf_parser.py
│   └── manifest_validator.py      # Hard-fail on missing fields
│
├── src/
│   ├── config.py                  # ONLY place env vars are read
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   └── routes.py              # POST /api/v1/query
│   ├── pipeline/
│   │   ├── classifier.py          # FR-1
│   │   ├── jurisdiction_router.py # FR-2
│   │   ├── retriever.py           # FR-3
│   │   ├── abs_tkdl_checker.py    # FR-4
│   │   ├── confidence_gate.py     # FR-5
│   │   └── answer_generator.py   # FR-6
│   ├── models/
│   │   ├── request.py             # QueryRequest Pydantic model
│   │   └── response.py            # QueryResponse, Citation Pydantic models
│   ├── vector_store/
│   │   ├── base.py               # VectorStore protocol (interface)
│   │   └── chroma_store.py        # ChromaDB implementation
│   └── privacy/
│       └── pii_strip.py           # PII regex filter (FR-9.2)
│
├── frontend/
│   └── app.py                     # Streamlit UI
│
└── tests/
    ├── golden_queries/
    │   └── test_set.json          # 20 golden queries with expected outputs
    ├── test_classifier.py
    ├── test_retriever.py
    ├── test_confidence_gate.py
    └── test_pipeline_integration.py
```

---

## Environment Configuration

All configurable values in `.env.example`:

```env
# LLM
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_OUTPUT_TOKENS=2048

# Embeddings
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Vector Store
CHROMA_COLLECTION_NAME=ip_sakti_corpus
CHROMA_PERSIST_DIR=./corpus/embeddings

# Pipeline
CONFIDENCE_THRESHOLD=0.65
RETRIEVAL_TOP_K=5

# Corpus
CORPUS_MANIFEST_PATH=./corpus/manifest.json
CORPUS_RAW_DIR=./corpus/raw

# Privacy
PII_STRIP_ENABLED=true

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

## API Contract

### `POST /api/v1/query`

**Request:**
```json
{
  "query_text": "Can I patent my proprietary herbal oil blend?",
  "session_id": "uuid-v4-anonymous"
}
```

**Response (answered):**
```json
{
  "status": "answered",
  "category": "Proprietary Ayurveda",
  "jurisdiction": "India (MVP)",
  "answer": "Based on the retrieved documents...",
  "citations": [
    {
      "doc_id": "patents-act-1970-s3p",
      "source_url": "https://indiacode.nic.in/...",
      "doc_type": "statute",
      "section": "Section 3(p)",
      "date_retrieved": "2026-08-20"
    }
  ],
  "abs_flag": true,
  "abs_detail": "This query involves a biological resource. ABS clearance may be required under the Biological Diversity Act 2002 Section 6.",
  "confidence_score": 0.82,
  "disclaimer": "This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.",
  "response_time_ms": 4200
}
```

**Response (abstained):**
```json
{
  "status": "abstained",
  "category": "Unclassifiable",
  "jurisdiction": "India (MVP)",
  "answer": null,
  "citations": [],
  "abs_flag": false,
  "confidence_score": 0.31,
  "abstention_message": "Insufficient information in current corpus to answer this query reliably. Please consult a qualified IP attorney or government IP facilitator.",
  "disclaimer": "This information is provided for general awareness and does not constitute legal advice.",
  "response_time_ms": 1100
}
```

---

## Phase 2 Extension Points (Architecture Allows)

These are designed-in hooks — not built now, but the current architecture does NOT need to be torn down to add them:

| Phase 2 Feature | Extension Point |
|---|---|
| International jurisdiction | `jurisdiction_router.py` — add `INTERNATIONAL` branch, tag corpus slice |
| More product categories | `classifier.py` — extend schema categories list + add corpus documents |
| Graph RAG | `retriever.py` — implement `GraphStore` class conforming to `VectorStore` protocol |
| Bhashini multilingual | Pre-processing step before classifier, post-processing step after generator |
| Agentic orchestration | Replace `pipeline/` sequence with an orchestrator — the individual stage modules remain reusable |
| Next.js frontend | Drop-in replacement — FastAPI contract unchanged |

---

## Key Risks (Architecture Level)

| Risk | Impact | Mitigation |
|---|---|---|
| TKDL programmatic access blocked | High — reduces corpus coverage | Use publicly available TKDL excerpts (PDF/web); flag as known gap in demo |
| Gemini API rate limit during demo | High — demo fails | Pre-warm, cache test responses; have offline demo mode with pre-computed answers |
| Embedding model cold start slow | Medium — first query takes 30s+ | Pre-load model at server startup (`lifespan` event in FastAPI) |
| ChromaDB collection empty at demo | Critical | Ingestion script is Sprint 1, Day 1; CI checks collection is non-empty before merge |

---

## Deferred Decisions

| Decision | Why Deferred |
|---|---|
| Production vector DB (Qdrant vs ChromaDB) | Post-demo deployment decision; ChromaDB sufficient for MVP |
| LLM provider for Phase 2 (multi-provider) | Single provider (Gemini) sufficient for MVP |
| Corpus update automation (cron vs webhook) | Manual re-ingestion is acceptable for MVP; schedule post-demo |
| Per-category corpus partitioning strategy | Single collection with metadata filter is sufficient for 2 categories |

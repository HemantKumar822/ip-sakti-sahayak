# IP-SAKTI Sahayak

> AI-powered Ayurveda IPR guidance system — SIH 2026 Problem Statement PS-26045

## What is this?

**IP-SAKTI Sahayak** (Intelligent Patent and Scholarly Knowledge for Ayurveda and Traditional Indian Knowledge) is a web-based AI system that helps Ayurveda practitioners, startups, and researchers understand their IP rights under Indian law.

**Core guarantees:**
- ✅ Every answer is grounded in retrieved Indian law — not model memory
- ✅ Every claim has an inline citation with `source_url` + document ID
- ✅ System abstains (not guesses) when corpus confidence is too low
- ✅ Zero personal data collected — DPDP Act 2023 compliant
- ✅ "Information, not legal advice" disclaimer on every response

## Architecture

Fixed deterministic RAG pipeline: **Classify → Route → Retrieve → ABS-check → Confidence-gate → Generate/Abstain**

See [`docs/planning/architecture/ARCHITECTURE-SPINE.md`](docs/planning/architecture/ARCHITECTURE-SPINE.md) for full architecture decisions.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Embeddings | sentence-transformers (`BAAI/bge-small-en-v1.5`) |
| Vector Store | ChromaDB (local/MVP) |
| LLM | Gemini 1.5 Flash (Google AI API) |
| Frontend | Streamlit |
| Deployment | Docker Compose |

## SIH 2026 Context

- **PS ID:** 26045
- **Domain:** MedTech / BioTech / HealthTech
- **Team:** SIH26 (5-6 members)
- **MVP Scope:** India jurisdiction, Classical + Proprietary Ayurveda categories

## Planning Docs

All planning artifacts are in [`docs/planning/`](docs/planning/):

- [Product Brief](docs/planning/product-brief/brief.md)
- [PRD](docs/planning/prd/prd.md)
- [Architecture Spine](docs/planning/architecture/ARCHITECTURE-SPINE.md)
- [Epics and Stories](docs/planning/epics.md)
- [Sprint Status](docs/planning/sprint-status.yaml)

## GitHub Workflow

```
main (protected) ← develop ← feature/<issue-number>-<short-name>
```

- Every piece of work starts as a GitHub Issue
- PRs require 1 approval, link the issue with `Closes #N`
- Squash-merge into `develop`

## Getting Started (coming Sprint 1)

```bash
cp .env.example .env
# Add your GEMINI_API_KEY
docker-compose up
```

## Compliance

- Data sources: TKDL, India Code, IP India, NBA (official government sources only)
- No personal data stored: anonymous session IDs only
- Mandatory disclaimer on every response
- DPDP Act 2023 compliant by architecture

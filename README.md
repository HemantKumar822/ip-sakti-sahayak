# 🏛️ IP-SAKTI Sahayak

> **SIH 2026 | PS-26045**  
> An AI-powered Intellectual Property advisory system for Traditional Knowledge, Ayurveda, and Biological Resources. Built for India. 🇮🇳

IP-SAKTI Sahayak provides inventors, researchers, and MSMEs with accurate, citation-backed answers to complex IP questions. Unlike general-purpose LLMs, this system relies on a **strict RAG architecture** (Retrieval-Augmented Generation) constrained to an official, curated corpus of Indian law — guaranteeing zero hallucinations.

---

## ✨ Key Features

- **🛡️ Anti-Hallucination Pipeline**: The AI can *only* answer using retrieved legal documents. Every sentence is backed by a verifiable citation linking to the exact source.
- **🧬 ABS Detection**: Automatically flags queries involving biological resources that require Access and Benefit Sharing (ABS) compliance under the Biological Diversity Act 2023.
- **💭 Honest Abstention**: If the answer isn't in the corpus, the system confidently says "I don't know" instead of guessing.
- **🔒 Privacy by Design (DPDP Act)**: Strips PII (Personal Identifiable Information) from all queries before logging. No user data is stored.
- **🎨 Notion-Inspired UI**: A calm, clean, minimal user interface designed for readability and professional use.

---

## 🏗️ Architecture Stack

We rely on a deterministic, testable pipeline rather than "LLM magic".

| Component | Technology | Purpose |
|---|---|---|
| **API Backend** | `FastAPI` (Python) | High-performance, async-first query orchestration |
| **Vector DB** | `ChromaDB` | Fast semantic search (running locally, no cloud dependency) |
| **LLM Engine** | `Gemini 1.5 Flash` | Fast, structured generation via Google AI API |
| **Embeddings** | `BAAI/bge-small-en-v1.5` | Converts legal text chunks into searchable vectors |
| **Frontend** | `Streamlit` | Rapid UI iteration with custom Notion-style CSS |

**The Pipeline Flow:**
`Query → PII Strip → Classify → Route → Retrieve + ABS Check → Confidence Gate (Abstain/Generate) → Generate Answer + Citations`

---

## 🚀 Quickstart (Local Development)

We designed the development environment to be beginner-friendly. **No Docker is required.** Everything runs in a standard Python virtual environment.

### 1. Setup the Environment
```bash
# Clone the repository
git clone https://github.com/HemantKumar822/ip-sakti-sahayak.git
cd ip-sakti-sahayak

# Create and activate a Python virtual environment
python -m venv .venv

# Activate on Mac/Linux:
source .venv/bin/activate
# Activate on Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Secrets
```bash
# Copy the template config
cp .env.example .env
```
Open `.env` and add your `GEMINI_API_KEY`. (Get one for free at Google AI Studio).

### 3. Run the System
You need two terminal windows (both with the `.venv` activated):

**Terminal 1 (Backend API):**
```bash
bash run_api.sh
# Windows: run_api.bat
```
*API runs on `http://localhost:8000`*

**Terminal 2 (Frontend UI):**
```bash
bash run_frontend.sh
# Windows: run_frontend.bat
```
*UI runs on `http://localhost:8501`*

---

## 🗺️ Project Structure & Execution

We have decomposed the project into **6 Epics** and **35 modular GitHub Issues**. Every issue has clear acceptance criteria and is ready to be picked up by the team.

1. **Epic 0: Dev Setup & CI/CD** (Issues #19-23) — Local environments, GitHub Actions, code linting.
2. **Epic 1: Legal Corpus** (Issues #1-6, 32-33) — Downloading laws (India Code, IP India), manifest validation, PDF chunking, ChromaDB ingestion.
3. **Epic 2: Query Pipeline** (Issues #7-11, 34) — FastAPI skeleton, category classification, ABS checker, confidence gate.
4. **Epic 3: Answer & Privacy** (Issues #12-14) — Citation-grounded answer generation, PII stripping.
5. **Epic 4: Demo Readiness** (Issues #15-18, 35) — Streamlit integration, golden test set QA, compliance audit.
6. **Epic 5: UX/UI (Notion Design)** (Issues #24-31) — Custom CSS variables, clean input fields, response cards, accordion citations.

### GitHub Workflow
- `main` branch is protected.
- All development happens in feature branches: `feature/<issue-number>-<short-name>`.
- Open a Pull Request (PR) to `develop`.
- CI/CD will automatically run linting (`ruff`, `black`) and tests (`pytest`).
- Merge after 1 approval.

---

## 👥 The Team

Built for SIH 2026. Designed for impact.

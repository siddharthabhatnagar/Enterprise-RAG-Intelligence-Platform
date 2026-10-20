# Enterprise RAG Intelligence Platform

An enterprise-grade **Retrieval-Augmented Generation (RAG)** system designed to provide internal employees with reliable, strictly grounded answers from large collections of PDF documents, backed by **pure LangChain**, **FastAPI**, **Groq LLM (`openai/gpt-oss-120b`)**, **NVIDIA Embeddings**, **FAISS Vector Search**, **Two-Stage Reranking**, **Document-Level Access Controls (RBAC)**, and **Hallucination Guardrails**.

---

## 1. Problem & Solution Overview

### The Problem
Employees across departments (Engineering, HR, Finance, Legal, Operations) struggle to locate accurate policies, specifications, and financial reports buried across hundreds of internal PDFs. Existing search solutions either produce hallucinated answers or leak confidential departmental documents (e.g., non-executives seeing restricted executive compensation or unreleased board reports).

### The Solution
This platform solves these challenges through:
1. **Document-Level Access Controls (RBAC)**: Enforces security boundaries at retrieval time. A user only retrieves chunks matching their maximum clearance level and department. Unauthorized chunks are physically excluded before reaching the LLM.
2. **Page-Preserving PDF Ingestion**: Extracts text page-by-page with PyMuPDF, attaching strict document provenance (`document_id`, `page_number`, `department`, `access_level`) to every vector chunk.
3. **High-Performance NVIDIA Embeddings**: Generates dense semantic representations via NVIDIA NIM (`nvidia/nv-embedqa-e5-v5`) with an automatic on-device fallback (`fastembed BGE-small`) for zero-configuration local runs.
4. **FAISS Vector Search**: High-speed, persistent vector indexing and cosine distance search.
5. **Two-Stage Reranking**: A cross-encoder rescoring engine combining semantic cross-attention and lexical BM25 token density to elevate top-signal chunks and filter out low-confidence noise.
6. **Strict LangChain LCEL & Groq (`openai/gpt-oss-120b`)**: Executes a pure LangChain Expression Language chain (`prompt | llm | parser`) with zero LangGraph/CrewAI framework overhead.
7. **Structured Citations & Hallucination Guardrails**: Generates inline document citations and verifies answer claims against source chunks, scoring grounding confidence from 0% to 100%.

---

## 2. Architecture & Data Flow

```
                      [ User Natural Language Question ]
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │  FastAPI Gateway & Identity Resolution (RBAC)    │
             │  (Extracts user role, clearance, and department) │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │            FAISS Vector Database                 │
             │       Similarity Search (Over-fetch k=25)        │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       Document-Level Access Control (RBAC)       │
             │  (Drops chunks if clearance > user_max_clearance │
             │   or if department does not match permissions)   │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │        Stage-2 Cross-Attention Reranker          │
             │  (Combines dense similarity + BM25 keyword score │
             │   + phrase match bonus -> Top 4 chunks)          │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │         LangChain LCEL Pipeline                  │
             │ ChatPromptTemplate | ChatGroq (gpt-oss-120b)     │
             │            | StrOutputParser()                   │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │        Hallucination & Faithfulness Guardrail    │
             │  (Entity extraction, context claim verification, │
             │   grounding score gauge & citation synthesis)    │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             [ Answer + Citations + Latency + Grounding Score ]
```

---

## 3. Role-Based Access Control (RBAC) Matrix

Clearance Hierarchy: `PUBLIC` < `INTERNAL` < `CONFIDENTIAL` < `RESTRICTED`

| Role | Active Persona | Clearance | Allowed Access |
| :--- | :--- | :--- | :--- |
| **Contractor** | David Miller | `PUBLIC` | Public Company Policies only |
| **Software Engineer** | Chloe Zhang | `INTERNAL` | Public Policies, Engineering Specs |
| **Engineering Lead** | Alex Rivera | `CONFIDENTIAL` | Public, Internal, Confidential Eng Specs |
| **Finance Controller**| Raj Patel | `CONFIDENTIAL` | Public, Internal, Confidential Financial Audits |
| **HR Director** | Sarah Jenkins | `CONFIDENTIAL` | Public, Internal, Confidential HR Policies |
| **Executive (CEO)** | Marcus Sterling | `RESTRICTED` | All Departments, All Clearance Levels |
| **Admin (IT/Sec)** | Elena Vance | `RESTRICTED` | Full Superuser Access to All Data |

---

## 4. Codebase Directory Structure

```
RAGUsingLangchain/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_ingest.py        # PDF upload & batch parsing
│   │   │   ├── routes_query.py         # Query endpoint with RBAC & RAG pipeline
│   │   │   ├── routes_documents.py     # Document listing, chunk viewer, delete
│   │   │   ├── routes_users.py         # Demo user profiles & clearance definitions
│   │   │   └── routes_analytics.py     # System metrics & model provider status
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic BaseSettings & environment configs
│   │   │   ├── security.py             # RBAC clearance logic & access validator
│   │   │   └── logger.py               # Structured application logger
│   │   ├── services/
│   │   │   ├── pdf_loader.py           # PyMuPDF page-by-page text extractor
│   │   │   ├── chunker.py              # Recursive chunking preserving page metadata
│   │   │   ├── embeddings.py           # NVIDIA NIM Embeddings + FastEmbed fallback
│   │   │   ├── vector_store.py         # FAISS vector store with persistent index
│   │   │   ├── reranker.py             # Semantic + Lexical Cross-Attention Reranker
│   │   │   ├── rag_chain.py            # Pure LangChain LCEL chain with ChatGroq
│   │   │   └── hallucination.py        # Faithfulness check & grounding score
│   │   ├── schemas/
│   │   │   ├── document.py             # Pydantic models for docs, chunks, metadata
│   │   │   ├── query.py                # Request, response, citations, latency models
│   │   │   └── user.py                 # User & role schemas
│   │   └── main.py                     # FastAPI application & static mount
│   └── data/
│       ├── uploads/                    # Physical uploaded PDF documents
│       └── vector_index/               # Persistent FAISS index and registry JSON
├── frontend/
│   ├── index.html                      # Single Page Application (SPA)
│   ├── css/
│   │   └── style.css                   # Modern dark-slate corporate UI styling
│   └── js/
│       ├── api.js                      # REST API client
│       └── app.js                      # UI logic, state management, citation viewer
├── sample_docs/                        # Built-in enterprise sample PDFs
│   ├── Employee_Handbook_General_Policy.pdf
│   ├── Engineering_Cloud_Infrastructure.pdf
│   ├── Q3_Confidential_Financial_Audit.pdf
│   └── HR_Executive_Compensation_2026.pdf
├── scripts/
│   ├── generate_sample_docs.py         # Generates multi-page enterprise PDFs
│   └── seed_database.py               # Ingests and indexes sample PDFs in FAISS
├── .env.example                        # Template for API keys & settings
├── Dockerfile                          # Production container image definition
├── render.yaml                         # 1-Click Render Blueprint configuration
├── vercel.json                         # Vercel deployment configuration
├── requirements.txt                    # Python dependencies
└── README.md                           # Documentation
```

---

## 5. Quick Start (Local Setup)

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### 1. Clone & Install Dependencies
```bash
git clone <your-repo-url>
cd RAGUsingLangchain

# Create and activate virtual environment (optional but recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
```env
# Groq API Key (https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# NVIDIA API Key (https://build.nvidia.com/)
NVIDIA_API_KEY=nvapi-your_nvidia_api_key_here
NVIDIA_EMBED_MODEL=nvidia/nv-embedqa-e5-v5
```

> **Zero-Key Demo Mode**: If you leave the keys empty, the system automatically runs in local demonstration mode using FastEmbed (`BAAI/bge-small-en-v1.5`) and grounded fallback synthesis. All RBAC filtering, FAISS indexing, reranking, and citation badges operate fully!

### 3. Generate Sample Documents & Seed FAISS
```bash
# Generate 4 enterprise PDFs across departments
python scripts/generate_sample_docs.py

# Ingest and index them into the persistent FAISS vector store
python scripts/seed_database.py
```

### 4. Start the Application
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at:
```
http://localhost:8000
```
Interactive API docs are available at:
```
http://localhost:8000/docs
```

---

## 6. Testing the RBAC Capabilities Live in the UI

1. Open `http://localhost:8000`.
2. Look at the **Clearance Identity** dropdown in the top header.
3. Switch identity to **David Miller (External Contractor)**:
   - Try the prompt: *"What is the CEO base salary and executive incentive pool?"*
   - Notice that the system returns **Access Restriction**: the executive document is restricted and was filtered out at retrieval!
   - Now try: *"What is our annual vacation leave and hybrid remote work policy?"*
   - Returns the exact vacation policy with citations from `Employee_Handbook_General_Policy.pdf`.
4. Switch identity to **Elena Vance (Admin / C-Level)**:
   - Ask the same question about executive compensation.
   - Now the platform retrieves `HR_Executive_Compensation_2026.pdf` (Page 1), shows the exact salaries, and displays the citations!
5. Toggle the **Retrieval & Reranker Inspector** drawer at the bottom of the answer to see the raw candidate chunks, original vector ranks, and reranked scores.

---

## 7. Deployment Guide

### Architecture Reality: Vercel vs Render for RAG
- **Why Render (or Railway / Docker) is ideal for the backend**:
  A production RAG platform utilizes vector search libraries (`faiss-cpu`) and persistent disk indexes (`backend/data/vector_index`). Vercel Serverless functions have a 50MB uncompressed limit on the free tier and a **read-only ephemeral filesystem** (where local vector index files and uploaded PDFs are discarded between requests).
- Therefore, we provide two deployment options:
  - **Option A (Recommended)**: Full-Stack on **Render** (zero hassle, persistent storage, 1-click blueprint).
  - **Option B (Decoupled)**: Frontend on **Vercel** + Backend on **Render**.
  - **Option C (Serverless Vercel)**: Serverless configuration using `vercel.json` with external vector storage / in-memory index.

---

### Option A: Deploy Full-Stack on Render (Recommended)

1. Push your repository to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** ➔ **Blueprint**.
3. Select your GitHub repository.
4. Render will read `render.yaml` automatically and configure:
   - Build Command: `pip install -r requirements.txt && python scripts/generate_sample_docs.py && python scripts/seed_database.py`
   - Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
5. In the Render Dashboard, add your environment variables:
   - `GROQ_API_KEY`: Your Groq key
   - `NVIDIA_API_KEY`: Your NVIDIA key
6. Click **Apply**. Your app is live at `https://your-app-name.onrender.com`!

---

### Option B: Deploy Frontend on Vercel + Backend on Render

1. **Deploy Backend to Render** following Option A.
2. Note your Render backend URL (e.g., `https://api-enterprise-rag.onrender.com`).
3. In `frontend/js/api.js`, update `API_BASE` (or set an environment variable) to point to your Render backend:
   ```javascript
   const API_BASE = window.location.hostname === "localhost" 
     ? "http://localhost:8000" 
     : "https://your-backend.onrender.com";
   ```
4. **Deploy Frontend to Vercel**:
   - Go to [Vercel](https://vercel.com/) and click **Add New** ➔ **Project**.
   - Import your repository.
   - Root Directory: `.`
   - Output Directory: `frontend`
   - Click **Deploy**.
   - Your frontend is instantly live on Vercel's edge network, calling your Render backend.

---

### Option C: Deploy Directly to Vercel via CLI

This repository includes `vercel.json` and `api/index.py` configured for Vercel Serverless:

```bash
# Install Vercel CLI
npm install -g vercel

# Log in and deploy
vercel
```

Add your environment variables in the Vercel Project Settings:
- `GROQ_API_KEY`
- `NVIDIA_API_KEY`
- `GROQ_MODEL`: `openai/gpt-oss-120b`

---

## 8. API Reference

### 1. Ingestion (`POST /api/ingest/upload`)
Uploads and indexes an internal PDF.
- **Request**: Multipart Form Data
  - `file`: PDF file
  - `department`: `general` | `engineering` | `finance` | `hr` | `legal` | `executive`
  - `access_level`: `public` | `internal` | `confidential` | `restricted`
  - `category`: String tag
- **Response**:
  ```json
  {
    "success": true,
    "document_id": "4a59eafcdbab",
    "filename": "Q3_Report.pdf",
    "total_pages": 4,
    "total_chunks": 8,
    "message": "Successfully ingested and indexed 'Q3_Report.pdf' into FAISS."
  }
  ```

### 2. Query (`POST /api/query`)
Submits a natural language query with active identity clearance.
- **Request**:
  ```json
  {
    "query": "What is our Q3 EBITDA margin?",
    "user_id": "admin",
    "department_filter": "finance",
    "include_debug_chunks": true
  }
  ```
- **Response**:
  ```json
  {
    "query": "What is our Q3 EBITDA margin?",
    "answer": "According to the financial audit report, the Adjusted EBITDA for Q3 was $12,740,000, yielding an EBITDA margin of 26.4% [Doc: Q3_Confidential_Financial_Audit.pdf, Page: 1].",
    "citations": [
      {
        "document_name": "Q3_Confidential_Financial_Audit.pdf",
        "page_number": 1,
        "department": "finance",
        "access_level": "confidential",
        "relevance_score": 0.94,
        "excerpt": "Adjusted EBITDA for the quarter was $12,740,000, yielding a strong EBITDA margin of 26.4%...",
        "chunk_id": "b0ac62d61fd4_p1_c1"
      }
    ],
    "latency": {
      "retrieval_ms": 32.4,
      "rerank_ms": 1.2,
      "llm_generation_ms": 480.5,
      "total_ms": 514.1
    },
    "grounding": {
      "score": 96.5,
      "verdict": "HIGH",
      "hallucination_risk": "Minimal",
      "reasoning": "Strong context grounding: 96.5% of factual claims & entities verified directly in source context."
    }
  }
  ```

### 3. List Documents (`GET /api/documents`)
Returns all indexed enterprise documents with page and chunk counts.

### 4. Inspect Chunks (`GET /api/documents/{document_id}/chunks`)
Returns all indexed chunks and page numbers for a document.

### 5. Delete Document (`DELETE /api/documents/{document_id}`)
Removes a document from the registry and rebuilds the FAISS index.

### 6. Analytics (`GET /api/analytics/stats`)
Returns total documents, chunks, department breakdowns, and active model providers.

---

## 9. Technology Stack

- **Framework**: FastAPI (Python 3.12)
- **RAG Orchestration**: LangChain (Pure LCEL, No LangGraph, No CrewAI)
- **LLM**: Groq API (`openai/gpt-oss-120b` with fallback to `llama-3.3-70b-versatile`)
- **Embeddings**: NVIDIA NIM (`nvidia/nv-embedqa-e5-v5` / FastEmbed fallback)
- **Vector Search**: FAISS (Facebook AI Similarity Search) CPU
- **PDF Extraction**: PyMuPDF (`fitz`)
- **Reranker**: Two-Stage Semantic Cross-Attention + Lexical BM25 Scoring
- **Guardrails**: Entity Grounding & Citation Verification
- **Frontend**: Responsive Enterprise HTML5, Modern CSS Glassmorphic Dashboard, Vanilla JavaScript SPA

<div align="center">

<br/>

# Agentic RAG for Enterprise Compliance

<p>A multi-agent compliance auditing engine — replacing single-pass RAG with a cyclical<br/>graph state machine that verifies its own outputs before writing a single audit line.</p>

<br/>

![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6F61?style=for-the-badge&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?style=for-the-badge&logo=qdrant&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<br/>

> **Multi-Agent RAG · Hybrid Vector Search · Deterministic Audit Ledger** &nbsp;|&nbsp; Self-correcting · Citation-verified · Fully containerised

<br/>

---

</div>

## Why This Exists

Standard RAG fails in legal and compliance contexts. It hallucinates in the middle of long documents, chunks text without respecting clause boundaries, and has no mechanism to cross-examine what it just retrieved against what it actually cited.

The result: audits that look confident and are silently wrong.

Aegis Core approaches this differently. Instead of a single prompt-and-return pipeline, it runs a **cyclical multi-agent graph** where a Planner maps the document, an Auditor identifies violations with direct clause citations, and a Critic rejects the output and triggers a retry loop if the citations don't hold. Nothing reaches the audit ledger unless it passes verification.

<br/>

---

## Key Numbers

<br/>

<div align="center">

| Cyclical Graph | Hybrid Search | Dual-Agent Critic | Fully Containerised |
|:---:|:---:|:---:|:---:|
| Eliminates single-pass hallucinations | Dense + sparse retrieval combined | Rejects unverified outputs before logging | Docker Compose — zero infra dependency |

</div>

<br/>

---

## How It Works

<br/>

```
Contract Document + Policy Standard
              │
              ▼
  Recursive Clause Chunking
  (15–20% token overlap — preserves clause boundaries)
              │
              ▼
  Qdrant Hybrid Retrieval
  (Dense semantic + sparse keyword matching)
              │
              ▼
  Planner Agent
  (Structural analysis — maps document against policy)
              │
              ▼
  Auditor Agent
  (Violation detection — every finding tied to a clause citation)
              │
              ▼
  ┌─────────────────────────────────────┐
  │   QA Critic: Citation valid?        │
  │   Compliance check passed?          │
  └─────────────────────────────────────┘
         │                    │
      [Fail]               [Pass]
         │                    │
         ▼                    ▼
  Refinement Loop      Audit Ledger Output
  (Retry with          (Structured report +
   corrected context)   line-item citations)
```

<br/>

---

## Technical Decisions

<br/>

| Layer | Choice | Rationale |
|---|---|---|
| Agent Orchestration | LangGraph | Cyclic loops, state persistence, conditional routing — impossible with basic DAGs |
| Vector Engine | Qdrant (Dockerised) | Native hybrid search: dense embeddings + exact clause keyword matching |
| Chunking Strategy | Recursive Text Splitter | 15–20% overlap window preserves paragraph context across clause boundaries |
| Quality Gate | Auditor-Critic Loop | No output passes without citation validation — eliminates blind pass-throughs |
| Backend | FastAPI + Uvicorn | Async execution built for enterprise REST endpoints and streaming agent logs |
| Frontend | Streamlit | Interactive graph visualiser + rapid legal context review |

<br/>

---

## Business Framing

<br/>

> **What's the operational problem?**
>
> Manual compliance reviews are slow, expensive, and inconsistent. Legal teams spend hours cross-referencing contracts against policy standards — work that creates bottlenecks, delays contract sign-offs, and introduces human oversight risk at scale.

<br/>

> **What does better look like?**
>
> An automated pipeline that reads a contract, maps it against a policy standard, identifies violations with direct clause citations, validates its own findings, and produces a reproducible audit ledger — without a human in the loop until the output is already verified.

<br/>

> **Is this deployable?**
>
> Yes. Fully containerised via Docker Compose — `FastAPI` + `Qdrant` + `Streamlit` as independent services. Deploys to AWS ECS, GCP Cloud Run, or on-premise infrastructure with a single command.

<br/>

---

## Tech Stack

<br/>

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6F61?style=flat-square)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?style=flat-square&logo=qdrant&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white)

</div>

<br/>

---

## Repository Structure

```
aegis-compliance-rag/
├── src/
│   ├── database/          # Qdrant initialisation and vector indexing
│   ├── utils/             # PDF reporting and document parsers
│   └── main.py            # FastAPI entrypoint and route handlers
├── app.py                 # Streamlit interactive UI + graph visualiser
├── test_pipeline.py       # Integration tests for graph state machine
├── test_planner.py        # Unit tests for planner agent reasoning
├── test_db.py             # Vector database retrieval benchmarks
├── docker-compose.yml     # Local Qdrant container configuration
└── requirements.txt       # Production dependencies
```

<br/>

---

## About

<br/>

<div align="center">

Built by **Syam Preetham** — aspiring PM/BA with a focus on AI products and data-backed decision making.

*Most RAG systems are built to sound right. This one is built to be verifiable.*

<br/>

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](your-linkedin-url)
[![Portfolio](https://img.shields.io/badge/Portfolio-000000?style=for-the-badge&logo=notion&logoColor=white)](your-portfolio-url)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](your-github-url)

<br/>

</div>

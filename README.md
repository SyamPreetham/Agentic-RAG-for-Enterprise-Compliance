🛡️ Product Requirements Document (PRD)
Project Name: Aegis
Subtitle: Multi-Agent Compliance Audit & Risk Assessment Engine
Author: S Syam Preetham
Role: Lead AI Engineer & Product Owner
Target Architecture: Production-Grade Agentic RAG
1. Executive Summary & Problem Statement
The Problem
Modern enterprises handle thousands of complex vendor agreements, employment contracts, and privacy policies. Concurrently, regulatory frameworks (e.g., financial directives, data privacy mandates) shift rapidly.
Standard RAG (Retrieval-Augmented Generation) architectures fail at legal compliance auditing because they rely on simple, flat keyword or vector similarity. They treat isolated text fragments out of context, leading to critical hallucinations, overlooked legal contradictions, and high financial/regulatory risks.
The Solution
Aegis is an automated, production-grade enterprise risk manager. By utilizing a cognitive state loop (Agentic RAG) rather than a linear pipeline, Aegis orchestrates a multi-agent system to ingest complex legal PDFs, break down auditing requirements into programmatic sub-tasks, cross-examine data partitions with precise payload filtering, and run strict semantic verification checks to eliminate hallucinations entirely.
2. Core Personas & User Stories
Persona A: The Compliance Officer (Startup / SME)
Need: Lacks the budget for an extensive human legal team but must verify that incoming vendor SaaS agreements do not breach native country compliance regulations.
Persona B: The Enterprise Legal Auditor (MNC / Fintech)
Need: Must rapidly audit ten thousand legacy internal data retention clauses against an updated 2026 data compliance mandate without reading every page manually.
User Stories
As a Compliance Officer, I want to upload a new vendor contract PDF and select a specific regulatory framework so that I can automatically receive a structured risk score and gap analysis report.
As a Legal Auditor, I want the system to flag the exact page and paragraph numbers where a contract clause explicitly contradicts a regulatory mandate so that I can audit with verifiable evidence.
3. System Architecture & Component Mapping
To ensure deterministic behavior, high performance, and rapid testing cycles on Apple Silicon (M1 hardware), the system uses a decoupled, asynchronous micro-architecture.
Component
Technology
Functional Justification
API Layer
FastAPI
Native asynchronous (async/await) execution handling long-running multi-agent reasoning loops without blocking concurrent web traffic.
Agent Orchestration
LangGraph
Models the multi-agent system as a strict state machine. Allows explicit, deterministic routing loops (e.g., routing back to retrieval if verification fails).
Vector Space
Qdrant
Enterprise-grade vector database supporting advanced Payload Filtering to restrict vector searches dynamically by jurisdiction, date, or document type.
Local Inference
Ollama
Runs quantized local weights (llama3.2:3b / qwen2.5:3b) using Metal acceleration on Apple M1 for local development and zero-cost graph testing.
Production Inference
External Cloud (Groq / OpenAI)
Configured via structural environment variables for ultra-low latency, high-reasoning execution in production environments.

4. The Cognitive Agent State Workflow
Instead of a standard stream, Aegis executes inside an explicit directed graph containing the following key operational nodes:
[ User Input ] ---> ( Node 1: Deconstruction & Planning Agent )
                                  |
                                  v
                    ( Node 2: Router & Vector Retrieval )
                                  |
                                  v
                    ( Node 3: Legal Auditor Agent )
                                  |
                                  v
              +---> ( Node 4: Hallucination & Citation Critic )
              |                   |
    [IF FAILS | Re-Route]         +---> [Passes Verification?]
              |                                 |
              +---------------------------------+---> [Generates Final JSON Audit]

Deconstruction & Planning Agent: Parses the user's compliance query into specific, discrete sub-queries.
Router & Storage Engine: Targets exact document payloads in Qdrant based on metadata attributes.
Legal Auditor Agent: Evaluates retrieved contexts side-by-side to generate a structured discrepancy draft.
Hallucination & Citation Critic: Executes a defensive semantic verification pass. If a statement lacks an explicit source document tag or page citation, the graph forces a state rollback to Node 2 for deeper context retrieval.
5. Success Metrics (KPIs)
Zero Hallucination Tolerance: 100% of generated risk assessments must explicitly map to a valid source metadata hash from the vector DB.
Production Readiness: 100% dockerized orchestration via single-command deployments (docker-compose up --build).
Developer Agility: The complete local environment must execute locally within a sub-10GB RAM memory footprint using hybrid execution schemes.
Now that the Product Requirements Document is locked and loaded, we are ready to build the literal bones of this application.




## 🏗️ Technical Architecture & M1 Optimization Logs

This section tracks the explicit, production-grade engineering choices implemented to guarantee a low-memory footprint on a constrained hardware environment (Apple Silicon M1, 8GB RAM) without sacrificing enterprise accuracy.

### 💾 1. Database & Container Resource Optimization

The database layer is orchestrated via `docker-compose.yml` with strict, non-default infrastructure bounds to prevent system thermal throttling and memory starvation:

*   **Hard Container Limits (`memory: 1024M`):** Restricts the Docker virtualization engine from allocating more than 1GB of system RAM to the database container, guaranteeing the remaining 7GB is left entirely open for the macOS operating system, local code testing, and inference pipelines.
*   **Thread Restriction (`MAX_SEARCH_THREADS: 1`):** Limits internal database query workers to a single execution thread. This prevents the database from multi-threading across all CPU cores simultaneously, avoiding major thermal spikes and performance throttling on fanless MacBook Air architectures.

---

### 🧠 2. Vector Index & Quantization Breakdown

Inside `src/database/qdrant_client.py`, the index landscape is built using a compressed schema architecture rather than standard high-dimension defaults:

#### A. Vector Sizing (`size=384`)
*   **What was done:** Designed the collection schema to accept exactly 384-dimensional dense vectors (mapping directly to lightweight, local embedding pipelines like `all-MiniLM-L6-v2`).
*   **The Engineering Why:** While legacy enterprise models push 1536- or 4096-dimensional arrays, processing those matrices locally on an 8GB machine causes massive CPU latency. A 384-dimensional architecture provides highly granular semantic compliance maps at a fraction of the computational and memory footprint.

#### B. Index Memory Bypass (`on_disk=True`)
*   **What was done:** Forced Qdrant's structural HNSW lookup graphs to write and read directly from SSD storage volumes instead of caching in system memory.
*   **The Engineering Why:** By default, vector databases attempt to anchor indices entirely in RAM to optimize speed. On an 8GB RAM footprint, processing multi-page legal PDFs would cause immediate system crashes. Forcing the index map to stay on disk entirely protects runtime memory.

#### C. Compression Matrix (`ScalarType.INT8` & `always_ram=False`)
*   **What was done:** Applied `INT8` Scalar Quantization, compressing large 32-bit floating-point numbers down to dense 8-bit integers, while forcing the quantization metadata tables to stay off the system RAM.
*   **The Engineering Why:** This optimization layout decreases the database vector footprint by **nearly 75%**. The system bypasses memory bloating entirely by streaming compressed integer maps dynamically into active memory only at the exact millisecond a search query executes.
### 🚀 5. Local Inference Architecture Validation Log
*   **Milestone Reached:** Successfully validated the **Deconstruction & Planning Agent** (`src/agents/nodes/planner.py`) running against quantized local model weights (`llama3.2:3b`).
*   **Performance Metrics:** Handled local zero-temperature structured extraction loops with zero latency or syntax leakage.
*   **Outputs Generated:** Raw audit prompts are cleanly split into contextualized search strings containing precise jurisdictional and temporal metadata hooks ready for Qdrant storage filtering.

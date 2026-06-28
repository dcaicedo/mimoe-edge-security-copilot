# mimOE Edge Security Copilot

> **An Agentic AI demonstration built with Python, Clean Architecture, Retrieval-Augmented Generation (RAG), and mimOE.**

## Overview

mimOE Edge Security Copilot is a local-first AI application that demonstrates how an intelligent Security Agent orchestrates multiple AI capabilities to analyze physical security events and generate structured anomaly reports using **mimOE**.

The solution uses:

- Local embeddings (`nomic-embed-text`)
- Local LLM (`SmolLM2`)
- OpenAI-compatible APIs exposed by mimOE
- Clean Architecture
- Test-Driven Development (TDD)
- Retrieval-Augmented Generation (RAG)

The current implementation simulates security systems using local JSON files. The architecture is intentionally designed so these data sources can later be replaced by distributed **mim** services without changing the application layer.

---

# Project Goals

The project demonstrates how an AI Agent can:

- Aggregate heterogeneous security events
- Retrieve relevant evidence through semantic search
- Correlate events across different systems
- Produce executive-ready anomaly reports
- Execute entirely on-device using mimOE

---

# Solution Workflow

1. Load physical security events.
2. Generate embeddings for all documents.
3. Perform semantic retrieval using cosine similarity.
4. Select the Top-K most relevant documents.
5. Build contextual prompts.
6. Generate a structured report using SmolLM2.

---

# Edge AI Architecture with mimOE

```text
                        Guard
                          │
                          ▼
                  Security Agent
                          │
                  GenerateSecurityReport
                          │
      ┌───────────────────┼───────────────────┐
      ▼                   ▼                   ▼
 File Repository   Semantic Retriever   Prompt Builder
      │                   │
      │                   ▼
      │          MimoeEmbeddingClient
      │            POST /v1/embeddings
      │
      └───────────────────┬───────────────────┘
                          ▼
                  MimoeLLMClient
             POST /v1/chat/completions
                          │
                          ▼
                       SmolLM2
                          │
                          ▼
              Structured Security Report
```

---

# Agentic AI Evolution

Current implementation:

```text
Security Agent
 ├── File Repository
 ├── Embedding Model
 └── SmolLM2
```

Future architecture:

```text
Security Agent
      │
 ┌────┼──────────────┐
 ▼    ▼              ▼
Vision Mim    Access Log Mim    Alarm Mim
      │
      ▼
Embedding Mim
      │
      ▼
SmolLM2
      │
      ▼
Security Report
```

---

# Data Sources

- access_logs.json
- door_events.json
- camera_observations.json
- alarm_logs.json
- security_policy.txt

---

# Project Structure

```text
src/security_agent/
├── domain/
├── application/
├── infrastructure/
└── main.py

data/
tests/
```

---

# Engineering Highlights

- Clean Architecture
- SOLID Principles
- Dependency Injection
- Repository Pattern
- Protocol-based Interfaces
- Retrieval-Augmented Generation (RAG)
- Semantic Search
- Local AI inference with mimOE
- Fully mocked unit tests
- Infrastructure independent from business logic

---

# Configuration

```env
MIMOE_BASE_URL=http://localhost:8083/mimik-ai/openai/v1
MIMOE_API_KEY=1234
MIMOE_CHAT_MODEL=smollm2-360m
MIMOE_EMBEDDING_MODEL=nomic-embed-text
```

---

# Installation

```bash
git clone https://github.com/dcaicedo/mimoe-edge-security-copilot.git
cd mimoe-edge-security-copilot

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

# Run

```bash
PYTHONPATH=src python -m security_agent.main \
"Generate a security anomaly report for last night."
```

---

# Testing

```bash
pytest
pytest -v
```

The test suite validates:

- Cosine similarity
- Semantic retrieval
- Prompt generation
- Use case orchestration
- Repository layer
- mimOE embedding client
- mimOE chat client

All HTTP calls are mocked, allowing tests to execute without a running LLM server.

---

# Technologies

- Python
- mimOE
- SmolLM2
- nomic-embed-text
- OpenAI-compatible APIs
- pytest
- Clean Architecture
- RAG
- Semantic Search
- Edge AI

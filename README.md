# Security Anomaly Agent

A Python CLI agent that analyzes physical security events and generates structured anomaly reports using a local [mimOE](https://mimik.com) OpenAI-compatible API.

Built with **Clean Architecture** and **TDD** — 61 unit tests, zero real HTTP calls in the test suite.

---

## How it works

```
data/*.json + security_policy.txt
        │
        ▼
FileSecurityDataRepository  ──► List[Document]
        │
        ▼
SemanticRetriever  ◄──  MimoeEmbeddingClient  ──► POST /v1/embeddings
  (cosine similarity)
        │  top-K relevant docs
        ▼
PromptBuilder  ──► [system, user] messages
        │
        ▼
MimoeLLMClient  ──► POST /v1/chat/completions
        │
        ▼
  Structured Report
```

1. Loads security events from JSON files and policy from a text file
2. Embeds each document via the local LLM server
3. Embeds the user query, retrieves the top-K most relevant documents using cosine similarity
4. Builds a structured prompt with evidence, timestamps, and sources
5. Calls the LLM and returns a report with five sections

---

## Report format

```
## Executive Summary
## Uncommon Behaviors
## Risk Level
## Evidence
## Recommended Actions
```

---

## Project structure

```
src/security_agent/
├── domain/
│   ├── ports.py              # Document dataclass
│   └── similarity.py         # cosine_similarity
├── application/
│   ├── ports.py              # EmbeddingClient, LLMClient, SecurityDataRepository,
│   │                         # Retriever, PromptBuilderPort (Protocols)
│   ├── semantic_retriever.py # SemanticRetriever
│   ├── prompt_builder.py     # PromptBuilder
│   ├── generate_report.py    # GenerateSecurityReport (use case)
│   └── main.py               # CLI entry point & composition root
└── infrastructure/
    ├── file_security_repository.py  # reads data/
    ├── mimoe_embedding_client.py    # POST /v1/embeddings
    └── mimoe_llm_client.py          # POST /v1/chat/completions

data/
├── access_logs.json
├── alarm_logs.json
├── camera_observations.json
├── door_events.json
└── security_policy.txt

tests/
├── test_similarity.py
├── test_semantic_retriever.py
├── test_prompt_builder.py
├── test_generate_report.py
├── test_mimoe_embedding_client.py
├── test_mimoe_llm_client.py
└── test_file_security_repository.py
```

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Copy and configure environment variables:

```bash
cp .env.example .env
```

`.env` variables:

| Variable | Description | Default |
|---|---|---|
| `MIMOE_BASE_URL` | Base URL of the local mimOE/Ollama server | `http://localhost:11434` |
| `MIMOE_API_KEY` | API key (leave empty if not required) | _(empty)_ |
| `MIMOE_CHAT_MODEL` | Chat completion model name | `llama3.2` |
| `MIMOE_EMBEDDING_MODEL` | Embedding model name | `nomic-embed-text` |

---

## Run

```bash
PYTHONPATH=src python -m security_agent.main "your query here"
```

Examples:

```bash
PYTHONPATH=src python -m security_agent.main \
  "Were there any after-hours intrusions in the server room?"

PYTHONPATH=src python -m security_agent.main \
  "Correlate all camera and alarm events and identify the most critical threat" \
  --top-k 10

PYTHONPATH=src python -m security_agent.main \
  "Summarize all forced-entry and tailgate events" \
  --top-k 8 --data-dir ./data
```

Options:

```
positional:
  query             Security question or investigation prompt

optional:
  --top-k N         Number of relevant documents to retrieve (default: 5)
  --data-dir PATH   Path to data directory (default: ./data)
```

---

## Tests

```bash
pytest
pytest -v                        # verbose
pytest tests/test_similarity.py  # single file
```

All 61 tests run without a running LLM server — HTTP calls are mocked with `pytest-mock`.

---

## Architecture notes

- **Domain** layer has zero external dependencies — only stdlib
- **Application** layer depends only on domain — defines ports as `Protocol` classes
- **Infrastructure** layer implements ports — all I/O lives here
- **Dependency injection** throughout — `GenerateSecurityReport` receives all collaborators as constructor arguments, making it fully testable in isolation
- The URL builder normalizes `MIMOE_BASE_URL` so both `http://host:port` and `http://host:port/path/v1` formats work correctly

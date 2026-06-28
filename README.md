# mimOE Edge Security Copilot

A Python CLI agent that demonstrates local-first Edge AI using mimOE. It reads physical security event logs, finds the most relevant evidence through semantic search, and generates a security analysis — all running on-device without any cloud dependency.

---

## What this project demonstrates

- How to build an AI agent with **Clean Architecture** and **Test-Driven Development**
- How to use **mimOE OpenAI-compatible APIs** for local embeddings and local chat completions
- How **Retrieval-Augmented Generation (RAG)** works end to end: embed documents, embed a query, rank by cosine similarity, pass top results to the LLM
- How to keep the **infrastructure layer replaceable** — the application core has no dependency on mimOE or on any specific data source

---

## How it works

Security event files (JSON and TXT) simulate data from badge readers, door sensors, cameras, and alarms. At runtime:

1. All documents are loaded from the `data/` directory
2. Each document is embedded using `nomic-embed-text` via the mimOE `/v1/embeddings` API
3. The user's query is also embedded, then compared against all documents using cosine similarity
4. The top-K most relevant documents are selected
5. A structured prompt is built — policy documents and event documents are separated to help the model focus
6. `SmolLM2` generates the analysis via the mimOE `/v1/chat/completions` API

---

## Architecture

The project follows **Clean Architecture**: dependencies only point inward. The mimOE clients, file readers, and CLI are all in the infrastructure layer and can be swapped without touching any application or domain code.

```text
CLI (main.py)
     │
     ▼
GenerateSecurityReport          ← application use case
     │
     ├── FileSecurityDataRepository   ← reads local JSON + TXT files
     │
     ├── SemanticRetriever            ← cosine similarity ranking
     │       └── MimoeEmbeddingClient   → POST /v1/embeddings
     │
     ├── PromptBuilder                ← formats evidence into LLM messages
     │
     └── MimoeLLMClient              → POST /v1/chat/completions
                                              │
                                          SmolLM2
                                              │
                                     Security analysis
```

**Dependency direction:** infrastructure → application → domain. The domain (`Document`, `cosine_similarity`) has no external dependencies.

**Ports and adapters:** `EmbeddingClient`, `LLMClient`, `SecurityDataRepository`, and `Retriever` are Python `Protocol` interfaces defined in the application layer. Infrastructure classes implement them structurally — no inheritance required.

---

## Data sources

The `data/` directory contains simulated physical security events. These files stand in for real security systems; the architecture is designed so they can later be replaced by live mim services without changing the application layer.

| File | Simulates |
|---|---|
| `access_logs.json` | Badge reader events — grants, denials, unrecognized badges |
| `door_events.json` | Door open/close, held-open alarms, forced-entry events |
| `camera_observations.json` | Camera observations with confidence scores |
| `alarm_logs.json` | Triggered alarms with severity and disposition |
| `security_policy.txt` | Access-hour rules, escalation procedures, device policy |

The dataset includes intentional correlated anomalies:
- **02:17–02:47** — three denied badge attempts → tailgate → server room door held 312 s → device connected to rack
- **09:47** — stairwell door forced open, suspect not located
- **23:58** — after-hours entry, same employee in server room 48 seconds later

---

## Setup

```bash
git clone https://github.com/dcaicedo/mimoe-edge-security-copilot.git
cd mimoe-edge-security-copilot

python -m venv .venv
source .venv/bin/activate

pip install -r requirements-dev.txt   # includes pytest and pytest-mock
cp .env.example .env                  # then edit with your mimOE settings
```

Configure `.env`:

```env
MIMOE_BASE_URL=http://localhost:8083/mimik-ai/openai/v1
MIMOE_API_KEY=1234
MIMOE_CHAT_MODEL=smollm2-360m
MIMOE_EMBEDDING_MODEL=nomic-embed-text
```

The base URL is normalized automatically — `/v1` suffix is optional.

---

## Run

```bash
PYTHONPATH=src python -m security_agent.main "your security question"
```

Examples:

```bash
# Investigate a specific incident
PYTHONPATH=src python -m security_agent.main \
  "Were there any after-hours intrusions in the server room?"

# Broad sweep
PYTHONPATH=src python -m security_agent.main \
  "Identify all anomalies and policy violations from last night" \
  --top-k 8
```

| Option | Description | Default |
|---|---|---|
| `query` | Security question (positional) | required |
| `--top-k N` | Documents to retrieve | `5` |
| `--data-dir PATH` | Path to event data | `./data` |

---

## Tests

```bash
pytest        # 59 tests
pytest -v     # verbose
```

All HTTP calls to mimOE are mocked with `pytest-mock`. The full test suite runs without a live server.

| Test file | What it covers |
|---|---|
| `test_similarity.py` | Cosine similarity math |
| `test_semantic_retriever.py` | Embedding and ranking with a mocked client |
| `test_prompt_builder.py` | Message structure, policy/event split, content truncation |
| `test_generate_report.py` | Use case orchestration with all four collaborators mocked |
| `test_mimoe_embedding_client.py` | HTTP contract, auth, timeout, URL normalization |
| `test_mimoe_llm_client.py` | HTTP contract, auth, timeout, URL normalization |
| `test_file_security_repository.py` | File parsing, document formatting, unique IDs |

---

## Design decisions

**Why Clean Architecture?**
The application core (`GenerateSecurityReport`, `SemanticRetriever`, `PromptBuilder`) has no dependency on mimOE, on HTTP, or on the filesystem. Swapping the embedding model, the LLM, or the data source requires only a new infrastructure class — no changes to business logic.

**Why Protocol interfaces?**
Python's `typing.Protocol` enables structural typing: any class that implements the right methods satisfies the interface, without inheriting from a base class. This keeps the domain and application layers free of framework coupling.

**Why mocked unit tests?**
Each layer is tested in isolation. Infrastructure tests mock `requests`. Application tests mock all four collaborators. This makes tests fast, deterministic, and independent of any running service.

**Why separate policy from event documents in the prompt?**
During retrieval, policy documents score high for almost any security query because they contain relevant vocabulary. Separating them into a `POLICY:` block and keeping actual events in an `EVENTS:` block prevents the model from fixating on policy text and ignoring the incidents.

---

## Future evolution with real mims

The current implementation uses local JSON and TXT files to simulate security system data. The embeddings and LLM inference already run on-device through mimOE today.

The next step is to replace the local file repository with real mim services — one per data stream — so the agent pulls live data from distributed edge sources:

```text
Current                          Future
──────────────────────────────────────────────────────────────
Local JSON/TXT files        →    Access Log Mim
(access_logs.json,               Door Event Mim
 door_events.json,               Camera / Vision Mim
 camera_observations.json,       Alarm Mim
 alarm_logs.json)

mimOE embeddings (in use)        mimOE embeddings (unchanged)
mimOE LLM (in use)               mimOE LLM (unchanged)
```

Each future mim would implement the `SecurityDataRepository` protocol already defined in `src/security_agent/application/ports.py`. The application use case, semantic retriever, prompt builder, and LLM client require no changes.

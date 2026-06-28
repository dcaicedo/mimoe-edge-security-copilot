import pytest
from security_agent.domain.ports import Document
from security_agent.application.generate_report import GenerateSecurityReport


FAKE_REPORT = """\
## Executive Summary
Unauthorized tailgate entry into the server room followed by hardware interaction.

## Uncommon Behaviors
- Entry at 02:21 outside approved hours
- Unidentified individual connected a device to the server rack

## Risk Level
CRITICAL — active breach indicators confirmed inside server room.

## Evidence
- [alarm_logs | 2026-06-27T02:21:35Z] Tailgate detected at DOOR-SERVER-01
- [camera_observations | 2026-06-27T02:47:08Z] Device connected to rack

## Recommended Actions
1. Isolate the affected server rack immediately
2. Review access logs for data exfiltration
3. Engage the incident response team
"""

DOCUMENTS = [
    Document(
        id="alm-001",
        content="Tailgate detected at DOOR-SERVER-01.",
        source="alarm_logs",
        timestamp="2026-06-27T02:21:35Z",
    ),
    Document(
        id="cam-004",
        content="Individual connecting device to server rack port.",
        source="camera_observations",
        timestamp="2026-06-27T02:47:08Z",
    ),
    Document(
        id="policy-1",
        content="Server room access outside approved hours is a potential breach.",
        source="security_policy",
        timestamp="",
    ),
]

RELEVANT = [
    {"doc_id": "alm-001", "score": 0.99},
    {"doc_id": "cam-004", "score": 0.94},
]

FAKE_MESSAGES = [
    {"role": "system", "content": "You are a security analyst..."},
    {"role": "user",   "content": "SECURITY EVENT EVIDENCE:\n..."},
]


@pytest.fixture
def mock_repository(mocker):
    repo = mocker.MagicMock()
    repo.load_documents.return_value = DOCUMENTS
    return repo


@pytest.fixture
def mock_retriever(mocker):
    retriever = mocker.MagicMock()
    retriever.find_relevant.return_value = RELEVANT
    return retriever


@pytest.fixture
def mock_prompt_builder(mocker):
    builder = mocker.MagicMock()
    builder.build.return_value = FAKE_MESSAGES
    return builder


@pytest.fixture
def mock_llm_client(mocker):
    client = mocker.MagicMock()
    client.generate.return_value = FAKE_REPORT
    return client


@pytest.fixture
def use_case(mock_repository, mock_retriever, mock_prompt_builder, mock_llm_client):
    return GenerateSecurityReport(
        repository=mock_repository,
        retriever=mock_retriever,
        prompt_builder=mock_prompt_builder,
        llm_client=mock_llm_client,
    )


# ── Step 1: load documents ───────────────────────────────────────────────────

def test_loads_documents_from_repository(use_case, mock_repository):
    use_case.execute(query="server room intrusion", top_k=2)

    mock_repository.load_documents.assert_called_once()


# ── Step 2: index documents in retriever ─────────────────────────────────────

def test_indexes_every_document_in_retriever(use_case, mock_retriever):
    use_case.execute(query="server room intrusion", top_k=2)

    assert mock_retriever.add_document.call_count == len(DOCUMENTS)


def test_indexes_documents_with_id_and_content(use_case, mock_retriever):
    use_case.execute(query="server room intrusion", top_k=2)

    mock_retriever.add_document.assert_any_call("alm-001", "Tailgate detected at DOOR-SERVER-01.")
    mock_retriever.add_document.assert_any_call("cam-004", "Individual connecting device to server rack port.")


# ── Step 3: retrieve top-k ───────────────────────────────────────────────────

def test_retrieves_with_query_and_top_k(use_case, mock_retriever):
    use_case.execute(query="server room intrusion", top_k=2)

    mock_retriever.find_relevant.assert_called_once_with(query="server room intrusion", top_k=2)


# ── Step 4: build prompt ─────────────────────────────────────────────────────

def test_builds_prompt_with_query_and_relevant_documents(use_case, mock_prompt_builder):
    use_case.execute(query="server room intrusion", top_k=2)

    call_args = mock_prompt_builder.build.call_args
    assert call_args.kwargs["query"] == "server room intrusion"

    passed_docs = call_args.kwargs["documents"]
    passed_ids = {doc.id for doc in passed_docs}
    assert passed_ids == {"alm-001", "cam-004"}


def test_prompt_excludes_non_relevant_documents(use_case, mock_prompt_builder):
    use_case.execute(query="server room intrusion", top_k=2)

    passed_docs = mock_prompt_builder.build.call_args.kwargs["documents"]
    passed_ids = {doc.id for doc in passed_docs}
    assert "policy-1" not in passed_ids


# ── Step 5: call LLM and return report ───────────────────────────────────────

def test_sends_built_messages_to_llm(use_case, mock_llm_client):
    use_case.execute(query="server room intrusion", top_k=2)

    mock_llm_client.generate.assert_called_once_with(FAKE_MESSAGES)


def test_returns_llm_response(use_case):
    result = use_case.execute(query="server room intrusion", top_k=2)

    assert result == FAKE_REPORT

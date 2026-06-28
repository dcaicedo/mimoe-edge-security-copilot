import pytest
from security_agent.domain.ports import Document
from security_agent.application.prompt_builder import PromptBuilder


@pytest.fixture
def documents():
    return [
        Document(
            id="alm-001",
            content="Tailgate detected at DOOR-SERVER-01. Unidentified individual followed authorized staff.",
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
            id="policy-server",
            content="Server room access outside approved hours is treated as a potential security breach.",
            source="security_policy",
            timestamp="",
        ),
    ]


# ── Structure ─────────────────────────────────────────────────────────────────

def test_returns_two_messages(documents):
    messages = PromptBuilder().build(query="What happened?", documents=documents)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_returns_two_messages_without_documents():
    messages = PromptBuilder().build(query="Any anomalies?", documents=[])
    assert len(messages) == 2


# ── System message ────────────────────────────────────────────────────────────

def test_system_message_establishes_analyst_role(documents):
    system = PromptBuilder().build(query="any", documents=documents)[0]["content"]
    assert "security analyst" in system.lower()


def test_system_message_is_concise(documents):
    system = PromptBuilder().build(query="any", documents=documents)[0]["content"]
    assert len(system) < 200


# ── User message: evidence ────────────────────────────────────────────────────

def test_user_message_includes_document_content(documents):
    user = PromptBuilder().build(query="any", documents=documents)[1]["content"]
    assert "Tailgate detected at DOOR-SERVER-01" in user
    assert "Individual connecting device to server rack port" in user


def test_user_message_includes_timestamps(documents):
    user = PromptBuilder().build(query="any", documents=documents)[1]["content"]
    assert "2026-06-27T02:21:35Z" in user
    assert "2026-06-27T02:47:08Z" in user


def test_user_message_includes_sources(documents):
    user = PromptBuilder().build(query="any", documents=documents)[1]["content"]
    assert "alarm_logs" in user
    assert "camera_observations" in user
    assert "security_policy" in user


def test_user_message_includes_query(documents):
    query = "Is the server room compromised?"
    user = PromptBuilder().build(query=query, documents=documents)[1]["content"]
    assert query in user


def test_documents_without_timestamp_are_still_included():
    docs = [Document(id="p1", content="Policy text.", source="security_policy", timestamp="")]
    user = PromptBuilder().build(query="any", documents=docs)[1]["content"]
    assert "Policy text." in user
    assert "security_policy" in user


def test_empty_documents_query_in_user_message():
    messages = PromptBuilder().build(query="Any anomalies?", documents=[])
    assert "Any anomalies?" in messages[1]["content"]


def test_content_is_truncated_to_fit_context():
    long_content = "A" * 500
    docs = [Document(id="d1", content=long_content, source="test", timestamp="")]
    user = PromptBuilder().build(query="any", documents=docs)[1]["content"]
    assert long_content not in user
    assert "A" * 120 in user

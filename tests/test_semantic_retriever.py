import pytest
from security_agent.application.semantic_retriever import SemanticRetriever


@pytest.fixture
def mock_embedding_client(mocker):
    client = mocker.MagicMock()
    client.embed.side_effect = lambda text: {
        "brute force login attempt admin":    [1.0, 1.0, 0.0, 0.0],
        "port scan detected on subnet":       [0.0, 0.0, 1.0, 1.0],
        "multiple failed logins for user":    [0.9, 0.8, 0.1, 0.0],
        "suspicious login activity detected": [1.0, 0.9, 0.0, 0.1],
    }[text]
    return client


def test_returns_most_relevant_document(mock_embedding_client):
    retriever = SemanticRetriever(embedding_client=mock_embedding_client)
    retriever.add_document("doc-brute",    "brute force login attempt admin")
    retriever.add_document("doc-portscan", "port scan detected on subnet")

    results = retriever.find_relevant("multiple failed logins for user", top_k=1)

    assert len(results) == 1
    assert results[0]["doc_id"] == "doc-brute"
    assert results[0]["score"] > 0.9


def test_respects_top_k(mock_embedding_client):
    retriever = SemanticRetriever(embedding_client=mock_embedding_client)
    retriever.add_document("doc-brute",    "brute force login attempt admin")
    retriever.add_document("doc-portscan", "port scan detected on subnet")

    results = retriever.find_relevant("multiple failed logins for user", top_k=2)

    assert len(results) == 2
    assert results[0]["score"] >= results[1]["score"]


def test_embedding_client_called_once_per_document(mock_embedding_client):
    retriever = SemanticRetriever(embedding_client=mock_embedding_client)
    retriever.add_document("doc-brute", "brute force login attempt admin")
    retriever.add_document("doc-brute", "brute force login attempt admin")  # same doc twice

    assert mock_embedding_client.embed.call_count == 2


def test_query_is_embedded_at_search_time(mock_embedding_client):
    retriever = SemanticRetriever(embedding_client=mock_embedding_client)
    retriever.add_document("doc-brute", "brute force login attempt admin")

    retriever.find_relevant("suspicious login activity detected", top_k=1)

    mock_embedding_client.embed.assert_called_with("suspicious login activity detected")

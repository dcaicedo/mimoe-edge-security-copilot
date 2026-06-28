import pytest
import requests
from security_agent.infrastructure.mimoe_embedding_client import MimoeEmbeddingClient

BASE_URL = "http://localhost:11434"
MODEL    = "nomic-embed-text"
API_KEY  = "test-secret-key"
VECTOR   = [0.1, 0.2, 0.3, 0.4]


@pytest.fixture
def mock_post(mocker):
    response = mocker.MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "object": "list",
        "data": [{"object": "embedding", "embedding": VECTOR, "index": 0}],
        "model": MODEL,
    }
    return mocker.patch("requests.post", return_value=response)


# ── Core contract ─────────────────────────────────────────────────────────────

def test_returns_embedding_vector(mock_post):
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL)
    assert client.embed("failed login attempt") == VECTOR


def test_posts_to_embeddings_endpoint(mock_post):
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL)
    client.embed("failed login attempt")
    assert mock_post.call_args[0][0] == f"{BASE_URL}/v1/embeddings"


def test_sends_text_and_model_in_body(mock_post):
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL)
    client.embed("failed login attempt")
    payload = mock_post.call_args[1]["json"]
    assert payload["input"] == "failed login attempt"
    assert payload["model"] == MODEL


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_sends_api_key_as_bearer_header(mock_post):
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL, api_key=API_KEY)
    client.embed("failed login attempt")
    headers = mock_post.call_args[1]["headers"]
    assert headers["Authorization"] == f"Bearer {API_KEY}"


def test_omits_auth_header_when_no_api_key(mock_post):
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL, api_key="")
    client.embed("failed login attempt")
    headers = mock_post.call_args[1]["headers"]
    assert "Authorization" not in headers


# ── Timeout ───────────────────────────────────────────────────────────────────

def test_passes_timeout_to_request(mock_post):
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL, timeout=15)
    client.embed("failed login attempt")
    assert mock_post.call_args[1]["timeout"] == 15


def test_raises_on_timeout(mocker):
    mocker.patch("requests.post", side_effect=requests.exceptions.Timeout)
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL)
    with pytest.raises(RuntimeError, match="timed out"):
        client.embed("failed login attempt")


# ── Error handling ────────────────────────────────────────────────────────────

def test_raises_on_http_error(mocker):
    response = mocker.MagicMock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mocker.patch("requests.post", return_value=response)
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL)
    with pytest.raises(requests.exceptions.HTTPError, match="500 Server Error"):
        client.embed("failed login attempt")


def test_raises_on_connection_error(mocker):
    mocker.patch("requests.post", side_effect=requests.exceptions.ConnectionError)
    client = MimoeEmbeddingClient(base_url=BASE_URL, model=MODEL)
    with pytest.raises(RuntimeError, match="Could not connect"):
        client.embed("failed login attempt")


# ── Environment variables ─────────────────────────────────────────────────────

def test_reads_base_url_from_env(mocker, mock_post):
    mocker.patch.dict("os.environ", {"MIMOE_BASE_URL": "http://custom-host:8080"})
    client = MimoeEmbeddingClient()
    client.embed("test")
    assert mock_post.call_args[0][0] == "http://custom-host:8080/v1/embeddings"


def test_reads_model_from_env(mocker, mock_post):
    mocker.patch.dict("os.environ", {"MIMOE_EMBEDDING_MODEL": "mxbai-embed-large"})
    client = MimoeEmbeddingClient()
    client.embed("test")
    assert mock_post.call_args[1]["json"]["model"] == "mxbai-embed-large"


def test_reads_api_key_from_env(mocker, mock_post):
    mocker.patch.dict("os.environ", {"MIMOE_API_KEY": "env-secret"})
    client = MimoeEmbeddingClient()
    client.embed("test")
    assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer env-secret"


def test_normalizes_base_url_that_already_contains_v1(mock_post):
    client = MimoeEmbeddingClient(base_url="http://localhost:8083/mimik-ai/openai/v1", model=MODEL)
    client.embed("test")
    assert mock_post.call_args[0][0] == "http://localhost:8083/mimik-ai/openai/v1/embeddings"

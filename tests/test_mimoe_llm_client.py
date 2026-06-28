import pytest
import requests
from security_agent.infrastructure.mimoe_llm_client import MimoeLLMClient

BASE_URL = "http://localhost:11434"
MODEL    = "llama3.2"
API_KEY  = "test-secret-key"
MESSAGES = [
    {"role": "system", "content": "You are a security analyst."},
    {"role": "user",   "content": "What happened at 02:21?"},
]
REPLY = "A tailgate was detected at the server room door."


@pytest.fixture
def mock_post(mocker):
    response = mocker.MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "id": "chatcmpl-001",
        "object": "chat.completion",
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": REPLY},
                "finish_reason": "stop",
            }
        ],
    }
    return mocker.patch("requests.post", return_value=response)


# ── Core contract ─────────────────────────────────────────────────────────────

def test_returns_assistant_content(mock_post):
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL)
    assert client.generate(MESSAGES) == REPLY


def test_posts_to_chat_completions_endpoint(mock_post):
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL)
    client.generate(MESSAGES)
    assert mock_post.call_args[0][0] == f"{BASE_URL}/v1/chat/completions"


def test_sends_messages_and_model_in_body(mock_post):
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL)
    client.generate(MESSAGES)
    payload = mock_post.call_args[1]["json"]
    assert payload["messages"] == MESSAGES
    assert payload["model"] == MODEL


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_sends_api_key_as_bearer_header(mock_post):
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL, api_key=API_KEY)
    client.generate(MESSAGES)
    headers = mock_post.call_args[1]["headers"]
    assert headers["Authorization"] == f"Bearer {API_KEY}"


def test_omits_auth_header_when_no_api_key(mock_post):
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL, api_key="")
    client.generate(MESSAGES)
    headers = mock_post.call_args[1]["headers"]
    assert "Authorization" not in headers


# ── Timeout ───────────────────────────────────────────────────────────────────

def test_passes_timeout_to_request(mock_post):
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL, timeout=60)
    client.generate(MESSAGES)
    assert mock_post.call_args[1]["timeout"] == 60


def test_raises_on_timeout(mocker):
    mocker.patch("requests.post", side_effect=requests.exceptions.Timeout)
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL)
    with pytest.raises(RuntimeError, match="timed out"):
        client.generate(MESSAGES)


# ── Error handling ────────────────────────────────────────────────────────────

def test_raises_on_http_error(mocker):
    response = mocker.MagicMock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("503 Service Unavailable")
    mocker.patch("requests.post", return_value=response)
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL)
    with pytest.raises(requests.exceptions.HTTPError, match="503 Service Unavailable"):
        client.generate(MESSAGES)


def test_raises_on_connection_error(mocker):
    mocker.patch("requests.post", side_effect=requests.exceptions.ConnectionError)
    client = MimoeLLMClient(base_url=BASE_URL, model=MODEL)
    with pytest.raises(RuntimeError, match="Could not connect"):
        client.generate(MESSAGES)


# ── Environment variables ─────────────────────────────────────────────────────

def test_reads_base_url_from_env(mocker, mock_post):
    mocker.patch.dict("os.environ", {"MIMOE_BASE_URL": "http://custom-host:8080"})
    client = MimoeLLMClient()
    client.generate(MESSAGES)
    assert mock_post.call_args[0][0] == "http://custom-host:8080/v1/chat/completions"


def test_reads_model_from_env(mocker, mock_post):
    mocker.patch.dict("os.environ", {"MIMOE_CHAT_MODEL": "mistral"})
    client = MimoeLLMClient()
    client.generate(MESSAGES)
    assert mock_post.call_args[1]["json"]["model"] == "mistral"


def test_reads_api_key_from_env(mocker, mock_post):
    mocker.patch.dict("os.environ", {"MIMOE_API_KEY": "env-secret"})
    client = MimoeLLMClient()
    client.generate(MESSAGES)
    assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer env-secret"


def test_normalizes_base_url_that_already_contains_v1(mock_post):
    client = MimoeLLMClient(base_url="http://localhost:8083/mimik-ai/openai/v1", model=MODEL)
    client.generate(MESSAGES)
    assert mock_post.call_args[0][0] == "http://localhost:8083/mimik-ai/openai/v1/chat/completions"

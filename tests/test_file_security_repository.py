import json
import pytest
from pathlib import Path

from security_agent.domain.ports import Document
from security_agent.infrastructure.file_security_repository import FileSecurityDataRepository


@pytest.fixture
def data_dir(tmp_path):
    access = [
        {
            "id": "acc-001",
            "timestamp": "2026-06-27T02:17:43Z",
            "user_id": "USR-089",
            "door_id": "DOOR-SERVER-01",
            "result": "denied",
            "reason": "outside_allowed_hours",
        }
    ]
    alarms = [
        {
            "id": "alm-001",
            "timestamp": "2026-06-27T02:21:35Z",
            "alarm_type": "tailgate_detected",
            "location": "DOOR-SERVER-01",
            "severity": "high",
            "acknowledged": False,
            "resolved": False,
            "notes": "Unidentified individual followed authorized staff.",
        }
    ]
    cameras = [
        {
            "id": "cam-001",
            "timestamp": "2026-06-27T02:17:30Z",
            "camera_id": "CAM-SERVER-HALL",
            "observation": "individual loitering near server room door",
            "confidence": 0.91,
            "tags": ["person", "loitering"],
        }
    ]
    doors = [
        {
            "id": "door-001",
            "timestamp": "2026-06-27T02:21:31Z",
            "door_id": "DOOR-SERVER-01",
            "event": "opened",
            "held_open_seconds": None,
            "forced": False,
        }
    ]
    policy = "Server room access outside approved hours is treated as a potential security breach.\n\nThree consecutive denied attempts trigger a medium alarm."

    (tmp_path / "access_logs.json").write_text(json.dumps(access))
    (tmp_path / "alarm_logs.json").write_text(json.dumps(alarms))
    (tmp_path / "camera_observations.json").write_text(json.dumps(cameras))
    (tmp_path / "door_events.json").write_text(json.dumps(doors))
    (tmp_path / "security_policy.txt").write_text(policy)

    return tmp_path


# ── Contract ──────────────────────────────────────────────────────────────────

def test_returns_list_of_documents(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    docs = repo.load_documents()
    assert isinstance(docs, list)
    assert all(isinstance(d, Document) for d in docs)


def test_loads_documents_from_all_sources(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    sources = {doc.source for doc in repo.load_documents()}
    assert "access_logs" in sources
    assert "alarm_logs" in sources
    assert "camera_observations" in sources
    assert "door_events" in sources
    assert "security_policy" in sources


def test_access_log_document_contains_key_fields(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    docs = {doc.source: doc for doc in repo.load_documents() if doc.source == "access_logs"}
    doc = list(docs.values())[0]
    assert "USR-089" in doc.content
    assert "DOOR-SERVER-01" in doc.content
    assert "denied" in doc.content
    assert doc.timestamp == "2026-06-27T02:17:43Z"


def test_alarm_document_contains_key_fields(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    docs = [doc for doc in repo.load_documents() if doc.source == "alarm_logs"]
    doc = docs[0]
    assert "tailgate_detected" in doc.content
    assert "DOOR-SERVER-01" in doc.content
    assert "high" in doc.content
    assert doc.timestamp == "2026-06-27T02:21:35Z"


def test_camera_document_contains_observation(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    docs = [doc for doc in repo.load_documents() if doc.source == "camera_observations"]
    doc = docs[0]
    assert "loitering near server room door" in doc.content
    assert doc.timestamp == "2026-06-27T02:17:30Z"


def test_door_document_contains_key_fields(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    docs = [doc for doc in repo.load_documents() if doc.source == "door_events"]
    doc = docs[0]
    assert "DOOR-SERVER-01" in doc.content
    assert "opened" in doc.content
    assert doc.timestamp == "2026-06-27T02:21:31Z"


def test_policy_splits_into_paragraphs(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    policy_docs = [doc for doc in repo.load_documents() if doc.source == "security_policy"]
    assert len(policy_docs) == 2
    assert "server room" in policy_docs[0].content.lower()
    assert "three consecutive" in policy_docs[1].content.lower()


def test_each_document_has_unique_id(data_dir):
    repo = FileSecurityDataRepository(data_dir=data_dir)
    ids = [doc.id for doc in repo.load_documents()]
    assert len(ids) == len(set(ids))


def test_accepts_path_string(data_dir):
    repo = FileSecurityDataRepository(data_dir=str(data_dir))
    docs = repo.load_documents()
    assert len(docs) > 0

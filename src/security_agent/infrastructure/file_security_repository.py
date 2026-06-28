import json
from pathlib import Path
from typing import List, Union

from security_agent.domain.ports import Document


class FileSecurityDataRepository:
    def __init__(self, data_dir: Union[str, Path]) -> None:
        self._dir = Path(data_dir)

    def load_documents(self) -> List[Document]:
        docs: List[Document] = []
        docs.extend(self._load_json("access_logs.json",        "access_logs",        self._format_access))
        docs.extend(self._load_json("alarm_logs.json",         "alarm_logs",         self._format_alarm))
        docs.extend(self._load_json("camera_observations.json","camera_observations", self._format_camera))
        docs.extend(self._load_json("door_events.json",        "door_events",        self._format_door))
        docs.extend(self._load_policy("security_policy.txt"))
        return docs

    # ── loaders ──────────────────────────────────────────────────────────────

    def _load_json(self, filename, source, formatter) -> List[Document]:
        path = self._dir / filename
        records = json.loads(path.read_text())
        return [
            Document(
                id=rec["id"],
                content=formatter(rec),
                source=source,
                timestamp=rec.get("timestamp", ""),
            )
            for rec in records
        ]

    def _load_policy(self, filename) -> List[Document]:
        path = self._dir / filename
        paragraphs = [p.strip() for p in path.read_text().split("\n\n") if p.strip()]
        return [
            Document(
                id=f"policy-{i}",
                content=paragraph,
                source="security_policy",
                timestamp="",
            )
            for i, paragraph in enumerate(paragraphs)
        ]

    # ── formatters ───────────────────────────────────────────────────────────

    @staticmethod
    def _format_access(r: dict) -> str:
        reason = f", reason: {r['reason']}" if r.get("reason") else ""
        return (
            f"Access event {r['id']}: user {r['user_id']} attempted {r['door_id']} "
            f"— {r['result']}{reason}."
        )

    @staticmethod
    def _format_alarm(r: dict) -> str:
        notes = f" Notes: {r['notes']}" if r.get("notes") else ""
        return (
            f"Alarm {r['id']}: {r['alarm_type']} at {r['location']} "
            f"[severity: {r['severity']}].{notes}"
        )

    @staticmethod
    def _format_camera(r: dict) -> str:
        tags = ", ".join(r.get("tags", []))
        return (
            f"Camera {r['camera_id']} observed: {r['observation']} "
            f"(confidence: {r['confidence']}, tags: {tags})."
        )

    @staticmethod
    def _format_door(r: dict) -> str:
        forced = " FORCED OPEN." if r.get("forced") else ""
        held = f" Held open {r['held_open_seconds']}s." if r.get("held_open_seconds") else ""
        return f"Door event {r['id']}: {r['door_id']} — {r['event']}.{forced}{held}"

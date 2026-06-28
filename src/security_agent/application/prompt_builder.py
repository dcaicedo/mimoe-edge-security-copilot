from typing import List

from security_agent.domain.ports import Document

_SYSTEM_PROMPT = "You are a security analyst. Identify security threats from event logs."

_MAX_CONTENT_CHARS = 140


def _format_document(doc: Document) -> str:
    timestamp_part = f" | {doc.timestamp}" if doc.timestamp else ""
    content = doc.content[:_MAX_CONTENT_CHARS].rstrip()
    return f"[{doc.source}{timestamp_part}] {content}"


class PromptBuilder:
    def build(self, query: str, documents: List[Document]) -> List[dict]:
        events = [d for d in documents if d.source != "security_policy"]
        policy = [d for d in documents if d.source == "security_policy"]

        parts: List[str] = []

        if policy:
            policy_block = "\n".join(_format_document(d) for d in policy)
            parts.append(f"POLICY:\n{policy_block}")

        if events:
            events_block = "\n".join(_format_document(d) for d in events)
            parts.append(f"EVENTS:\n{events_block}")

        parts.append(f"Question: {query}")
        parts.append(
            "Answer with:\n"
            "1. What happened (key incidents with timestamps)\n"
            "2. Risk level (CRITICAL / HIGH / MEDIUM / LOW)\n"
            "3. Recommended actions"
        )

        user_content = "\n\n".join(parts)

        return [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_content},
        ]

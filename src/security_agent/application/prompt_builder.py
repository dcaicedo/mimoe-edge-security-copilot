from typing import List

from security_agent.domain.ports import Document

_SYSTEM_PROMPT = """\
You are an expert security analyst. Given security event evidence below, \
produce a structured report with exactly these sections:

## Executive Summary
A concise paragraph describing what occurred and the overall threat picture.

## Uncommon Behaviors
Bullet list of behaviors that deviate from normal operations or policy.

## Risk Level
One of: CRITICAL / HIGH / MEDIUM / LOW — followed by a one-sentence justification.

## Evidence
Bullet list citing each piece of evidence with its source and timestamp.

## Recommended Actions
Numbered list of concrete, prioritized steps for the security team.

Be precise. Do not speculate beyond the evidence provided.\
"""


def _format_document(doc: Document) -> str:
    timestamp_part = f" | TIMESTAMP: {doc.timestamp}" if doc.timestamp else ""
    return f"[SOURCE: {doc.source}{timestamp_part}]\n{doc.content}"


class PromptBuilder:
    def build(self, query: str, documents: List[Document]) -> List[dict]:
        evidence_block = "\n\n".join(_format_document(doc) for doc in documents)

        if evidence_block:
            user_content = (
                f"SECURITY EVENT EVIDENCE:\n\n{evidence_block}\n\n"
                f"ANALYST QUERY: {query}"
            )
        else:
            user_content = f"ANALYST QUERY: {query}"

        return [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_content},
        ]

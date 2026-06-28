from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    id: str
    content: str
    source: str
    timestamp: str = ""

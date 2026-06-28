from typing import Any, Dict, List
from typing_extensions import Protocol

from security_agent.domain.ports import Document


class EmbeddingClient(Protocol):
    def embed(self, text: str) -> List[float]:
        ...


class LLMClient(Protocol):
    def generate(self, messages: List[dict]) -> str:
        ...


class SecurityDataRepository(Protocol):
    def load_documents(self) -> List[Document]:
        ...


class Retriever(Protocol):
    def add_document(self, doc_id: str, text: str) -> None:
        ...

    def find_relevant(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        ...


class PromptBuilderPort(Protocol):
    def build(self, query: str, documents: List[Document]) -> List[dict]:
        ...

from typing import List, Dict, Any
from security_agent.application.ports import EmbeddingClient
from security_agent.domain.similarity import cosine_similarity


class SemanticRetriever:
    def __init__(self, embedding_client: EmbeddingClient) -> None:
        self._client = embedding_client
        self._store: Dict[str, List[float]] = {}

    def add_document(self, doc_id: str, text: str) -> None:
        self._store[doc_id] = self._client.embed(text)

    def find_relevant(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        query_vector = self._client.embed(query)
        scored = [
            {"doc_id": doc_id, "score": cosine_similarity(query_vector, vec)}
            for doc_id, vec in self._store.items()
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

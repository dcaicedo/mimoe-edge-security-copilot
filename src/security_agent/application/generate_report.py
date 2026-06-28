from security_agent.application.ports import (
    LLMClient,
    PromptBuilderPort,
    Retriever,
    SecurityDataRepository,
)


class GenerateSecurityReport:
    def __init__(
        self,
        repository: SecurityDataRepository,
        retriever: Retriever,
        prompt_builder: PromptBuilderPort,
        llm_client: LLMClient,
    ) -> None:
        self._repository = repository
        self._retriever = retriever
        self._prompt_builder = prompt_builder
        self._llm = llm_client

    def execute(self, query: str, top_k: int = 5) -> str:
        documents = self._repository.load_documents()
        doc_index = {doc.id: doc for doc in documents}

        for doc in documents:
            self._retriever.add_document(doc.id, doc.content)

        relevant = self._retriever.find_relevant(query=query, top_k=top_k)
        selected = [doc_index[r["doc_id"]] for r in relevant if r["doc_id"] in doc_index]

        messages = self._prompt_builder.build(query=query, documents=selected)
        return self._llm.generate(messages)

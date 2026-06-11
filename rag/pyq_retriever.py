from typing import Any

from config.settings import settings
from rag.vector_store import VectorStore


class PYQRetriever:
    """Retriever for exam-pattern context from CBSE PYQ question chunks."""

    def __init__(self):
        self._embedder = None
        self._store: VectorStore | None = None

    @property
    def store(self) -> VectorStore:
        if self._store is None:
            self._store = VectorStore(
                dim=settings.embedding_dim,
                index_path=settings.pyq_faiss_index_path,
                meta_path=settings.pyq_metadata_path,
            )
        return self._store

    @property
    def embedder(self):
        if self._embedder is None:
            from ingest.embedder import Embedder
            self._embedder = Embedder(model_name=settings.embedding_model)
        return self._embedder

    def retrieve(self, query: str, top_k: int = 5,
                 paper_level: str | None = None,
                 question_type: str | None = None) -> list[dict[str, Any]]:
        query_vector = self.embedder.embed(query)
        results = self.store.search(query_vector, k=max(top_k * 20, 100))

        filtered = results
        has_filters = bool(paper_level or question_type)
        if paper_level:
            level = paper_level.lower()
            filtered = [r for r in filtered if r.get("paper_level", "").lower() == level]
        if question_type:
            qtype = question_type.lower()
            filtered = [r for r in filtered if r.get("question_type", "").lower() == qtype]

        if has_filters:
            return filtered[:top_k]
        return results[:top_k]

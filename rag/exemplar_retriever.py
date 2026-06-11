from typing import Any

from config.settings import settings
from rag.vector_store import VectorStore


class ExemplarRetriever:
    """Retriever for board-aligned conceptual depth from NCERT Exemplar chunks."""

    def __init__(self):
        self._embedder = None
        self._store: VectorStore | None = None

    @property
    def store(self) -> VectorStore:
        if self._store is None:
            self._store = VectorStore(
                dim=settings.embedding_dim,
                index_path=settings.exemplar_faiss_index_path,
                meta_path=settings.exemplar_metadata_path,
            )
        return self._store

    @property
    def embedder(self):
        if self._embedder is None:
            from ingest.embedder import Embedder
            self._embedder = Embedder(model_name=settings.embedding_model)
        return self._embedder

    def retrieve(self, query: str, top_k: int = 5,
                 chapter: str | None = None,
                 question_type: str | None = None,
                 estimated_depth: str | None = None) -> list[dict[str, Any]]:
        query_vector = self.embedder.embed(query)
        results = self.store.search(query_vector, k=max(top_k * 25, 100))

        filtered = results
        has_filters = bool(chapter or question_type or estimated_depth)
        if chapter:
            chapter_l = chapter.lower()
            filtered = [r for r in filtered if chapter_l in r.get("chapter", "").lower()]
        if question_type:
            qtype = question_type.lower()
            filtered = [r for r in filtered if r.get("question_type", "").lower() == qtype]
        if estimated_depth:
            depth = estimated_depth.lower()
            filtered = [r for r in filtered if r.get("estimated_depth", "").lower() == depth]

        if has_filters:
            return filtered[:top_k]
        return results[:top_k]

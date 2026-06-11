import logging
from typing import Any

from config.settings import settings
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self):
        self._embedder = None
        self._store: VectorStore | None = None
        self._graph_rag = None

    @property
    def store(self) -> VectorStore:
        if self._store is None:
            self._store = VectorStore(
                dim=settings.embedding_dim,
                index_path=settings.faiss_index_path,
                meta_path=settings.faiss_metadata_path,
            )
        return self._store

    @property
    def embedder(self):
        if self._embedder is None:
            from ingest.embedder import Embedder
            self._embedder = Embedder(model_name=settings.embedding_model)
        return self._embedder

    @property
    def graph_rag(self):
        if self._graph_rag is None:
            from graph.graph_rag import GraphRAG
            self._graph_rag = GraphRAG(store=self._store, embedder=self._embedder)
        return self._graph_rag

    def retrieve(self, query: str, top_k: int | None = None,
                 chapter_filter: str | None = None) -> list[dict[str, Any]]:
        k = top_k or settings.top_k_retrieved
        query_vector = self.embedder.embed(query)
        results = self.store.search(query_vector, k=max(k * 3, 15))

        if chapter_filter:
            chapter_lower = chapter_filter.lower()
            filtered = [r for r in results if chapter_lower in r.get("chapter", "").lower()]
            if len(filtered) >= k:
                return filtered[:k]
            remaining = [r for r in results if r not in filtered]
            filtered.extend(remaining)
            results = filtered

        return results[:k]

    def retrieve_graph(self, query: str, top_k: int | None = None,
                       chapter_filter: str | None = None,
                       expand_depth: int = 1) -> dict[str, Any]:
        k = top_k or settings.top_k_retrieved
        return self.graph_rag.retrieve(
            query=query,
            top_k=k,
            chapter_filter=chapter_filter,
            expand_depth=expand_depth,
        )

    def build_prompt_context(self, query: str, top_k: int | None = None,
                              chapter_filter: str | None = None,
                              difficulty: str | None = None) -> tuple[str, list[dict], dict]:
        k = top_k or settings.top_k_retrieved
        return self.graph_rag.build_prompt_context(
            query=query,
            top_k=k,
            chapter_filter=chapter_filter,
            difficulty=difficulty,
        )

import json
import logging
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, dim: int = 384, index_path: str | Path = "data/faiss.index",
                 meta_path: str | Path = "data/metadata.json"):
        self.dim = dim
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self.index: faiss.Index | None = None
        self.metadata: list[dict[str, Any]] = []

    def _ensure_index(self):
        if self.index is None:
            if self.index_path.exists():
                logger.info(f"Loading FAISS index from {self.index_path}")
                self.index = faiss.read_index(str(self.index_path))
                self.metadata = json.loads(self.meta_path.read_text())
                self.dim = self.index.d
            else:
                logger.info(f"Creating new FAISS index (dim={self.dim})")
                self.index_path.parent.mkdir(parents=True, exist_ok=True)
                base = faiss.IndexFlatIP(self.dim)
                self.index = faiss.IndexIDMap2(base)
                self.metadata = []

    def add(self, vectors: NDArray[np.float32], metadata: list[dict[str, Any]]):
        self._ensure_index()
        n = len(vectors)
        if n == 0:
            return
        ids = np.arange(len(self.metadata), len(self.metadata) + n, dtype=np.int64)
        self.index.add_with_ids(vectors, ids)
        self.metadata.extend(metadata)
        self.save()
        logger.info(f"Added {n} vectors (total: {len(self.metadata)})")

    def search(self, query_vector: NDArray[np.float32], k: int = 5) -> list[dict[str, Any]]:
        self._ensure_index()
        if self.index.ntotal == 0:
            return []
        query = query_vector.reshape(1, -1).astype(np.float32)
        scores, ids = self.index.search(query, min(k, self.index.ntotal))
        results = []
        for idx, score in zip(ids[0], scores[0]):
            if idx == -1:
                continue
            entry = dict(self.metadata[idx])
            entry["score"] = float(score)
            results.append(entry)
        return results

    def search_by_chapter(self, chapter: str, k: int = 10) -> list[dict[str, Any]]:
        results = []
        for entry in self.metadata:
            if chapter.lower() in entry.get("chapter", "").lower():
                results.append(entry)
        return results[:k]

    def all(self) -> list[dict[str, Any]]:
        self._ensure_index()
        return self.metadata

    @property
    def count(self) -> int:
        self._ensure_index()
        return self.index.ntotal if self.index else 0

    def save(self):
        if self.index is None:
            return
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps(self.metadata, ensure_ascii=False))

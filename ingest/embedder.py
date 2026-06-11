import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        return self._model

    def embed(self, text: str) -> NDArray[np.float32]:
        return self.model.encode(text, normalize_embeddings=True).astype(np.float32)

    def embed_batch(self, texts: list[str]) -> NDArray[np.float32]:
        return self.model.encode(texts, normalize_embeddings=True).astype(np.float32)

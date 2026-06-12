import logging
from pathlib import Path

from config.settings import normalize_subject, settings
from ingest.chunker import NCERTChunker
from ingest.embedder import Embedder
from ingest.extractor import PDFExtractor
from ingest.science_chunker import ScienceNCERTChunker
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


def run_ingestion(data_dir: str | None = None, subject: str = "maths") -> int:
    subject = normalize_subject(subject)
    root = Path(data_dir or settings.content_dir_for(subject, "textbook"))
    pdf_files = sorted(root.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDFs found in {root}")
        return 0

    extractor = PDFExtractor()
    chunker = ScienceNCERTChunker() if subject == "science" else NCERTChunker()
    embedder = Embedder(model_name=settings.embedding_model)
    index_path, meta_path = settings.index_paths_for(subject, "textbook")
    store = VectorStore(
        dim=settings.embedding_dim,
        index_path=index_path,
        meta_path=meta_path,
    )

    all_chunks = []
    for pdf_path in pdf_files:
        text = extractor.extract(pdf_path)
        chunks = chunker.chunk(text, source=pdf_path.name)
        all_chunks.extend(chunks)
        logger.info(f"{pdf_path.name}: {len(chunks)} chunks")

    if not all_chunks:
        logger.warning("No chunks extracted")
        return 0

    texts = [c.text for c in all_chunks]
    vectors = embedder.embed_batch(texts)

    metadata = []
    for chunk in all_chunks:
        metadata.append({
            "text": chunk.text,
            "source": chunk.source,
            "chapter": chunk.chapter,
            "section": chunk.section,
            "chunk_id": chunk.chunk_id,
            **chunk.metadata,
        })

    store.add(vectors, metadata)
    logger.info(f"Stored {len(all_chunks)} chunks in FAISS")
    return len(all_chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = run_ingestion()
    print(f"Ingested {count} chunks")

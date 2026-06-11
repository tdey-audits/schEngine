import logging
from pathlib import Path

from config.settings import settings
from ingest.embedder import Embedder
from ingest.exemplar_chunker import ExemplarChunker
from ingest.extractor import PDFExtractor
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


def run_exemplar_ingestion(data_dir: str | None = None) -> int:
    root = Path(data_dir or settings.exemplar_data_dir)
    pdf_files = sorted(root.rglob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No NCERT Exemplar PDFs found in {root}")
        return 0

    extractor = PDFExtractor()
    chunker = ExemplarChunker()
    embedder = Embedder(model_name=settings.embedding_model)
    store = VectorStore(
        dim=settings.embedding_dim,
        index_path=settings.exemplar_faiss_index_path,
        meta_path=settings.exemplar_metadata_path,
    )

    all_chunks = []
    for pdf_path in pdf_files:
        source = str(pdf_path.relative_to(root))
        text = extractor.extract(pdf_path)
        chunks = chunker.chunk(text, source=source)
        all_chunks.extend(chunks)
        logger.info(f"{source}: {len(chunks)} NCERT Exemplar chunks")

    if not all_chunks:
        logger.warning("No NCERT Exemplar chunks extracted")
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
    logger.info(f"Stored {len(all_chunks)} NCERT Exemplar chunks in FAISS")
    return len(all_chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = run_exemplar_ingestion()
    print(f"Ingested {count} NCERT Exemplar chunks")

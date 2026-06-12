import logging
from pathlib import Path

from config.settings import normalize_subject, settings
from ingest.chunker import NCERTChunker
from ingest.embedder import Embedder
from ingest.extractor import PDFExtractor
from ingest.science_chunker import ScienceNCERTChunker
from ingest.sst_chunker import SSTNCERTChunker
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


def run_ingestion(data_dir: str | None = None, subject: str = "maths") -> int:
    subject = normalize_subject(subject)
    root = Path(data_dir or settings.content_dir_for(subject, "textbook"))
    pdf_files = sorted(root.rglob("*.pdf") if subject == "sst" else root.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDFs found in {root}")
        return 0

    extractor = PDFExtractor()
    if subject == "science":
        chunker = ScienceNCERTChunker()
    elif subject == "sst":
        chunker = SSTNCERTChunker()
    else:
        chunker = NCERTChunker()
    embedder = Embedder(model_name=settings.embedding_model)
    index_path, meta_path = settings.index_paths_for(subject, "textbook")
    store = VectorStore(
        dim=settings.embedding_dim,
        index_path=index_path,
        meta_path=meta_path,
    )

    all_chunks = []
    for pdf_path in pdf_files:
        source = str(pdf_path.relative_to(root)) if subject == "sst" else pdf_path.name
        if subject == "sst" and source.lower().startswith("pyqs/"):
            continue
        if subject == "sst" and (pdf_path.name.lower() == "ps.pdf" or source == "Social-History/ch1.pdf"):
            logger.info(f"{source}: skipped non-chapter or duplicate PDF")
            continue
        text = extractor.extract(pdf_path)
        chunks = chunker.chunk(text, source=source)
        all_chunks.extend(chunks)
        logger.info(f"{source}: {len(chunks)} chunks")

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

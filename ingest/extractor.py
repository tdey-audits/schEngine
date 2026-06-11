import logging
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)


class PDFExtractor:
    def extract(self, pdf_path: Path) -> str:
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages)

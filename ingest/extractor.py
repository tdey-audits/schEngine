import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFExtractor:
    def extract(self, pdf_path: Path) -> str:
        try:
            import fitz
        except ModuleNotFoundError:
            return self._extract_with_pdftotext(pdf_path)

        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages)

    def _extract_with_pdftotext(self, pdf_path: Path) -> str:
        try:
            result = subprocess.run(
                ["pdftotext", str(pdf_path), "-"],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(
                "PDF extraction requires PyMuPDF (`pymupdf`) or the `pdftotext` binary"
            ) from exc
        return result.stdout

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    text: str
    source: str
    chapter: str = ""
    section: str = ""
    chunk_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class NCERTChunker:
    CHAPTER_RE = re.compile(r"^(Chapter\s+\d+|Real Numbers|Polynomials|Pair of Linear|Quadratic|Arithmetic Progressions|Triangles|Coordinate|Trigonometry|Circles|Constructions|Areas|Surface|Statistics|Probability)", re.IGNORECASE | re.MULTILINE)
    SECTION_RE = re.compile(r"^(\d+\.\d+\s+[A-Z])", re.MULTILINE)
    EXERCISE_RE = re.compile(r"^(Exercise\s+\d+\.\d+)", re.MULTILINE)

    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        paragraphs = re.split(r"\n\s*\n", text)
        chunks: list[Chunk] = []
        current_section = "introduction"
        current_chapter = self._guess_chapter(source)

        buffer: list[str] = []
        buffer_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < 20:
                continue

            exercise_match = self.EXERCISE_RE.search(para)
            if exercise_match:
                current_section = exercise_match.group(1)

            section_match = self.SECTION_RE.match(para)
            if section_match:
                current_section = section_match.group(1)

            if buffer_len + len(para) > 1500 and buffer:
                chunks.append(self._make_chunk(buffer, source, current_chapter, current_section))
                buffer = []
                buffer_len = 0

            buffer.append(para)
            buffer_len += len(para)

        if buffer:
            chunks.append(self._make_chunk(buffer, source, current_chapter, current_section))

        return chunks

    def _make_chunk(self, buffer: list[str], source: str, chapter: str, section: str) -> Chunk:
        text = "\n\n".join(buffer)
        return Chunk(
            text=text,
            source=source,
            chapter=chapter,
            section=section,
            chunk_id=f"{source}::{chapter}::{section}::{hash(text) % 10**8}",
        )

    def _guess_chapter(self, source: str) -> str:
        name = source.lower().replace("_", " ").replace(".pdf", "")
        for keyword in ["real numbers", "polynomials", "linear equations", "quadratic",
                         "arithmetic progressions", "triangles", "coordinate geometry",
                         "trigonometry", "circles", "constructions", "areas related",
                         "surface areas", "statistics", "probability"]:
            if keyword in name:
                return keyword.title()
        return source.replace(".pdf", "")

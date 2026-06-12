import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ingest.chunker import Chunk
from syllabus.ncert_class10_science import CHAPTER_NAME_BY_NUMBER


CHAPTER_NO_RE = re.compile(r"ch(\d{1,2})", re.IGNORECASE)
QUESTION_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+")
SECTION_RE = re.compile(r"SECTION\s*[-–]?\s*([A-E])", re.IGNORECASE)


def _chapter_number_from_source(source: str) -> int | None:
    match = CHAPTER_NO_RE.search(Path(source).stem)
    if not match:
        return None
    return int(match.group(1))


def _chapter_name_from_source(source: str) -> str:
    number = _chapter_number_from_source(source)
    if number and number in CHAPTER_NAME_BY_NUMBER:
        return CHAPTER_NAME_BY_NUMBER[number]
    return Path(source).stem


class ScienceNCERTChunker:
    SECTION_MARKERS = re.compile(
        r"(?m)^(Activity\s+\d+\.\d+|\d+\.\d+\s+[A-Z][^\n]+|Questions|Exercise|What you have learnt)"
    )

    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        text = self._clean_text(text)
        chapter = _chapter_name_from_source(source)
        chapter_no = _chapter_number_from_source(source)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks: list[Chunk] = []
        current_section = "introduction"
        buffer: list[str] = []
        buffer_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < 20:
                continue
            marker = self.SECTION_MARKERS.match(para)
            if marker:
                current_section = re.sub(r"\s+", " ", marker.group(1)).strip()

            if buffer and buffer_len + len(para) > 1500:
                chunks.append(self._make_chunk(buffer, source, chapter, current_section, chapter_no))
                buffer = []
                buffer_len = 0

            buffer.append(para)
            buffer_len += len(para)

        if buffer:
            chunks.append(self._make_chunk(buffer, source, chapter, current_section, chapter_no))
        return chunks

    def _make_chunk(self, buffer: list[str], source: str, chapter: str,
                    section: str, chapter_no: int | None) -> Chunk:
        text = "\n\n".join(buffer)
        return Chunk(
            text=text,
            source=source,
            chapter=chapter,
            section=section,
            chunk_id=f"{source}::{chapter}::{section}::{hash(text) % 10**8}",
            metadata={
                "subject": "science",
                "source_type": "ncert_textbook",
                "chapter_number": chapter_no,
                "retrieval_role": "concept_grounding",
            },
        )

    def _clean_text(self, text: str) -> str:
        text = text.replace("\u00a0", " ").replace("\u00ad", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


@dataclass(frozen=True)
class ScienceExemplarSection:
    label: str
    question_type: str
    marks: int
    estimated_depth: str


SCIENCE_EXEMPLAR_SECTIONS = (
    (re.compile(r"Multiple Choice Questions", re.IGNORECASE), ScienceExemplarSection("Multiple Choice Questions", "mcq", 1, "medium")),
    (re.compile(r"Short Answer Questions", re.IGNORECASE), ScienceExemplarSection("Short Answer Questions", "sa", 3, "challenging")),
    (re.compile(r"Long Answer Questions", re.IGNORECASE), ScienceExemplarSection("Long Answer Questions", "la", 5, "challenging")),
)


class ScienceExemplarChunker:
    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        text = self._clean_text(text)
        chapter = _chapter_name_from_source(source)
        chapter_no = _chapter_number_from_source(source)
        section_spans = self._section_spans(text)
        chunks: list[Chunk] = []
        for section, block in section_spans:
            chunks.extend(self._split_questions(block, source, chapter, chapter_no, section))
        return chunks

    def _section_spans(self, text: str) -> list[tuple[ScienceExemplarSection, str]]:
        matches: list[tuple[int, ScienceExemplarSection]] = []
        for pattern, section in SCIENCE_EXEMPLAR_SECTIONS:
            for match in pattern.finditer(text):
                matches.append((match.start(), section))
        matches.sort(key=lambda item: item[0])
        if not matches:
            return [(ScienceExemplarSection("Questions", "sa", 3, "medium"), text)]

        spans = []
        for i, (start, section) in enumerate(matches):
            end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            spans.append((section, text[start:end]))
        return spans

    def _split_questions(self, block: str, source: str, chapter: str,
                         chapter_no: int | None, section: ScienceExemplarSection) -> list[Chunk]:
        matches = list(QUESTION_RE.finditer(block))
        chunks: list[Chunk] = []
        for i, match in enumerate(matches):
            q_no = int(match.group(1))
            end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
            question = self._trim_noise(block[match.start():end].strip())
            if not self._is_valid_question(question):
                continue
            metadata: dict[str, Any] = {
                "subject": "science",
                "source_type": "ncert_exemplar",
                "retrieval_role": "concept_depth",
                "chapter_number": chapter_no,
                "question_no": q_no,
                "question_type": section.question_type,
                "marks": section.marks,
                "estimated_depth": section.estimated_depth,
                "section_name": section.label,
                "board_alignment": "strict_ncert_class10_science",
            }
            chunks.append(Chunk(
                text=question,
                source=source,
                chapter=chapter,
                section=section.label,
                chunk_id=f"{source}::{chapter_no}::{section.question_type}::{q_no:02d}::{hash(question) % 10**8}",
                metadata=metadata,
            ))
        return chunks

    def _clean_text(self, text: str) -> str:
        text = text.replace("\u00a0", " ").replace("\u00ad", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _trim_noise(self, question: str) -> str:
        question = re.sub(r"\n?\d+\s+E XEMPLAR P ROBLEMS.*$", "", question, flags=re.DOTALL)
        question = re.sub(r"\n?Answers.*$", "", question, flags=re.DOTALL | re.IGNORECASE)
        return question.strip()

    def _is_valid_question(self, question: str) -> bool:
        return len(question) >= 20 and bool(re.search(r"[A-Za-z]", question))


class SciencePYQChunker:
    HEADER_PATTERNS = (
        re.compile(r"^CBSE Board Examination", re.IGNORECASE),
        re.compile(r"^Solved Paper", re.IGNORECASE),
        re.compile(r"^Class\s*[-–]?\s*10", re.IGNORECASE),
        re.compile(r"^Maximum Marks", re.IGNORECASE),
        re.compile(r"^Time allowed", re.IGNORECASE),
        re.compile(r"^GENERAL INSTRUCTIONS", re.IGNORECASE),
        re.compile(r"^Delhi Set", re.IGNORECASE),
        re.compile(r"^\d+/\d+/\d+$"),
        re.compile(r"^Oswaal", re.IGNORECASE),
    )

    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        text = self._english_question_block(text)
        text = self._clean_text(text)
        return self._split_questions(text, source)

    def _english_question_block(self, text: str) -> str:
        section_a = re.search(r"SECTION\s*[-–]?\s*A", text, re.IGNORECASE)
        if section_a:
            return text[section_a.start():]
        return text

    def _clean_text(self, text: str) -> str:
        lines: list[str] = []
        for raw_line in text.splitlines():
            line = re.sub(r"[ \t]+", " ", raw_line.replace("\u00ad", "")).strip()
            if not line:
                continue
            if any(pattern.search(line) for pattern in self.HEADER_PATTERNS):
                continue
            if re.fullmatch(r"[\d/#\-\s]+", line):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def _split_questions(self, text: str, source: str) -> list[Chunk]:
        matches = list(QUESTION_RE.finditer(text))
        candidates: dict[int, list[str]] = {}
        for i, match in enumerate(matches):
            q_no = int(match.group(1))
            if not 1 <= q_no <= 39:
                continue
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            question = self._trim_trailing_section_noise(text[match.start():end].strip())
            if self._is_valid_question(question):
                candidates.setdefault(q_no, []).append(question)

        chunks: list[Chunk] = []
        for q_no in sorted(candidates):
            # Science PYQ PDFs in this corpus are solved papers: the same
            # question number can appear later in the answer/explanation key.
            # Keep the first paper-section occurrence, not the longer solution.
            question = candidates[q_no][0]
            qtype, marks = self._type_and_marks(q_no)
            section = self._section_for_question(q_no)
            metadata: dict[str, Any] = {
                "subject": "science",
                "source_type": "pyq",
                "paper_level": "science",
                "paper_code": Path(source).stem,
                "language": "english",
                "question_no": q_no,
                "question_type": qtype,
                "marks": marks,
                "retrieval_role": "exam_pattern",
            }
            chunks.append(Chunk(
                text=question,
                source=source,
                chapter="CBSE Class 10 Science PYQ",
                section=section,
                chunk_id=f"{source}::science::{q_no:02d}::{hash(question) % 10**8}",
                metadata=metadata,
            ))
        return chunks

    def _trim_trailing_section_noise(self, question: str) -> str:
        next_section = SECTION_RE.search(question, 8)
        if next_section:
            question = question[:next_section.start()].strip()
        return question

    def _is_valid_question(self, question: str) -> bool:
        return len(question) >= 20 and bool(re.search(r"[A-Za-z]", question))

    def _section_for_question(self, question_no: int) -> str:
        if 1 <= question_no <= 20:
            return "Section A"
        if 21 <= question_no <= 26:
            return "Section B"
        if 27 <= question_no <= 33:
            return "Section C"
        if 34 <= question_no <= 36:
            return "Section D"
        if 37 <= question_no <= 39:
            return "Section E"
        return "Unknown"

    def _type_and_marks(self, question_no: int) -> tuple[str, int]:
        if 1 <= question_no <= 18:
            return "mcq", 1
        if 19 <= question_no <= 20:
            return "assertion_reason", 1
        if 21 <= question_no <= 26:
            return "vsa", 2
        if 27 <= question_no <= 33:
            return "sa", 3
        if 34 <= question_no <= 36:
            return "la", 5
        if 37 <= question_no <= 39:
            return "case_study", 4
        return "unknown", 0

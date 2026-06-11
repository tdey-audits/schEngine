import re
from dataclasses import dataclass
from typing import Any

from ingest.chunker import Chunk


CHAPTER_RE = re.compile(r"(?m)^([A-Z][A-Z \-]+)\nCHAPTER\s*(\d+)")
EXERCISE_RE = re.compile(r"(?m)^\s*EXERCISE\s+(\d+\.\d+)")
QUESTION_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+")
SECTION_RE = re.compile(r"(?m)^\(([B-E])\)\s+(.+Questions.*)$")


CHAPTER_NAME_MAP = {
    "REAL NUMBERS": "Real Numbers",
    "POLYNOMIALS": "Polynomials",
    "PAIR OF LINEAR EQUATIONS IN TWO VARIABLES": "Pair of Linear Equations in Two Variables",
    "QUADRATIC EQUATIONS": "Quadratic Equations",
    "ARITHMETIC PROGRESSIONS": "Arithmetic Progressions",
    "TRIANGLES": "Triangles",
    "COORDINATE GEOMETRY": "Coordinate Geometry",
    "INTRODUCTION TO TRIGONOMETRY AND ITS APPLICATIONS": "Introduction to Trigonometry",
    "CIRCLES": "Circles",
    "CONSTRUCTIONS": "Constructions",
    "AREA RELATED TO CIRCLES": "Areas Related to Circles",
    "SURFACE AREAS AND VOLUMES": "Surface Areas and Volumes",
    "STATISTICS AND PROBABILITY": "Statistics",
}


@dataclass(frozen=True)
class ExemplarSection:
    label: str
    name: str
    question_type: str
    marks: int
    estimated_depth: str


SECTION_MAP = {
    "B": ExemplarSection("B", "Multiple Choice Questions", "mcq", 1, "medium"),
    "C": ExemplarSection("C", "Short Answer Questions with Reasoning", "vsa", 2, "medium"),
    "D": ExemplarSection("D", "Short Answer Questions", "sa", 3, "challenging"),
    "E": ExemplarSection("E", "Long Answer Questions", "la", 4, "challenging"),
}


class ExemplarChunker:
    """Chunk NCERT Exemplar into board-aligned conceptual depth examples."""

    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        text = self._clean_text(text)
        chapters = self._chapter_spans(text)
        chunks: list[Chunk] = []
        for chapter_name, chapter_no, chapter_text in chapters:
            chunks.extend(self._chunk_chapter(chapter_text, source, chapter_name, chapter_no))
        return chunks

    def _clean_text(self, text: str) -> str:
        text = text.replace("\u00a0", " ")
        text = text.replace("\u00ad", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _chapter_spans(self, text: str) -> list[tuple[str, int, str]]:
        matches = list(CHAPTER_RE.finditer(text))
        spans = []
        for i, match in enumerate(matches):
            raw_name = re.sub(r"\s+", " ", match.group(1)).strip()
            chapter_name = CHAPTER_NAME_MAP.get(raw_name, raw_name.title())
            chapter_no = int(match.group(2))
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            spans.append((chapter_name, chapter_no, text[start:end]))
        return spans

    def _chunk_chapter(self, text: str, source: str, chapter: str, chapter_no: int) -> list[Chunk]:
        exercise_matches = list(EXERCISE_RE.finditer(text))
        chunks: list[Chunk] = []
        for i, exercise_match in enumerate(exercise_matches):
            exercise = exercise_match.group(1)
            start = exercise_match.end()
            end = exercise_matches[i + 1].start() if i + 1 < len(exercise_matches) else len(text)
            block = text[start:end].strip()
            section = self._section_before(text[:exercise_match.start()])
            chunks.extend(self._split_questions(block, source, chapter, chapter_no, exercise, section))
        return chunks

    def _section_before(self, prefix: str) -> ExemplarSection:
        matches = list(SECTION_RE.finditer(prefix))
        if not matches:
            return SECTION_MAP["D"]
        label = matches[-1].group(1)
        return SECTION_MAP.get(label, SECTION_MAP["D"])

    def _split_questions(self, block: str, source: str, chapter: str, chapter_no: int,
                         exercise: str, section: ExemplarSection) -> list[Chunk]:
        matches = list(QUESTION_RE.finditer(block))
        chunks: list[Chunk] = []
        for i, match in enumerate(matches):
            question_no = int(match.group(1))
            end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
            question = block[match.start():end].strip()
            question = self._trim_noise(question)
            if not self._is_valid_question(question):
                continue
            metadata: dict[str, Any] = {
                "source_type": "ncert_exemplar",
                "retrieval_role": "concept_depth",
                "chapter_number": chapter_no,
                "exercise": exercise,
                "question_no": question_no,
                "question_type": section.question_type,
                "marks": section.marks,
                "estimated_depth": section.estimated_depth,
                "section": section.label,
                "section_name": section.name,
                "board_alignment": "strict_ncert_class10",
            }
            chunks.append(Chunk(
                text=question,
                source=source,
                chapter=chapter,
                section=f"Exercise {exercise} ({section.label})",
                chunk_id=f"{source}::{chapter_no}::{exercise}::{question_no:02d}::{hash(question) % 10**8}",
                metadata=metadata,
            ))
        return chunks

    def _trim_noise(self, question: str) -> str:
        question = re.sub(r"\n?\(?[A-E]\)\s+[A-Za-z ]+Questions.*$", "", question, flags=re.DOTALL)
        question = re.sub(r"\n?EXERCISE\s+\d+\.\d+.*$", "", question, flags=re.DOTALL)
        return question.strip()

    def _is_valid_question(self, question: str) -> bool:
        if len(question) < 25:
            return False
        if not re.search(r"[A-Za-z]", question):
            return False
        return True

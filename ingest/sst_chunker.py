import re
from pathlib import Path
from typing import Any

from ingest.chunker import Chunk
from syllabus.ncert_class10_sst import CHAPTER_NAME_BY_STREAM_NUMBER, CHAPTERS


CHAPTER_NO_RE = re.compile(r"ch0?(\d{1,2})", re.IGNORECASE)
QUESTION_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+")
SECTION_RE = re.compile(r"SECTION\s*[-–]?\s*([A-F])", re.IGNORECASE)

STREAM_BY_FOLDER = {
    "social-history": "history",
    "social-geography": "geography",
    "social-political": "political",
    "social-economics": "economics",
}

GLOBAL_CHAPTER_OFFSET = {
    "history": 0,
    "geography": 5,
    "political": 12,
    "economics": 20,
}

STREAM_KEYWORDS: dict[str, set[str]] = {
    stream: set()
    for stream in STREAM_BY_FOLDER.values()
}
for chapter in CHAPTERS:
    terms = (chapter.name, chapter.stream, *chapter.aliases, *chapter.focus_terms)
    STREAM_KEYWORDS[chapter.stream].update(_term.lower() for _term in terms if _term)
STREAM_KEYWORDS["history"].update({
    "silk route", "congress session", "satyagraha", "non-cooperation", "civil disobedience",
    "dandi", "champaran", "kheda", "nationalism", "print culture", "industrialisation",
})
STREAM_KEYWORDS["geography"].update({
    "outline map", "dam", "river", "port", "airport", "crop", "thermal plant",
    "nuclear plant", "mine", "iron ore", "coal", "software technology park",
})
STREAM_KEYWORDS["political"].update({
    "power sharing", "federalism", "democracy", "political party", "communalism",
    "caste", "gender", "pressure group", "decentralisation",
})
STREAM_KEYWORDS["economics"].update({
    "per capita income", "gdp", "credit", "bank", "collateral", "globalisation",
    "consumer", "public sector", "private sector", "primary sector", "tertiary sector",
})


def _source_parts(source: str) -> tuple[str | None, int | None]:
    path = Path(source)
    folder = path.parts[0].lower() if len(path.parts) > 1 else ""
    stream = STREAM_BY_FOLDER.get(folder)
    match = CHAPTER_NO_RE.search(path.stem)
    chapter_no = int(match.group(1)) if match else None
    if stream and chapter_no:
        chapter_no += GLOBAL_CHAPTER_OFFSET.get(stream, 0)
    return stream, chapter_no


def _chapter_name_from_source(source: str) -> str:
    stream, chapter_no = _source_parts(source)
    if stream and chapter_no:
        return CHAPTER_NAME_BY_STREAM_NUMBER.get((stream, chapter_no), Path(source).stem)
    return Path(source).stem


class SSTNCERTChunker:
    SECTION_MARKERS = re.compile(
        r"(?m)^((?:\d+\.)?\d+\s+[A-Z][^\n]{5,}|Activity\s+\d+|Exercise|Project|Let us)"
    )

    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        text = self._clean_text(text)
        stream, chapter_no = _source_parts(source)
        chapter = _chapter_name_from_source(source)
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

            if buffer and buffer_len + len(para) > 1700:
                chunks.append(self._make_chunk(buffer, source, chapter, current_section, stream, chapter_no))
                buffer = []
                buffer_len = 0

            buffer.append(para)
            buffer_len += len(para)

        if buffer:
            chunks.append(self._make_chunk(buffer, source, chapter, current_section, stream, chapter_no))
        return chunks

    def _make_chunk(self, buffer: list[str], source: str, chapter: str, section: str,
                    stream: str | None, chapter_no: int | None) -> Chunk:
        text = "\n\n".join(buffer)
        return Chunk(
            text=text,
            source=source,
            chapter=chapter,
            section=section,
            chunk_id=f"{source}::{chapter}::{section}::{hash(text) % 10**8}",
            metadata={
                "subject": "sst",
                "stream": stream,
                "source_type": "ncert_textbook",
                "chapter_number": chapter_no,
                "retrieval_role": "concept_grounding",
                "board_alignment": "strict_ncert_class10_sst",
            },
        )

    def _clean_text(self, text: str) -> str:
        text = text.replace("\u00a0", " ").replace("\u00ad", "")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


class SSTPYQChunker:
    HEADER_PATTERNS = (
        re.compile(r"^CBSE Board Examination", re.IGNORECASE),
        re.compile(r"^Solved Paper", re.IGNORECASE),
        re.compile(r"^Class\s*[-–]?\s*10", re.IGNORECASE),
        re.compile(r"^Social Science", re.IGNORECASE),
        re.compile(r"^Maximum Marks", re.IGNORECASE),
        re.compile(r"^Time allowed", re.IGNORECASE),
        re.compile(r"^GENERAL INSTRUCTIONS", re.IGNORECASE),
        re.compile(r"^Delhi Set", re.IGNORECASE),
        re.compile(r"^Oswaal", re.IGNORECASE),
        re.compile(r"^\d+/\d+/\d+$"),
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
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
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
            if not 1 <= q_no <= 40:
                continue
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            question = self._trim_trailing_section_noise(text[match.start():end].strip())
            if self._is_valid_question(question):
                candidates.setdefault(q_no, []).append(question)

        chunks: list[Chunk] = []
        for q_no in sorted(candidates):
            question = candidates[q_no][0]
            qtype, marks = self._type_and_marks(q_no, source)
            section = self._section_for_question(q_no, source)
            stream = self._infer_stream(question)
            metadata: dict[str, Any] = {
                "subject": "sst",
                "stream": stream,
                "source_type": "pyq",
                "paper_level": "sst",
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
                chapter="CBSE Class 10 Social Science PYQ",
                section=section,
                chunk_id=f"{source}::sst::{q_no:02d}::{hash(question) % 10**8}",
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

    def _section_for_question(self, question_no: int, source: str = "") -> str:
        if "sem1" in Path(source).stem.lower():
            return "Section A"
        if 1 <= question_no <= 20:
            return "Section A"
        if 21 <= question_no <= 24:
            return "Section B"
        if 25 <= question_no <= 29:
            return "Section C"
        if 30 <= question_no <= 33:
            return "Section D"
        if 34 <= question_no <= 36:
            return "Section E"
        if question_no == 37:
            return "Section F"
        return "Unknown"

    def _type_and_marks(self, question_no: int, source: str = "") -> tuple[str, int]:
        if "sem1" in Path(source).stem.lower() and 1 <= question_no <= 40:
            return "mcq", 1
        if 1 <= question_no <= 20:
            return "mcq", 1
        if 21 <= question_no <= 24:
            return "vsa", 2
        if 25 <= question_no <= 29:
            return "sa", 3
        if 30 <= question_no <= 33:
            return "la", 5
        if 34 <= question_no <= 36:
            return "case_study", 4
        if question_no == 37:
            return "map_skill", 5
        return "unknown", 0

    def _infer_stream(self, question: str) -> str:
        text = question.lower()
        text = re.sub(r"political outline map", "outline map", text)
        scores = {
            stream: sum(1 for term in terms if term and term in text)
            for stream, terms in STREAM_KEYWORDS.items()
        }
        best_stream, best_score = max(scores.items(), key=lambda item: item[1])
        return best_stream if best_score else "mixed"

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ingest.chunker import Chunk


QUESTION_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+")
SECTION_RE = re.compile(r"SECTION\s+([A-E])", re.IGNORECASE)


@dataclass(frozen=True)
class PYQPaperInfo:
    level: str
    code: str


class PYQChunker:
    """Chunk CBSE Class 10 Maths PYQs as exam-pattern examples.

    PYQ PDFs are bilingual. The useful English question block normally starts at
    "General Instructions" and repeats the same questions after the Hindi block.
    We drop the earlier bilingual/instruction noise and split on board-paper
    question numbers instead of textbook-style paragraphs.
    """

    HEADER_PATTERNS = (
        re.compile(r"^\s*\d+\s*\|\s*P\s*a\s*g\s*e\s*$", re.IGNORECASE),
        re.compile(r"^P\.?T\.?O\.?$", re.IGNORECASE),
        re.compile(r"^Page\s+\d+\s+of\s+\d+$", re.IGNORECASE),
        re.compile(r"^\{?\s*\}?\s*$"),
        re.compile(r"^Candidates must write the Q\.P\. Code", re.IGNORECASE),
        re.compile(r"^Q\.P\. Code$", re.IGNORECASE),
        re.compile(r"^Roll No\.$", re.IGNORECASE),
        re.compile(r"^SET\s*[~\-\s]*\d+$", re.IGNORECASE),
        re.compile(r"^Series\s*:", re.IGNORECASE),
        re.compile(r"^Time allowed\s*:", re.IGNORECASE),
        re.compile(r"^Maximum Marks\s*:", re.IGNORECASE),
    )

    def chunk(self, text: str, source: str = "") -> list[Chunk]:
        info = self._paper_info(source)
        english = self._english_question_block(text)
        cleaned = self._clean_text(english)
        return self._split_questions(cleaned, source, info)

    def _paper_info(self, source: str) -> PYQPaperInfo:
        name = Path(source).name
        lower = name.lower()
        if "basic" in lower or "430" in lower:
            level = "basic"
        elif "standard" in lower or "std" in lower or lower.startswith("30"):
            level = "standard"
        else:
            level = "unknown"

        code_match = re.search(r"\b(?:30|430)[-_/]\d[-_/]\d\b", name)
        code = code_match.group(0).replace("_", "-") if code_match else Path(source).stem
        return PYQPaperInfo(level=level, code=code)

    def _english_question_block(self, text: str) -> str:
        markers = ["General Instructions", "SECTION A", "This section has"]
        start_positions = [text.find(marker) for marker in markers if text.find(marker) >= 0]
        if start_positions:
            text = text[min(start_positions):]

        section_a = re.search(r"SECTION\s+A", text, re.IGNORECASE)
        if section_a:
            text = text[section_a.start():]
        return text

    def _clean_text(self, text: str) -> str:
        lines: list[str] = []
        for raw_line in text.splitlines():
            line = self._normalize_line(raw_line)
            if not line:
                continue
            if self._is_noise_line(line):
                continue
            if self._looks_like_non_english_noise(line):
                continue
            lines.append(line)

        joined = "\n".join(lines)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        return joined.strip()

    def _normalize_line(self, line: str) -> str:
        line = line.replace("\u00ad", "")
        line = line.replace("\uf0b4", "pi")
        line = line.replace("\uf070", "pi")
        line = re.sub(r"[ \t]+", " ", line)
        return line.strip()

    def _is_noise_line(self, line: str) -> bool:
        if any(pattern.search(line) for pattern in self.HEADER_PATTERNS):
            return True
        if re.fullmatch(r"[\d/#\-\s]+", line):
            return True
        if re.fullmatch(r"\d{2,4}/\d/\d(?:/\d)?", line):
            return True
        return False

    def _looks_like_non_english_noise(self, line: str) -> bool:
        if any("\ue000" <= ch <= "\uf8ff" for ch in line):
            return True
        letters = [ch for ch in line if ch.isalpha()]
        if not letters:
            return False
        latin = sum(1 for ch in letters if "A" <= ch <= "Z" or "a" <= ch <= "z")
        return latin / max(len(letters), 1) < 0.45

    def _split_questions(self, text: str, source: str, info: PYQPaperInfo) -> list[Chunk]:
        matches = list(QUESTION_RE.finditer(text))
        candidates: dict[int, list[str]] = {}
        for i, match in enumerate(matches):
            q_no = int(match.group(1))
            if not 1 <= q_no <= 38:
                continue
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            raw_question = text[match.start():end].strip()
            question = self._trim_trailing_section_noise(raw_question)
            if not self._is_valid_question(question):
                continue
            candidates.setdefault(q_no, []).append(question)

        chunks: list[Chunk] = []
        for q_no in sorted(candidates):
            question = max(candidates[q_no], key=self._english_score)
            section = self._section_for_question(q_no)
            qtype, marks = self._type_and_marks(q_no)
            metadata: dict[str, Any] = {
                "source_type": "pyq",
                "paper_level": info.level,
                "paper_code": info.code,
                "language": "english",
                "question_no": q_no,
                "question_type": qtype,
                "marks": marks,
                "retrieval_role": "exam_pattern",
            }
            chunks.append(Chunk(
                text=question,
                source=source,
                chapter=f"CBSE Class 10 Mathematics PYQ {info.level.title()}",
                section=section,
                chunk_id=f"{source}::{info.level}::{q_no:02d}::{hash(question) % 10**8}",
                metadata=metadata,
            ))
        return chunks

    def _english_score(self, text: str) -> int:
        latin_words = re.findall(r"[A-Za-z]{2,}", text)
        option_labels = len(re.findall(r"\([A-D]\)", text))
        return len(latin_words) * 20 + option_labels * 25 + len(text)

    def _trim_trailing_section_noise(self, question: str) -> str:
        next_section = SECTION_RE.search(question, 8)
        if next_section:
            question = question[:next_section.start()].strip()
        return question

    def _is_valid_question(self, question: str) -> bool:
        if len(question) < 25:
            return False
        if not re.search(r"[A-Za-z]", question):
            return False
        return True

    def _section_for_question(self, question_no: int) -> str:
        if 1 <= question_no <= 20:
            return "Section A"
        if 21 <= question_no <= 25:
            return "Section B"
        if 26 <= question_no <= 31:
            return "Section C"
        if 32 <= question_no <= 35:
            return "Section D"
        if 36 <= question_no <= 38:
            return "Section E"
        return "Unknown"

    def _type_and_marks(self, question_no: int) -> tuple[str, int]:
        if 1 <= question_no <= 18:
            return "mcq", 1
        if 19 <= question_no <= 20:
            return "assertion_reason", 1
        if 21 <= question_no <= 25:
            return "vsa", 2
        if 26 <= question_no <= 31:
            return "sa", 3
        if 32 <= question_no <= 35:
            return "la", 5
        if 36 <= question_no <= 38:
            return "case_study", 4
        return "unknown", 0

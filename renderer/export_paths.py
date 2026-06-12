from __future__ import annotations

import re
from pathlib import Path


CHAPTER_EXPORT_CODES = {
    "Real Numbers": "reals",
    "Polynomials": "polys",
    "Pair of Linear Equations in Two Variables": "pairlin",
    "Quadratic Equations": "quads",
    "Arithmetic Progressions": "ap",
    "Triangles": "triangles",
    "Coordinate Geometry": "coord",
    "Introduction to Trigonometry": "trig",
    "Some Applications of Trigonometry": "apptrig",
    "Circles": "circles",
    "Constructions": "constr",
    "Areas Related to Circles": "arcir",
    "Surface Areas and Volumes": "sav",
    "Statistics": "stats",
    "Probability": "prob",
}

QUESTION_TYPE_CODES = {
    "assertion_reason": "ar",
    "case_study": "case",
    "map_skill": "map",
}

PAPER_LEVEL_CODES = {
    "standard": "std",
    "medium": "med",
    "challenging": "chal",
}

PAPER_VARIANT_CODES = {
    "standard": "std",
    "basic": "basic",
}


def topic_code(topic: str) -> str:
    topic = str(topic).strip()
    if topic in CHAPTER_EXPORT_CODES:
        return CHAPTER_EXPORT_CODES[topic]
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")
    if not slug:
        return "paper"
    return slug[:18]


def export_basename(topic: str,
                    question_type: str | None = None,
                    count: int | None = None,
                    paper_level: str | None = None,
                    paper_variant: str | None = None,
                    paper: bool = False) -> str:
    parts = [topic_code(topic)]
    if not paper and question_type:
        parts.append(QUESTION_TYPE_CODES.get(question_type, question_type))
    if paper_level:
        parts.append(PAPER_LEVEL_CODES.get(paper_level, paper_level))
    if paper_variant:
        parts.append(PAPER_VARIANT_CODES.get(paper_variant, paper_variant))
    if not paper and count and count > 1:
        parts.append(str(count))
    return "_".join(parts)


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

from __future__ import annotations

from types import ModuleType
from typing import Any

from config.settings import normalize_subject
from syllabus import ncert_class10, ncert_class10_science, ncert_class10_sst


def get_syllabus(subject: str | None = "maths") -> ModuleType:
    subject = normalize_subject(subject)
    if subject == "science":
        return ncert_class10_science
    if subject == "sst":
        return ncert_class10_sst
    return ncert_class10


def resolve(topic: str, subject: str | None = "maths"):
    return get_syllabus(subject).resolve(topic)


def list_chapters(subject: str | None = "maths") -> list[dict[str, Any]]:
    return get_syllabus(subject).list_chapters()


def list_question_types(subject: str | None = "maths") -> list[dict[str, Any]]:
    return get_syllabus(subject).list_question_types()


def normalize_question_type(question_type: str, subject: str | None = "maths") -> str:
    return get_syllabus(subject).normalize_question_type(question_type)


def marks_for_type(question_type: str, subject: str | None = "maths") -> int:
    return get_syllabus(subject).marks_for_type(question_type)


def hardness_from_marks(marks: int, subject: str | None = "maths") -> str:
    return get_syllabus(subject).hardness_from_marks(marks)

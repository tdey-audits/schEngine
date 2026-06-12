from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from config.settings import normalize_subject
from syllabus.registry import normalize_question_type


class GenerateRequest(BaseModel):
    subject: str = Field(default="maths", pattern="^(maths|math|mathematics|science|sci)$")
    topic: str = Field(..., description="Chapter or topic name")
    question_type: str = Field(
        default="sa",
        pattern="^(mcq|assertion_reason|vsa|sa|la|case_study)$",
    )
    marks: int | None = Field(default=None, ge=1, le=5)
    count: int = Field(default=1, ge=1, le=10)
    difficulty: str | None = Field(
        default=None,
        pattern="^(simple|medium|hard)$",
    )
    paper_level: str | None = Field(
        default="standard",
        pattern="^(standard|medium|challenging)$",
        description="Overall paper difficulty band",
    )
    paper_variant: str | None = Field(
        default="standard",
        pattern="^(standard|basic)$",
        description="CBSE Maths Basic/Standard variant for PYQ pattern retrieval",
    )
    use_pyq_patterns: bool = Field(
        default=True,
        description="Use PYQ corpus as exam-pattern context",
    )

    @field_validator("question_type", mode="before")
    @classmethod
    def normalize_question_type_field(cls, value):
        return normalize_question_type(value)

    @field_validator("subject", mode="before")
    @classmethod
    def normalize_subject_field(cls, value):
        return normalize_subject(value)


class GenerateResponse(BaseModel):
    questions: list[dict[str, Any]]
    count: int
    generated_at: datetime = Field(default_factory=datetime.now)


class ExportRequest(BaseModel):
    questions: list[dict[str, Any]] = Field(..., min_length=1)
    title: str = "CBSE Class 10 Mathematics"
    subject: str = Field(default="maths", pattern="^(maths|math|mathematics|science|sci)$")
    instructions: str | None = None
    time_allowed: str = "3 Hours"
    max_marks: str = "80"
    generation_id: str | None = Field(default=None, description="Generation ID for PDF filename")

    @field_validator("subject", mode="before")
    @classmethod
    def normalize_subject_field(cls, value):
        return normalize_subject(value)


class HealthResponse(BaseModel):
    status: str = "ok"
    chapters: list[dict[str, Any]] = []


class ChapterListResponse(BaseModel):
    chapters: list[dict[str, Any]]


class QuestionTypeResponse(BaseModel):
    types: list[dict[str, Any]]

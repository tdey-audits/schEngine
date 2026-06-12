import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from api.schemas import (
    ExportRequest, GenerateRequest, GenerateResponse,
    ChapterListResponse, HealthResponse, QuestionTypeResponse,
)
from generator.generator import QuestionGenerator
from renderer.latex_renderer import CBSELaTeXRenderer
from config.settings import normalize_subject
from syllabus.registry import list_chapters, list_question_types
from validator.validator import Validator

logger = logging.getLogger(__name__)

router = APIRouter()
generator = QuestionGenerator()
validator = Validator()


@router.get("/health", response_model=HealthResponse)
async def health(subject: str = Query(default="maths")):
    subject = normalize_subject(subject)
    return HealthResponse(
        status="ok",
        chapters=list_chapters(subject),
    )


@router.get("/chapters", response_model=ChapterListResponse)
async def chapters(subject: str = Query(default="maths")):
    subject = normalize_subject(subject)
    return ChapterListResponse(chapters=list_chapters(subject))


@router.get("/question-types", response_model=QuestionTypeResponse)
async def question_types(subject: str = Query(default="maths")):
    subject = normalize_subject(subject)
    return QuestionTypeResponse(types=list_question_types(subject))


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    try:
        questions = generator.generate(
            topic=req.topic,
            question_type=req.question_type,
            marks=req.marks,
            count=req.count,
            difficulty=req.difficulty,
            paper_level=req.paper_level,
            paper_variant=req.paper_variant,
            use_pyq_patterns=req.use_pyq_patterns,
            subject=req.subject,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    validated = validator.validate_batch(_with_subject(questions, req.subject))
    rejected = len(questions) - len(validated)
    if rejected:
        logger.warning(f"{rejected} questions failed validation")

    return GenerateResponse(
        questions=validated,
        count=len(validated),
    )


@router.post("/export/question-paper")
async def export_question_paper(req: ExportRequest):
    return _export_pdf(req, kind="question-paper")


@router.post("/export/answer-key")
async def export_answer_key(req: ExportRequest):
    return _export_pdf(req, kind="answer-key")


def _export_pdf(req: ExportRequest, kind: str):
    validated = validator.validate_batch(_with_subject(req.questions, req.subject))
    if not validated:
        raise HTTPException(status_code=422, detail="No valid questions available for export")

    try:
        renderer = CBSELaTeXRenderer(output_dir="pdfs")
        gen_id = req.generation_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{gen_id}_{kind.replace('-', '_')}"
        if kind == "question-paper":
            path = renderer.render_question_paper(
                validated,
                title=req.title,
                instructions=req.instructions,
                time_allowed=req.time_allowed,
                max_marks=req.max_marks,
                output_name=output_name,
            )
            filename = f"{gen_id}_question_paper.pdf"
        else:
            path = renderer.render_solution_booklet(
                validated,
                title=f"{req.title} - Answer Key",
                output_name=output_name,
            )
            filename = f"{gen_id}_answer_key.pdf"
    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

    pdf_path = Path(path)
    if pdf_path.suffix.lower() != ".pdf" or not pdf_path.exists():
        raise HTTPException(status_code=500, detail="PDF compilation failed")
    return FileResponse(pdf_path, media_type="application/pdf", filename=filename)


def _with_subject(questions: list[dict], subject: str) -> list[dict]:
    rows = []
    for question in questions:
        row = dict(question)
        metadata = dict(row.get("metadata") or {})
        metadata.setdefault("subject", subject)
        row["metadata"] = metadata
        rows.append(row)
    return rows

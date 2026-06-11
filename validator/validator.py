import re
from typing import Any

from renderer.diagrams import PDFDiagramRenderer
from syllabus.ncert_class10 import normalize_question_type

VALID_TYPES = {"mcq", "assertion_reason", "vsa", "sa", "la", "case_study"}
MARKS_RANGE = (1, 5)
VALID_HARDNESS = {"simple", "medium", "hard"}
OPTION_LABELS = {"(A)", "(B)", "(C)", "(D)"}


class Validator:
    LATEX_RE = re.compile(r"\$+[^$]+\$+")

    def __init__(self):
        self.diagram_renderer = PDFDiagramRenderer("/tmp/schengine-diagram-validation")

    def validate(self, question: dict[str, Any]) -> tuple[bool, list[str]]:
        errors = []

        qtype = normalize_question_type(question.get("type", ""))
        if qtype:
            question["type"] = qtype

        diagram_errors = self.diagram_renderer.validate(question.get("diagram"))
        if diagram_errors:
            question.setdefault("metadata", {})["diagram_validation_errors"] = diagram_errors
            question.pop("diagram", None)

        if qtype == "case_study":
            sub_questions = question.get("questions")
            if not sub_questions or not isinstance(sub_questions, list):
                errors.append("case_study must have 'questions' array")
            else:
                for i, sq in enumerate(sub_questions):
                    sub_valid, sub_errs = self._validate_case_sub(sq)
                    if not sub_valid:
                        errors.append(f"sub-question {i+1}: {'; '.join(sub_errs)}")
            if not question.get("question", "").strip():
                errors.append("case_study missing scenario paragraph")
            return len(errors) == 0, errors

        required = ["question", "answer", "topic"]
        for field in required:
            if field not in question or not question[field]:
                errors.append(f"Missing required field: {field}")

        if qtype not in VALID_TYPES:
            errors.append(f"Invalid type: {qtype}. Must be one of {VALID_TYPES}")

        marks = question.get("marks", 0)
        if not isinstance(marks, int) or marks < MARKS_RANGE[0] or marks > MARKS_RANGE[1]:
            errors.append(f"Marks must be 1-5, got {marks}")

        difficulty = question.get("difficulty", "")
        if difficulty not in VALID_HARDNESS:
            errors.append(f"Difficulty must be simple/medium/hard, got {difficulty}")

        if qtype == "mcq":
            options = question.get("options")
            if not options or not isinstance(options, list) or len(options) != 4:
                errors.append("MCQ must have exactly 4 options")
            elif len({str(o).strip() for o in options}) != 4:
                errors.append("MCQ options are not all distinct")
            answer_label = str(question.get("answer", "")).strip()[:3]
            if answer_label not in OPTION_LABELS:
                errors.append(f"MCQ answer must start with (A)/(B)/(C)/(D), got {question.get('answer')!r}")

        if qtype == "assertion_reason":
            answer_label = str(question.get("answer", "")).strip()[:3]
            if answer_label not in OPTION_LABELS:
                errors.append(f"Assertion-Reason answer must be (A)/(B)/(C)/(D), got {question.get('answer')!r}")

        q_text = question.get("question", "")
        if len(str(q_text).strip()) < 15:
            errors.append("Question too short (< 15 chars)")

        if qtype in ("vsa", "sa", "la"):
            if not self.LATEX_RE.search(str(q_text)):
                question.setdefault("metadata", {}).setdefault("validation_warnings", []).append(
                    "Question has no LaTeX math"
                )

        solution = question.get("solution", {})
        if isinstance(solution, dict):
            steps = solution.get("steps", [])
            if not steps:
                errors.append("Solution has no steps")
        elif qtype not in ("mcq", "assertion_reason", "vsa"):
            errors.append("Solution must be a dict with 'steps'")

        return len(errors) == 0, errors

    def _validate_case_sub(self, sq: dict[str, Any]) -> tuple[bool, list[str]]:
        errs = []
        if not sq.get("question", "").strip():
            errs.append("missing question")
        if not sq.get("answer", "").strip():
            errs.append("missing answer")
        st = normalize_question_type(sq.get("type", ""))
        if st:
            sq["type"] = st
        if st and st not in {"mcq", "vsa", "sa"}:
            errs.append(f"invalid sub-type: {st}")
        if st == "mcq" and (not sq.get("options") or len(sq.get("options", [])) != 4):
            errs.append("MCQ sub-question needs 4 options")
        diagram_errors = self.diagram_renderer.validate(sq.get("diagram"))
        if diagram_errors:
            sq.setdefault("metadata", {})["diagram_validation_errors"] = diagram_errors
            sq.pop("diagram", None)
        return len(errs) == 0, errs

    def validate_batch(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for q in questions:
            is_valid, errs = self.validate(q)
            q["_valid"] = is_valid
            q["_validation_errors"] = errs
        return [q for q in questions if q.get("_valid")]

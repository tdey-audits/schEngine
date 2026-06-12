#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.generator import QuestionGenerator
from renderer.export_paths import ensure_dir, export_basename, topic_code
from renderer.latex_renderer import CBSELaTeXRenderer
from syllabus.registry import list_chapters, normalize_question_type


TYPES = ["mcq", "assertion_reason", "vsa", "sa", "la", "case_study"]
TARGET_PER_TYPE = 5
DIFFICULTY_BY_TYPE = {
    "mcq": "medium",
    "assertion_reason": "medium",
    "vsa": "medium",
    "sa": "hard",
    "la": "hard",
    "case_study": "hard",
}


def is_valid(question: dict, expected_type: str) -> bool:
    qtype = normalize_question_type(question.get("type") or expected_type)
    if qtype != expected_type:
        return False
    text = str(question.get("question", "")).strip()
    if not text:
        return False
    if expected_type == "assertion_reason":
        return "Assertion" in text and "Reason" in text
    if expected_type == "case_study":
        sub_questions = question.get("questions", [])
        return isinstance(sub_questions, list) and len(sub_questions) >= 4
    if expected_type == "mcq":
        options = question.get("options", [])
        return isinstance(options, list) and len(options) == 4
    return True


def dedupe_key(question: dict) -> str:
    return re.sub(r"\s+", " ", str(question.get("question", "")).strip().lower())[:180]


def collect_questions(generator: QuestionGenerator, chapter: str, question_type: str,
                      paper_level: str, paper_variant: str) -> list[dict]:
    accepted: list[dict] = []
    seen: set[str] = set()

    for _ in range(4):
        need = TARGET_PER_TYPE - len(accepted)
        if need <= 0:
            break
        rows = generator.generate(
            topic=chapter,
            question_type=question_type,
            count=min(need, 5),
            difficulty=DIFFICULTY_BY_TYPE[question_type],
            paper_level=paper_level,
            paper_variant=paper_variant,
            use_pyq_patterns=True,
        )
        for row in rows:
            if not is_valid(row, question_type):
                continue
            key = dedupe_key(row)
            if not key or key in seen:
                continue
            seen.add(key)
            accepted.append(row)
            if len(accepted) == TARGET_PER_TYPE:
                break

    for _ in range(10):
        if len(accepted) >= TARGET_PER_TYPE:
            break
        rows = generator.generate(
            topic=chapter,
            question_type=question_type,
            count=1,
            difficulty=DIFFICULTY_BY_TYPE[question_type],
            paper_level=paper_level,
            paper_variant=paper_variant,
            use_pyq_patterns=True,
        )
        for row in rows:
            if not is_valid(row, question_type):
                continue
            key = dedupe_key(row)
            if not key or key in seen:
                continue
            seen.add(key)
            accepted.append(row)
            break

    if len(accepted) != TARGET_PER_TYPE:
        raise RuntimeError(f"{chapter} / {question_type}: expected {TARGET_PER_TYPE}, got {len(accepted)}")
    return accepted


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one 30-question paper per Class 10 Maths chapter")
    parser.add_argument("--pdf-dir", default="pdfs/batch1", help="PDF output directory")
    parser.add_argument("--meta-dir", default="output/batch1", help="Metadata output directory")
    parser.add_argument("--paper-level", default="challenging", choices=["standard", "medium", "challenging"])
    parser.add_argument("--paper-variant", default="standard", choices=["standard", "basic"])
    args = parser.parse_args()

    pdf_dir = ensure_dir(args.pdf_dir)
    meta_dir = ensure_dir(args.meta_dir)
    build_dir = ensure_dir(pdf_dir / "build")

    generator = QuestionGenerator()
    renderer = CBSELaTeXRenderer(output_dir=str(pdf_dir), build_dir=str(build_dir))

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "paper_level": args.paper_level,
        "paper_variant": args.paper_variant,
        "questions_per_type": TARGET_PER_TYPE,
        "chapters": [],
        "failures": [],
    }

    for chapter_row in list_chapters():
        chapter = chapter_row["name"]
        try:
            questions = []
            for question_type in TYPES:
                questions.extend(
                    collect_questions(generator, chapter, question_type, args.paper_level, args.paper_variant)
                )
            counts = Counter(normalize_question_type(q.get("type", "")) for q in questions)
            if any(counts.get(question_type, 0) != TARGET_PER_TYPE for question_type in TYPES):
                raise RuntimeError(f"invalid final distribution {counts}")

            base = export_basename(
                chapter,
                paper_level=args.paper_level,
                paper_variant=args.paper_variant,
                paper=True,
            )
            json_path = meta_dir / f"{base}.json"
            json_path.write_text(json.dumps(questions, indent=2))

            title = f"CBSE Class 10 Mathematics - {chapter}"
            qp_pdf, sol_pdf = renderer.render_both(questions, title=title, output_name=base)

            manifest["chapters"].append({
                "chapter": chapter,
                "code": topic_code(chapter),
                "count": len(questions),
                "types": dict(counts),
                "json": str(json_path),
                "question_pdf": str(qp_pdf),
                "solution_pdf": str(sol_pdf),
            })
        except Exception as exc:
            manifest["failures"].append({
                "chapter": chapter,
                "error": str(exc),
            })

    manifest_path = meta_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"MANIFEST: {manifest_path}")
    print(f"SUCCESS: {len(manifest['chapters'])}")
    print(f"FAILURES: {len(manifest['failures'])}")
    return 0 if not manifest["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

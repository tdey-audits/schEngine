#!/usr/bin/env python3
"""Generate CBSE-style questions from the command line."""

import json
import logging
from pathlib import Path

from generator.generator import QuestionGenerator
from renderer.export_paths import ensure_dir, export_basename
from syllabus.registry import list_question_types, list_chapters as list_syllabus_chapters
from renderer.latex_renderer import CBSELaTeXRenderer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate NCERT Class 10 questions")
    parser.add_argument("--subject", default="maths", choices=["maths", "science", "sst"],
                        help="Subject corpus/syllabus to use")
    parser.add_argument("--topic", "-t", default="Quadratic Equations",
                        help="Chapter or topic (e.g. 'Quadratic Equations')")
    parser.add_argument("--subtopic", "-s", default=None, help="Specific subtopic")
    parser.add_argument("--type", "-T", default="sa",
                        choices=["mcq", "assertion_reason", "vsa", "sa", "la", "case_study", "map_skill"],
                        help="Question type (see --list-types)")
    parser.add_argument("--marks", "-m", type=int, default=None, choices=[1, 2, 3, 4, 5],
                        help="Marks (auto-derived from type if omitted)")
    parser.add_argument("--difficulty", "-d", default=None,
                        choices=["simple", "medium", "hard"],
                        help="Difficulty level (auto-derived from marks if omitted)")
    parser.add_argument("--paper-level", default="standard",
                        choices=["standard", "medium", "challenging"],
                        help="Overall paper difficulty band")
    parser.add_argument("--paper-variant", default="standard",
                        choices=["standard", "basic"],
                        help="CBSE Maths Basic/Standard variant for PYQ pattern context")
    parser.add_argument("--no-pyq-patterns", action="store_true",
                        help="Disable PYQ pattern retrieval")
    parser.add_argument("--count", "-c", type=int, default=1, help="Number of questions")
    parser.add_argument("--chapter", "-C", type=int, default=None, help="Chapter number")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file")
    parser.add_argument("--pdf", action="store_true", help="Render to PDF (LaTeX)")
    parser.add_argument("--title", default=None,
                        help="Title for the question paper")
    parser.add_argument("--list-types", action="store_true", help="List available question types")
    parser.add_argument("--list-chapters", action="store_true", help="List chapters")
    parser.add_argument("--paper", action="store_true", help="Generate a full mixed paper (one of each type)")

    args = parser.parse_args()

    if args.list_types:
        for qt in list_question_types(args.subject):
            print(f"  {qt['type']:20s}  {qt['marks']} mark(s)  — {qt['description']}")
        return

    if args.list_chapters:
        for ch in list_syllabus_chapters(args.subject):
            subs = ", ".join(ch["subtopics"][:3])
            print(f"  Ch {ch['number']:2d}: {ch['name']:40s}  [{subs}{', ...' if len(ch['subtopics']) > 3 else ''}]")
        return

    gen = QuestionGenerator()
    title_by_subject = {
        "maths": "CBSE Class 10 Mathematics",
        "science": "CBSE Class 10 Science",
        "sst": "CBSE Class 10 Social Science",
    }
    default_title = args.title or title_by_subject[args.subject]

    if args.paper:
        chapters = [ch["name"] for ch in list_syllabus_chapters(args.subject)]
        types = [qt["type"] for qt in list_question_types(args.subject)]
        all_qs = []
        for i, (ch, tp) in enumerate(zip(chapters, types)):
            try:
                qs = gen.generate(
                    ch, tp, count=1,
                    difficulty={"mcq": "simple", "assertion_reason": "simple",
                                "vsa": "medium", "sa": "medium",
                                "la": "hard", "case_study": "hard",
                                "map_skill": "medium"}.get(tp),
                    paper_level=args.paper_level,
                    paper_variant=args.paper_variant,
                    use_pyq_patterns=not args.no_pyq_patterns,
                    subject=args.subject,
                )
                all_qs.extend(qs)
            except Exception as e:
                logger.warning(f"Failed {ch}/{tp}: {e}")
        questions = all_qs
        print(json.dumps(questions, indent=2))

        if args.pdf or args.output:
            if args.output:
                Path(args.output).write_text(json.dumps(questions, indent=2))
                print(f"\nJSON saved: {args.output}")
            if args.pdf:
                pdf_dir = ensure_dir("pdfs")
                renderer = CBSELaTeXRenderer(output_dir=str(pdf_dir))
                base = export_basename(
                    f"cbse_class10_{args.subject}",
                    paper_level=args.paper_level,
                    paper_variant=args.paper_variant if args.subject == "maths" else None,
                    paper=True,
                )
                qp, sb = renderer.render_both(questions, title=default_title, output_name=base)
                print(f"\nPDF: {qp}")
                print(f"Solutions: {sb}")
        return

    if args.chapter is not None:
        questions = gen.generate_from_syllabus(
            chapter_number=args.chapter,
            subtopic_name=args.subtopic,
            question_type=args.type,
            marks=args.marks,
            count=args.count,
            difficulty=args.difficulty,
            paper_level=args.paper_level,
            paper_variant=args.paper_variant,
            use_pyq_patterns=not args.no_pyq_patterns,
            subject=args.subject,
        )
    else:
        topic = args.topic
        if args.subtopic:
            topic = f"{args.topic} {args.subtopic}"
        questions = gen.generate(
            topic=topic,
            question_type=args.type,
            marks=args.marks,
            count=args.count,
            difficulty=args.difficulty,
            paper_level=args.paper_level,
            paper_variant=args.paper_variant,
            use_pyq_patterns=not args.no_pyq_patterns,
            subject=args.subject,
        )

    print(json.dumps(questions, indent=2))

    topic_name = topic if args.chapter is None else (
        next((ch["name"] for ch in list_syllabus_chapters(args.subject) if ch["number"] == args.chapter), "chapter")
    )
    base = export_basename(
        topic_name,
        question_type=args.type,
        count=args.count,
        paper_level=args.paper_level,
        paper_variant=args.paper_variant if args.subject == "maths" else None,
        paper=args.paper,
    )

    if args.output:
        path = Path(args.output)
    else:
        meta_dir = ensure_dir("output")
        path = meta_dir / f"{base}.json"
    path.write_text(json.dumps(questions, indent=2))
    print(f"\nJSON saved: {path}")

    if args.pdf:
        pdf_dir = ensure_dir("pdfs")
        renderer = CBSELaTeXRenderer(output_dir=str(pdf_dir))
        qp, sb = renderer.render_both(questions, title=default_title, output_name=base)
        print(f"\nPDF: {qp}")
        print(f"Solutions: {sb}")


if __name__ == "__main__":
    main()

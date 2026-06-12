from datetime import datetime
from pathlib import Path
from typing import Any

from syllabus.registry import normalize_question_type


def render_question_paper(questions: list[dict[str, Any]],
                          title: str = "CBSE Class 10 Mathematics",
                          output_path: str | None = None) -> str:
    lines = [
        f"# {title}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total Questions:** {len(questions)}",
        "---",
        "",
    ]

    grouped: dict[str, list[dict[str, Any]]] = {}
    for q in questions:
        topic = q.get("topic", "General")
        grouped.setdefault(topic, []).append(q)

    for topic, qs in grouped.items():
        lines.append(f"## {topic}")
        lines.append("")
        for i, q in enumerate(qs, 1):
            marks = q.get("marks", 4)
            qtype = normalize_question_type(q.get("type", "sa"))
            lines.append(f"### Question {i} [{marks} marks, {qtype}]")
            lines.append("")
            lines.append(str(q.get("question", "")))
            lines.append("")

            if qtype == "mcq":
                options = q.get("options", [])
                for label in ("(A)", "(B)", "(C)", "(D)"):
                    if label in options:
                        lines.append(f"- {label} {options[label]}")
                    elif options:
                        lines.append(f"- {options.pop(0)}")
                lines.append("")

            lines.append("---")
            lines.append("")

    text = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(text)

    return text


def render_solution_booklet(questions: list[dict[str, Any]],
                            title: str = "CBSE Class 10 Mathematics — Solutions",
                            output_path: str | None = None) -> str:
    lines = [
        f"# {title}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "---",
        "",
    ]

    for i, q in enumerate(questions, 1):
        lines.append(f"## Question {i}")
        lines.append("")
        lines.append(str(q.get("question", "")))
        lines.append("")
        lines.append("**Answer:** " + str(q.get("answer", "")))
        lines.append("")

        solution = q.get("solution", {})
        if isinstance(solution, dict):
            steps = solution.get("steps", [])
            if steps:
                lines.append("**Solution:**")
                for j, step in enumerate(steps, 1):
                    lines.append(f"{j}. {step}")
                lines.append("")
            derivation = solution.get("derivation", "")
            if derivation:
                lines.append("**Derivation:**")
                lines.append("```")
                lines.append(str(derivation))
                lines.append("```")
                lines.append("")

        lines.append("---")
        lines.append("")

    text = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(text)

    return text


def render_both(questions: list[dict[str, Any]], title: str = "CBSE Class 10 Mathematics",
                output_dir: str = "output") -> tuple[Path, Path]:
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    qp_path = output_dir_path / f"question_paper_{ts}.md"
    render_question_paper(questions, title, str(qp_path))

    sb_path = output_dir_path / f"solutions_{ts}.md"
    render_solution_booklet(questions, f"{title} — Solutions", str(sb_path))

    return qp_path, sb_path

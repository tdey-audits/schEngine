"""LaTeX renderer for CBSE Class 10 Mathematics question papers.

Generates authentic CBSE-style question papers and solution booklets
using the `exam` document class, compiled via pdflatex.
"""

import logging
import random
import re
import shutil
import string
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import Any

from renderer.diagrams import PDFDiagramRenderer
from syllabus.ncert_class10 import normalize_question_type

logger = logging.getLogger(__name__)


class CBSELaTeXRenderer:
    MATH_ENV_RE = re.compile(r"\\begin\{(?:align\*?|equation\*?|gather\*?|multline\*?|split)\}")
    INLINE_MATH_RE = re.compile(r"(\$\$.*?\$\$|\$.*?\$)", re.DOTALL)
    LATEX_CMD_RE = re.compile(r"\\([A-Za-z]+)")
    LATEX_SPECIALS = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                      "^": r"\textasciicircum{}", "~": r"\textasciitilde{}"}

    # Unicode → LaTeX. Shared by the math-mode converter (emits bare commands)
    # and the text-mode escaper (wraps each token in $...$ so it is valid in
    # running text). Keeping one source of truth avoids the old drift where a
    # symbol like ⇒ was handled in one place but not the other.
    SUB_MAP = {
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
        'ₙ': 'n',
    }
    SUP_MAP = {
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
        'ⁿ': 'n',
    }
    SYM_MAP = {
        '×': r'\times', '÷': r'\div', '→': r'\to',
        '⇒': r'\Rightarrow', '⇐': r'\Leftarrow', '⇔': r'\Leftrightarrow',
        '≈': r'\approx', '≠': r'\neq', '≤': r'\leq', '≥': r'\geq',
        '∞': r'\infty', '√': r'\sqrt', '∑': r'\sum', '∏': r'\prod',
        '∫': r'\int', '∴': r'\therefore', '∵': r'\because',
        '±': r'\pm', '∓': r'\mp', '⋅': r'\cdot', '·': r'\cdot',
        '∠': r'\angle', '△': r'\triangle', '∼': r'\sim',
        '≅': r'\cong', '≡': r'\equiv', '°': r'^{\circ}',
        '⊥': r'\perp', '∥': r'\parallel', '∝': r'\propto',
        '∈': r'\in', 'θ': r'\theta', 'π': r'\pi', 'α': r'\alpha',
        'β': r'\beta', 'γ': r'\gamma', 'λ': r'\lambda',
        'Δ': r'\Delta', 'μ': r'\mu', 'φ': r'\phi', 'ρ': r'\rho',
    }
    RUPEE = '₹'

    # Function names that are legitimately bare multi-letter tokens inside math
    # mode (rendered upright by LaTeX). These must NOT be wrapped in \text.
    MATH_FUNCS = {
        "sin", "cos", "tan", "cot", "sec", "csc",
        "sinh", "cosh", "tanh", "coth",
        "log", "ln", "lg", "lim", "exp", "det", "deg", "dim",
        "gcd", "lcm", "max", "min", "mod", "arg",
        "arcsin", "arccos", "arctan",
    }

    TYPE_LABELS = {
        "mcq": "Multiple Choice Question",
        "assertion_reason": "Assertion-Reason",
        "vsa": "Very Short Answer",
        "sa": "Short Answer",
        "la": "Long Answer",
        "case_study": "Case Study",
    }

    def __init__(self, output_dir: str = "pdfs", build_dir: str | None = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.build_dir = Path(build_dir) if build_dir else self.output_dir / "build"
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.diagram_renderer = PDFDiagramRenderer(self.build_dir / "diagrams")
        self._diagram_counter = 0
        self._check_pdflatex()

    def _check_pdflatex(self):
        self.pdflatex_path = None
        candidates = [
            "pdflatex",
            "/home/user/texlive/2026/bin/x86_64-linux/pdflatex",
            "/usr/bin/pdflatex",
            "/usr/local/bin/pdflatex",
        ]
        for c in candidates:
            try:
                r = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    self.pdflatex_path = c
                    return
            except FileNotFoundError:
                continue
        logger.warning("pdflatex not found. PDF compilation disabled.")

    # ── Public API ──────────────────────────────────────────────────────

    def render_question_paper(self, questions: list[dict[str, Any]],
                              title: str = "CBSE Class 10 Mathematics",
                              instructions: str | None = None,
                              time_allowed: str = "3 Hours",
                              max_marks: str = "80",
                              output_name: str | None = None) -> Path:
        tex = self._build_question_paper_tex(questions, title, instructions, time_allowed, max_marks)
        return self._write_and_compile(tex, "qs", output_name)

    def render_solution_booklet(self, questions: list[dict[str, Any]],
                                title: str = "CBSE Class 10 Mathematics — Solutions",
                                output_name: str | None = None) -> Path:
        tex = self._build_solution_booklet_tex(questions, title)
        return self._write_and_compile(tex, "sol", output_name)

    def render_both(self, questions: list[dict[str, Any]],
                    title: str = "CBSE Class 10 Mathematics",
                    output_name: str | None = None,
                    **kwargs) -> tuple[Path, Path]:
        qp_name = f"{output_name}_qp" if output_name else None
        sb_name = f"{output_name}_sol" if output_name else None
        qp = self.render_question_paper(questions, title, output_name=qp_name, **kwargs)
        sb = self.render_solution_booklet(questions, f"{title} — Solutions", output_name=sb_name)
        return qp, sb

    # ── TeX building ───────────────────────────────────────────────────

    def _build_question_paper_tex(self, questions: list[dict], title: str,
                                   instructions: str | None, time_allowed: str,
                                   max_marks: str) -> str:
        body_parts = [
            self._general_instructions(instructions, len(questions)),
            "\\bigskip",
        ]

        grouped = self._group_by_type(questions)
        section_labels = {
            "mcq": "A",
            "assertion_reason": "A",
            "vsa": "B",
            "sa": "C",
            "la": "D",
            "case_study": "E",
        }
        section_names = {
            "A": r"Section A: Multiple Choice \& Assertion-Reason (1 mark each)",
            "B": "Section B: Very Short Answer (2 marks each)",
            "C": "Section C: Short Answer (3 marks each)",
            "D": "Section D: Long Answer (4-5 marks each)",
            "E": "Section E: Case Study (4 marks each)",
        }

        for sec_letter in ("A", "B", "C", "D", "E"):
            sec_types = [t for t in grouped if section_labels.get(t) == sec_letter]
            sec_questions = []
            for t in sec_types:
                for q in grouped.get(t, []):
                    sec_questions.append(q)

            if not sec_questions:
                continue

            body_parts.append("\\noindent\\textbf{\\large " + section_names[sec_letter] + "}")
            body_parts.append("")
            body_parts.append("\\begin{questions}")

            for i, q in enumerate(sec_questions, 1):
                body_parts.append(self._format_question(q, i))

            body_parts.append("\\end{questions}")
            body_parts.append("\\bigskip")

        body = "\n".join(body_parts)
        return self._wrap_paper(title, max_marks, time_allowed, body)

    def _build_solution_booklet_tex(self, questions: list[dict], title: str) -> str:
        body_parts = ["\\begin{questions}"]
        for i, q in enumerate(questions, 1):
            body_parts.append(self._format_solution(q, i))
        body_parts.append("\\end{questions}")
        body = "\n".join(body_parts)
        return self._wrap_booklet(title, body)

    # ── Question formatting ───────────────────────────────────────────

    def _format_question(self, q: dict, number: int) -> str:
        qtype = normalize_question_type(q.get("type", "sa"))
        marks = q.get("marks", 4)
        q_text = self._escape_latex(q.get("question", ""))
        answer = self._escape_latex(q.get("answer", ""))

        parts = [f"\\question[{marks}] {q_text}"]
        diagram_tex = self._format_diagram(q.get("diagram"))
        if diagram_tex:
            parts.append(diagram_tex)

        if qtype == "mcq":
            options = q.get("options", [])
            parts.append("\\begin{enumerate}[label=(\\Alph*)]")
            for opt in options:
                parts.append(f"  \\item {self._escape_latex(opt)}")
            parts.append("\\end{enumerate}")

        elif qtype == "assertion_reason":
            ar_options = [
                "(A) Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A)",
                "(B) Both Assertion (A) and Reason (R) are true but Reason (R) is NOT the correct explanation of Assertion (A)",
                "(C) Assertion (A) is true but Reason (R) is false",
                "(D) Assertion (A) is false but Reason (R) is true",
            ]
            parts.append("\\begin{enumerate}[label=(\\Alph*)]")
            for opt in ar_options:
                parts.append(f"  \\item {self._escape_latex(opt)}")
            parts.append("\\end{enumerate}")

        elif qtype == "case_study":
            sub_questions = q.get("questions", [])
            if sub_questions:
                parts.append("\\vspace{0.2cm}")
                parts.append("\\begin{enumerate}[label=(\\roman*)]")
                for sq in sub_questions:
                    sq_text = self._escape_latex(sq.get("question", ""))
                    parts.append(f"  \\item {sq_text}")
                    sq_diagram_tex = self._format_diagram(sq.get("diagram"))
                    if sq_diagram_tex:
                        parts.append(sq_diagram_tex)
                    if sq.get("type") == "mcq":
                        sq_opts = sq.get("options", [])
                        parts.append("  \\begin{enumerate}[label=(\\Alph*)]")
                        for o in sq_opts:
                            parts.append(f"    \\item {self._escape_latex(o)}")
                        parts.append("  \\end{enumerate}")
                parts.append("\\end{enumerate}")

        parts.append("\\vspace{0.15cm}\n")
        return "\n".join(parts)

    def _format_solution(self, q: dict, number: int) -> str:
        qtype = normalize_question_type(q.get("type", "sa"))
        q_text = self._escape_latex(q.get("question", ""))
        answer_raw = q.get("answer", "")
        parts = [
            f"\\question {q_text}",
            "",
        ]
        if qtype == "case_study":
            sub_questions = q.get("questions", [])
            for sq in sub_questions:
                sq_id = sq.get("id", "")
                sq_q = self._escape_latex(sq.get("question", ""))
                sq_a = self._format_answer(sq.get("answer", ""), normalize_question_type(sq.get("type", "")))
                parts.append(f"\\textbf{{({sq_id})}} {sq_q}")
                parts.append("")
                parts.append("\\textbf{Answer:} " + sq_a)
                solution_tex = self._format_solution_content(sq)
                if solution_tex:
                    parts.append("\\textbf{Solution:}")
                    parts.append(solution_tex)
                parts.append("")
            parts.append("\\vspace{0.3cm}\n")
            return "\n".join(parts)

        answer = self._format_answer(answer_raw, qtype)
        parts.append("\\textbf{Answer:} " + answer)
        parts.append("")

        solution_tex = self._format_solution_content(q)
        if solution_tex:
            parts.append("\\textbf{Solution:}")
            parts.append(solution_tex)

        parts.append("\\vspace{0.3cm}\n")
        return "\n".join(parts)

    def _format_solution_content(self, item: dict) -> str:
        solution = item.get("solution", {})
        if isinstance(solution, dict):
            parts: list[str] = []
            steps = solution.get("steps", [])
            if steps:
                parts.append("\\begin{enumerate}[leftmargin=*, itemsep=0.25cm]")
                for step in steps:
                    parts.append("  \\item " + self._format_solution_step(step))
                parts.append("\\end{enumerate}")
            derivation = solution.get("derivation", "")
            if derivation:
                parts.append(self._format_derivation_or_fallback(str(derivation)))
            return "\n\n".join(part for part in parts if part)

        raw = str(solution or "").strip()
        if not raw:
            return ""
        if self._is_severely_broken_solution(raw):
            return self._format_plaintext_step_fallback(raw)
        try:
            escaped = self._escape_latex(raw)
        except Exception:
            return self._format_plaintext_step_fallback(raw)
        if self._has_broken_math(escaped):
            return self._format_plaintext_step_fallback(raw)
        return self._beautify_solution(escaped)

    def _format_derivation_or_fallback(self, derivation: str) -> str:
        try:
            rendered = self._format_derivation(derivation)
        except Exception:
            return self._format_plaintext_step_fallback(derivation)
        if self._has_broken_math(rendered):
            return self._format_plaintext_step_fallback(derivation)
        return rendered

    # ── Grouping ──────────────────────────────────────────────────────

    def _group_by_type(self, questions: list[dict]) -> OrderedDict:
        groups: OrderedDict = OrderedDict()
        type_order = ["mcq", "assertion_reason", "vsa", "sa", "la", "case_study"]
        for t in type_order:
            groups[t] = []
        for q in questions:
            qtype = normalize_question_type(q.get("type", "sa"))
            if qtype not in groups:
                groups[qtype] = []
            groups[qtype].append(q)
        return groups

    # ── Wrappers ─────────────────────────────────────────────────────

    def _wrap_paper(self, title: str, max_marks: str, time_allowed: str, body: str) -> str:
        return self._preamble() + f"""
\\begin{{document}}

\\thispagestyle{{empty}}
\\begin{{center}}
  \\textbf{{\\LARGE {self._escape_latex(title)}}} \\\\[0.3cm]
  \\textbf{{Time Allowed: {time_allowed}}} \\hfill \\textbf{{Maximum Marks: {max_marks}}} \\\\[0.3cm]
  \\rule{{\\textwidth}}{{0.5pt}}
\\end{{center}}

\\vspace{{0.3cm}}

{body}

\\end{{document}}
"""

    def _wrap_booklet(self, title: str, body: str) -> str:
        return self._preamble() + f"""
\\begin{{document}}

\\thispagestyle{{empty}}
\\begin{{center}}
  \\textbf{{\\LARGE {self._escape_latex(title)}}} \\\\[0.3cm]
  \\rule{{\\textwidth}}{{0.5pt}}
\\end{{center}}

\\vspace{{0.3cm}}

{body}

\\end{{document}}
"""

    def _preamble(self) -> str:
        return r"""\documentclass[12pt,a4paper]{exam}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{xcolor}
\geometry{a4paper, top=2cm, bottom=2cm, left=2.5cm, right=2.5cm}
\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}
\renewcommand{\thequestion}{\textbf{\arabic{question}}}
\renewcommand{\questionlabel}{\thequestion.}
\pointname{ marks}
\pointsdroppedatright
\bracketedpoints
\setlength{\parindent}{0pt}
\setlength{\emergencystretch}{3em}
\allowdisplaybreaks
\newsavebox{\schmathbox}
\newcommand{\fitmath}[1]{%
  \sbox{\schmathbox}{$\displaystyle #1$}%
  \ifdim\wd\schmathbox>\linewidth
    \resizebox{\linewidth}{!}{\usebox{\schmathbox}}%
  \else
    \usebox{\schmathbox}%
  \fi}
"""

    def _format_diagram(self, diagram: Any) -> str:
        if not diagram:
            return ""
        try:
            self._diagram_counter += 1
            asset = self.diagram_renderer.render_asset(diagram, f"diagram_{self._diagram_counter:03d}")
        except Exception as exc:
            logger.warning(f"Skipping invalid diagram: {exc}")
            return "% Diagram skipped: invalid diagram spec"
        if not asset:
            return ""
        return (
            "\n\\begin{center}\n"
            f"\\includegraphics[width=0.48\\textwidth]{{{asset.as_posix()}}}\n"
            "\\end{center}\n"
        )

    def _general_instructions(self, instructions: str | None, count: int = 0) -> str:
        if instructions:
            return "\\noindent\\textbf{General Instructions:}\n" + instructions
        # Use the real question count; literal "___" underscores trigger math mode.
        count_str = str(count) if count else "all"
        return f"""\\noindent\\textbf{{General Instructions:}}
\\begin{{enumerate}}
  \\item {{\\normalfont\\normalcolor This question paper contains {count_str} questions. All questions are compulsory.}}
  \\item {{\\normalfont\\normalcolor Questions are grouped into sections A through E.}}
  \\item {{\\normalfont\\normalcolor Use of calculators is NOT permitted.}}
\\end{{enumerate}}"""

    # ── LaTeX utilities ────────────────────────────────────────────────

    def _repair_tex(self, tex: str) -> str:
        # NOTE: previously this ran regexes with [^$]+ over the whole document to
        # fix "$x$^2"-style superscripts. Because [^$] crosses newlines, they
        # matched huge spans and corrupted valid math. Superscripts are now
        # handled correctly at the source, so we only keep delimiter balancing.
        protected = tex.replace("\\\\[", "<<<LB>>>")
        opens = protected.count("\\[")
        closes = protected.count("\\]")
        if opens > closes:
            tex += "\n\\]" * (opens - closes)
        opens_dollar = tex.count("$")
        if opens_dollar % 2 != 0:
            tex += "$"
        return tex

    def _write_and_compile(self, tex: str, prefix: str, output_name: str | None = None) -> Path:
        tag = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        name = output_name or f"{prefix}_{tag}"

        tex = self._repair_tex(tex)
        tex_path = self.build_dir / f"{name}.tex"
        tex_path.write_text(tex)

        if self.pdflatex_path:
            self._compile_pdf(tex_path)
            pdf_src = tex_path.with_suffix(".pdf")
            pdf_dst = self.output_dir / pdf_src.name
            if pdf_src.exists():
                shutil.copy2(pdf_src, pdf_dst)
                logger.info(f"PDF: {pdf_dst}")
                self._clean_build_files(name)
                self._clean_output_intermediates()
                return pdf_dst

        self._clean_output_intermediates()
        return self.output_dir / f"{name}.tex"

    def _compile_pdf(self, tex_path: Path) -> Path | None:
        if not self.pdflatex_path:
            return None
        try:
            subprocess.run(
                [self.pdflatex_path, "-interaction=nonstopmode",
                 f"-output-directory={self.build_dir}", str(tex_path)],
                capture_output=True, text=False, timeout=60,
            )
            pdf = tex_path.with_suffix(".pdf")
            if pdf.exists() and pdf.stat().st_size > 0:
                return pdf
        except Exception as e:
            logger.error(f"PDF compilation failed: {e}")
        return None

    def _clean_build_files(self, name: str):
        for ext in (".tex", ".aux", ".log", ".out", ".pdf"):
            p = self.build_dir / f"{name}{ext}"
            if p.exists():
                p.unlink()

    def _clean_output_intermediates(self):
        for f in self.output_dir.iterdir():
            if f.suffix in (".tex", ".aux", ".log", ".out"):
                f.unlink()

    def _escape_latex(self, text: str) -> str:
        if not text:
            return ""
        text = self._normalize_latex_text(text)
        if self._contains_markdown_table(text):
            return self._format_mixed_text_with_tables(text)
        return self._escape_mixed_with_math(text)

    def _format_mixed_text_with_tables(self, text: str) -> str:
        blocks = self._split_table_blocks(self._normalize_latex_text(text))
        parts: list[str] = []
        for block_type, payload in blocks:
            if block_type == "table":
                parts.append(self._format_markdown_table(payload))
            else:
                escaped = self._escape_mixed_with_math(payload)
                if escaped:
                    parts.append(escaped)
        return "\n\n".join(part for part in parts if part)

    def _contains_markdown_table(self, text: str) -> bool:
        lines = self._normalize_latex_text(text).splitlines()
        return any(self._looks_like_table_start(lines, i) for i in range(max(0, len(lines) - 1)))

    def _split_table_blocks(self, text: str) -> list[tuple[str, Any]]:
        lines = text.splitlines()
        blocks: list[tuple[str, Any]] = []
        buffer: list[str] = []

        def flush_text():
            source = "\n".join(buffer).strip()
            if source:
                blocks.append(("text", source))
            buffer.clear()

        i = 0
        while i < len(lines):
            if self._looks_like_table_start(lines, i):
                flush_text()
                table_lines = [lines[i], lines[i + 1]]
                i += 2
                while i < len(lines) and self._is_pipe_table_row(lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                rows = self._parse_markdown_table(table_lines)
                if rows:
                    blocks.append(("table", rows))
                continue
            buffer.append(lines[i])
            i += 1
        flush_text()
        return blocks

    def _looks_like_table_start(self, lines: list[str], index: int) -> bool:
        return (
            index + 1 < len(lines)
            and self._is_pipe_table_row(lines[index])
            and self._is_markdown_table_separator(lines[index + 1])
        )

    def _is_pipe_table_row(self, line: str) -> bool:
        return "|" in line and len(self._split_table_row(line)) >= 2

    def _is_markdown_table_separator(self, line: str) -> bool:
        cells = self._split_table_row(line)
        return len(cells) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)

    def _parse_markdown_table(self, lines: list[str]) -> list[list[str]]:
        rows: list[list[str]] = []
        for index, line in enumerate(lines):
            if index == 1 or not self._is_pipe_table_row(line):
                continue
            row = [cell.strip() for cell in self._split_table_row(line)]
            if len(row) >= 2:
                rows.append(row)
        return rows

    @staticmethod
    def _split_table_row(line: str) -> list[str]:
        line = re.sub(r"^\s*\|", "", line.strip())
        line = re.sub(r"\|\s*$", "", line)
        return line.split("|")

    def _format_markdown_table(self, rows: list[list[str]]) -> str:
        if not rows:
            return ""
        column_count = max(len(row) for row in rows)
        width = max(0.12, min(0.28, 0.92 / column_count))
        columns = "|" + "|".join([f"p{{{width:.2f}\\linewidth}}"] * column_count) + "|"
        lines = [
            "\\begin{center}",
            "\\small",
            "\\renewcommand{\\arraystretch}{1.2}",
            f"\\begin{{tabular}}{{{columns}}}",
            "\\hline",
        ]
        for row_index, row in enumerate(rows):
            padded = row + [""] * (column_count - len(row))
            cells = [self._escape_mixed_with_math(cell) for cell in padded]
            lines.append(" & ".join(cells) + r" \\")
            lines.append("\\hline")
            if row_index == 0 and len(rows) > 1:
                lines.append("\\hline")
        lines.extend([
            "\\end{tabular}",
            "\\normalsize",
            "\\end{center}",
        ])
        return "\n".join(lines)

    def _wrap_bare_commands(self, text: str) -> str:
        parts = []
        pos = 0
        for m in self.INLINE_MATH_RE.finditer(text):
            parts.append(text[pos:m.start()])
            parts.append(m.group(0))
            pos = m.end()
        tail = text[pos:]
        if tail and self._contains_bare_command(tail):
            tail = "$" + tail + "$"
        parts.append(tail)
        return "".join(parts)

    def _contains_bare_command(self, text: str) -> bool:
        return bool(self.LATEX_CMD_RE.search(text))

    def _normalize_latex_text(self, text: Any) -> str:
        text = "" if text is None else str(text)
        text = self._repair_control_char_latex(text)
        # Convert model/UI escaped whitespace before generic command cleanup.
        # Handle both "\n" and double-escaped "\\n" variants, while preserving
        # real LaTeX commands such as \nu, \neq, \nabla and \newline.
        protected_n_commands = r"(?!(?:u|eq|e|abla|atural|eg|i|ot|ewline|ormalsize|leq|geq|less|gtr)\b)"
        text = re.sub(r"\\\\n" + protected_n_commands, "\n", text)
        text = re.sub(r"\\\\t(?![a-z])", " ", text)
        text = re.sub(r"\\([A-Za-z]+)", lambda m: "\\" + m.group(1), text)
        text = text.replace("\\$", "$")
        text = text.replace("\\(", "$").replace("\\)", "$")
        text = text.replace("\\[", "$$").replace("\\]", "$$")
        text = text.replace("```latex", "").replace("```tex", "").replace("```", "")
        # Literal "\n"/"\t" the model sometimes emits as two characters (not real
        # whitespace) \u2014 undefined control sequences in LaTeX. Convert to real
        # whitespace. Protect lowercase-continued commands (\nu, \neq, \times,
        # \theta): a real escape is "\n"/"\t" followed by space/punct/uppercase.
        text = re.sub(r"\\n" + protected_n_commands, "\n", text)
        text = re.sub(r"\\t(?![a-z])", " ", text)
        text = re.sub(r"(?<=[0-9A-Za-z}\)\]])\s+imes\s+(?=[0-9A-Za-z\\({\[])", r" \\times ", text)
        text = text.replace("\u2212", "-").replace("\u00a0", " ")
        # NOTE: unicode\u2192LaTeX conversion is intentionally NOT done here. It is
        # context-sensitive: math mode wants bare commands, text mode wants them
        # wrapped in $...$. Done in _sanitize_math / _escape_text respectively.
        text = "".join(ch if ch in "\n\t" or ord(ch) >= 32 else " " for ch in text)
        text = re.sub(r"\\[a-zA-Z]{0,2}$", "", text)
        return text.strip()

    def _repair_control_char_latex(self, text: str) -> str:
        def replace_unicode_escape(match: re.Match) -> str:
            try:
                return chr(int(match.group(1), 16))
            except ValueError:
                return match.group(0)

        text = re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode_escape, text)
        repairs = {
            "\x0crac": r"\frac",
            "\x0corall": r"\forall",
            "\x08eta": r"\beta",
            "\x07lpha": r"\alpha",
            "\times": r"\times",
            "\text": r"\text",
            "\theta": r"\theta",
            "\tau": r"\tau",
            "\tan": r"\tan",
            "\to": r"\to",
            "\right": r"\right",
            "\rho": r"\rho",
            "\nabla": r"\nabla",
            "\neq": r"\neq",
            "\nu": r"\nu",
        }
        for broken, fixed in repairs.items():
            text = text.replace(broken, fixed)
        return text

    def _unicode_to_latex(self, text: str) -> str:
        """Convert unicode math to BARE LaTeX commands (for math mode)."""
        return self._convert_unicode(text, math_mode=True)

    def _convert_unicode(self, text: str, math_mode: bool) -> str:
        def emit(latex: str) -> str:
            # In math mode emit bare; in text mode wrap so it is valid as running text.
            return latex if math_mode else f"${latex}$"

        out: list[str] = []
        i, n = 0, len(text)
        while i < n:
            ch = text[i]
            if ch in self.SUB_MAP:
                digits = []
                while i < n and text[i] in self.SUB_MAP:
                    digits.append(self.SUB_MAP[text[i]]); i += 1
                out.append(emit("_{" + "".join(digits) + "}")); continue
            if ch in self.SUP_MAP:
                digits = []
                while i < n and text[i] in self.SUP_MAP:
                    digits.append(self.SUP_MAP[text[i]]); i += 1
                out.append(emit("^{" + "".join(digits) + "}")); continue
            if ch in self.SYM_MAP:
                out.append(emit(self.SYM_MAP[ch]))
                if math_mode:
                    out.append(" ")
                i += 1; continue
            if ch == self.RUPEE:
                out.append("Rs.~" if not math_mode else r"\text{Rs.~}"); i += 1; continue
            out.append(ch); i += 1
        return "".join(out)

    def _escape_mixed_latex(self, text: str) -> list[str]:
        text = self._close_math_envs(self._normalize_latex_text(text))
        parts: list[str] = []
        pos = 0
        for match in self.INLINE_MATH_RE.finditer(text):
            if match.start() > pos:
                parts.append(self._escape_text(text[pos:match.start()]))
            token = match.group(0)
            display = token.startswith("$$")
            content = token[2:-2] if display else token[1:-1]
            if self._math_is_prose(content):
                parts.append(self._demote_math_to_text(content))
            else:
                math = self._sanitize_math(content)
                parts.append(self._display_math(math) if display else f"${math}$")
            pos = match.end()
        if pos < len(text):
            parts.append(self._escape_text(text[pos:]))
        return parts

    def _escape_mixed_with_math(self, text: str) -> str:
        text = self._close_math_envs(self._normalize_latex_text(text))
        parts = []
        pos = 0
        for match in self.INLINE_MATH_RE.finditer(text):
            if match.start() > pos:
                parts.append(self._escape_text(text[pos:match.start()]))
            token = match.group(0)
            display = token.startswith("$$")
            content = token[2:-2] if display else token[1:-1]
            if self._math_is_prose(content):
                parts.append(self._demote_math_to_text(content))
            else:
                math = self._sanitize_math(content)
                parts.append(self._display_math(math) if display else f"${math}$")
            pos = match.end()
        if pos < len(text):
            parts.append(self._escape_text(text[pos:]))
        return "".join(parts)

    def _escape_text(self, text: str) -> str:
        parts = []
        i, n = 0, len(text)
        while i < n:
            ch = text[i]
            # Unicode math in running text → wrap in $...$ (emitted raw so the
            # injected braces are NOT brace-escaped below).
            if ch in self.SUB_MAP:
                d = []
                while i < n and text[i] in self.SUB_MAP:
                    d.append(self.SUB_MAP[text[i]]); i += 1
                parts.append("$_{" + "".join(d) + "}$"); continue
            if ch in self.SUP_MAP:
                d = []
                while i < n and text[i] in self.SUP_MAP:
                    d.append(self.SUP_MAP[text[i]]); i += 1
                parts.append("$^{" + "".join(d) + "}$"); continue
            if ch in self.SYM_MAP:
                parts.append("$" + self.SYM_MAP[ch] + "$"); i += 1; continue
            if ch == self.RUPEE:
                parts.append("Rs.~"); i += 1; continue
            if ch == "\\" and i + 1 < n and text[i + 1].isalpha():
                end = self._consume_math_run(text, i)
                frag = text[i:end].strip()
                if frag:
                    parts.append("$" + self._sanitize_math(frag) + "$")
                i = end
            elif ch == "\\":
                parts.append(r"\textbackslash{}")
                i += 1
            else:
                parts.append(self.LATEX_SPECIALS.get(ch, ch))
                i += 1
        return "".join(parts)

    def _sanitize_math(self, math: str) -> str:
        math = self._normalize_latex_text(math)
        math = self._unicode_to_latex(math)  # bare commands — we are inside math mode
        math = self._strip_outer_math_delimiters(math)
        math = math.replace("$", "")
        math = re.sub(r"\s+", " ", math).strip()
        math = self._textify_prose_in_math(math)
        return math or r"\text{ }"

    @staticmethod
    def _matching_brace(text: str, open_idx: int) -> int:
        """Return index just past the '}' matching the '{' at ``open_idx``."""
        depth = 0
        i = open_idx
        n = len(text)
        while i < n:
            c = text[i]
            if c == "\\":
                i += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        return n  # unbalanced — copy to end

    @staticmethod
    def _matching_bracket(text: str, open_idx: int) -> int:
        depth = 0
        i = open_idx
        n = len(text)
        while i < n:
            c = text[i]
            if c == "\\":
                i += 2
                continue
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        return n

    def _textify_prose_in_math(self, math: str) -> str:
        """Wrap prose the model wrongly placed inside math mode in ``\\text{}``.

        The model frequently emits whole sentences inside ``$...$`` ("Let the
        width be x metres"). In math mode every space is discarded, so the words
        collapse into one unbreakable token that overflows the page. Here we wrap
        prose words/phrases in ``\\text{}`` (which preserves spaces) while leaving
        genuine formula tokens — LaTeX commands, numbers, operators, single-letter
        variables and short 2–3 letter variable products — untouched.
        """
        # Commands whose brace argument is already text / a structural name and
        # must be copied verbatim (never re-wrapped): \begin{array}, \text{...},
        # \operatorname{...}, etc.
        verbatim_arg_cmds = {
            "begin", "end", "text", "textbf", "textit", "textrm", "mathrm",
            "mathbf", "mathit", "mathsf", "mathtt", "operatorname", "label",
            "ref", "mbox", "hbox", "textnormal",
        }
        out: list[str] = []
        i, n = 0, len(math)
        while i < n:
            ch = math[i]
            # Copy LaTeX commands verbatim: \frac, \theta, \\, \{, \, ...
            if ch == "\\":
                j = i + 1
                if j < n and math[j].isalpha():
                    while j < n and math[j].isalpha():
                        j += 1
                cmd = math[i + 1:j]
                if j == i + 1:  # backslash + non-letter (\\, \{, \,)
                    j = min(i + 2, n)
                    out.append(math[i:j])
                    i = j
                    continue
                out.append(math[i:j])
                i = j
                # Copy the brace argument(s) of text/structural commands verbatim
                if cmd in verbatim_arg_cmds:
                    while i < n and math[i] == "{":
                        grp_end = self._matching_brace(math, i)
                        out.append(math[i:grp_end])
                        i = grp_end
                continue
            if ch.isalpha():
                j = i
                while j < n and math[j].isalpha():
                    j += 1
                word = math[i:j]
                if len(word) < 2 or word.lower() in self.MATH_FUNCS:
                    out.append(word)
                    i = j
                    continue
                # Greedily absorb a following multi-word run so intra-phrase
                # spaces survive: "the park be x metres" → one \text{} block.
                phrase = word
                k = j
                while True:
                    m = re.match(r"[ ]+([A-Za-z]+)", math[k:])
                    if not m:
                        break
                    phrase += " " + m.group(1)
                    k += m.end()
                # A lone short word (2–3 letters) is most likely a variable
                # product (mx, ab, dx); leave it as math. Longer words or
                # multi-word phrases are prose → wrap them.
                if len(phrase.split()) >= 2 or len(word) >= 4:
                    if out and out[-1][-1:] not in (" ", "{", "(", "$"):
                        out.append(r"\ ")
                    out.append(r"\text{" + phrase + "}")
                    i = k
                else:
                    out.append(word)
                    i = j
                continue
            out.append(ch)
            i += 1
        return "".join(out)

    def _math_is_prose(self, content: str) -> bool:
        """True when a ``$...$`` span is really a sentence the model misfiled in
        math mode. Such spans must be rendered as running text so they line-break;
        as math they collapse and overflow the page. Commands and their braced
        arguments are removed first so formula labels (``\\frac{OA}{OP}``) are not
        mistaken for words; genuine prose carries several lowercase words."""
        stripped = re.sub(r"\\[A-Za-z]+(?:\s*\{[^{}]*\})*", " ", content)
        stripped = re.sub(r"[{}]", " ", stripped)
        words = [w for w in re.findall(r"[A-Za-z]{2,}", stripped)
                 if w.lower() not in self.MATH_FUNCS]
        lower_words = [w for w in words if len(w) >= 3 and not w.isupper()]
        return len(words) >= 3 and len(lower_words) >= 2

    def _demote_math_to_text(self, content: str) -> str:
        """Render a prose-ish math span as text, re-wrapping only the genuine
        formula fragments (``\\frac{1}{2}``, ``\\pi r^2`` …) in ``$...$``."""
        out: list[str] = []
        buf: list[str] = []

        def flush():
            if buf:
                out.append(self._escape_text("".join(buf)))
                buf.clear()

        i, n = 0, len(content)
        while i < n:
            ch = content[i]
            if ch == "\\" and i + 1 < n and content[i + 1].isalpha():
                flush()
                start = i
                i = self._consume_math_run(content, i)
                frag = content[start:i].strip()
                if frag:
                    out.append(f"${frag}$")
            else:
                buf.append(ch)
                i += 1
        flush()
        return "".join(out)

    def _consume_math_run(self, s: str, i: int) -> int:
        """From a backslash command at ``i``, consume the maximal contiguous
        math run (command + arguments + scripts + glued variables/operators)."""
        n = len(s)
        i += 1
        while i < n and s[i].isalpha():
            i += 1
        while i < n:
            c = s[i]
            if c == "{":
                i = self._matching_brace(s, i)
                continue
            if c == "[":
                i = self._matching_bracket(s, i)
                continue
            if c in "^_":
                i += 1
                if i < n and s[i] == "{":
                    i = self._matching_brace(s, i)
                elif i < n and s[i] == "\\" and i + 1 < n and s[i + 1].isalpha():
                    i += 1
                    while i < n and s[i].isalpha():
                        i += 1
                elif i < n:
                    i += 1
                continue
            if c == "\\":
                if i + 1 < n and s[i + 1].isalpha():
                    i += 1
                    while i < n and s[i].isalpha():
                        i += 1
                    continue
                i += 2
                continue
            if c.isdigit() or c in "+-*/=(),.<>|!":
                i += 1
                continue
            if c == " ":
                k = i
                while k < n and s[k] == " ":
                    k += 1
                glue = k < n and (
                    s[k] == "\\" or s[k].isdigit() or s[k] in "^_(+-=/"
                    or (s[k].isalpha() and (k + 1 >= n or not s[k + 1].isalpha()))
                )
                if glue:
                    i = k
                    continue
                break
            if c.isalpha():
                j = i
                while j < n and s[j].isalpha():
                    j += 1
                if j - i == 1:  # single-letter variable
                    i = j
                    continue
                break  # multi-letter prose word ends the run
            break
        return i

    @staticmethod
    def _strip_outer_math_delimiters(text: str) -> str:
        text = text.strip()
        for start, end in (("$$", "$$"), ("$", "$")):
            while text.startswith(start) and text.endswith(end) and len(text) >= len(start) + len(end):
                text = text[len(start):-len(end)].strip()
        return text

    def _close_math_envs(self, text: str) -> str:
        opens = text.count("\\(")
        closes = text.count("\\)")
        if opens > closes:
            text += "\\)" * (opens - closes)
        opens = text.count("\\[")
        closes = text.count("\\]")
        if opens > closes:
            text += "\\]" * (opens - closes)
        opens = text.count("$")
        if opens % 2 != 0:
            text += "$"
        return text

    def _format_answer(self, answer: Any, qtype: str = "") -> str:
        answer_str = self._normalize_latex_text(answer)
        # Plain option label, e.g. "(C)"
        if re.match(r'^\([A-D]\)$', answer_str):
            return answer_str
        # MCQ / Assertion-Reason answers may carry the option text, e.g.
        # "(C) $16 - 24$". Render them inline as text (preserving any $...$),
        # not as a standalone display-math block.
        if qtype in ("mcq", "assertion_reason"):
            return self._escape_latex(answer_str)
        if self._looks_like_math_answer(answer_str):
            return "$" + self._sanitize_math(answer_str) + "$"
        return self._escape_mixed_with_math(answer_str)

    def _looks_like_math_answer(self, answer: str) -> bool:
        answer = self._normalize_latex_text(answer)
        if not answer:
            return False
        if self.INLINE_MATH_RE.search(answer):
            outside = re.sub(self.INLINE_MATH_RE, " ", answer)
            if re.search(r"[A-Za-z]", outside):
                return False
        stripped = self._strip_outer_math_delimiters(answer)
        if answer.startswith("$") and answer.endswith("$"):
            return not self._contains_running_prose(stripped)
        if self._contains_running_prose(stripped):
            return False
        if re.search(r"\\(?:frac|sqrt|text|angle|triangle|pi|theta|times|div|cdot|pm|neq|leq|geq)\b", stripped):
            return True
        if re.search(r"[\^_=]|[A-Za-z]\s*[=<>]|[=<>]\s*[A-Za-z0-9]", stripped):
            return True
        return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:\s*\\text\{[^{}]+\})?", stripped))

    def _contains_running_prose(self, text: str) -> bool:
        text = self._normalize_latex_text(text)
        outside_math = re.sub(self.INLINE_MATH_RE, " ", text)
        outside_math = re.sub(r"\\[A-Za-z]+(?:\s*\{[^{}]*\})*", " ", outside_math)
        words = [word for word in re.findall(r"[A-Za-z]{4,}", outside_math)
                 if word.lower() not in self.MATH_FUNCS]
        if len(words) >= 3:
            return True
        return bool(re.search(r"[.!?]\s+[A-Z]", outside_math)) and len(words) >= 1

    def _is_severely_broken_solution(self, text: str) -> bool:
        if not text:
            return False
        open_display = text.count(r"\[")
        close_display = text.count(r"\]")
        return open_display > 5 and open_display > close_display + 3

    def _has_broken_math(self, text: str) -> bool:
        open_display = text.count(r"\[")
        close_display = text.count(r"\]")
        if abs(open_display - close_display) > 2:
            return True

        stripped = text.replace("$$", "")
        if stripped.count("$") % 2 != 0:
            return True

        if r"\[\]" in text or r"\]\[" in text:
            return True

        lefts = len(re.findall(r"\\left\b", text))
        rights = len(re.findall(r"\\right\b", text))
        return lefts != rights

    def _beautify_solution(self, text: str) -> str:
        if not text or len(text) < 200:
            return text

        display_blocks = len(re.findall(r"\\\[", text))
        has_align = "\\begin{align" in text
        if display_blocks <= 1 and not has_align and len(text) < 500:
            return text

        close_brackets = text.count(r"\]")
        if display_blocks > 5 and abs(display_blocks - close_brackets) > 5:
            return self._format_plaintext_step_fallback(text)

        text = re.sub(r"\\\]\s+\\\[", r"\\]\n\n\\[", text)
        text = re.sub(r"\\\]\s+([A-Z])", r"\\]\n\n\1", text)
        text = re.sub(r"([^\n])\$\$", r"\1\n\n$$", text)
        text = re.sub(r"\$\$\s+", r"$$\n\n", text)
        return text

    def _format_plaintext_step_fallback(self, text: str) -> str:
        plain_text = self._strip_latex(text)
        steps = self._split_plain_solution_steps(plain_text)
        if not steps:
            return r"\textit{Solution not available.}"
        items = [
            r"\item " + self._format_solution_step_explanation(step)
            for step in steps
            if step.strip()
        ]
        return (
            r"\begin{enumerate}[leftmargin=*, itemsep=0.35cm]" + "\n"
            + "\n".join(items) + "\n"
            + r"\end{enumerate}"
        )

    def _split_plain_solution_steps(self, text: str) -> list[str]:
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []

        transitions = [
            "However", "Therefore", "Thus", "Hence", "Since", "Because",
            "Consequently", "Accordingly", "Furthermore", "Moreover",
            "Alternatively", "Instead", "Similarly", "Conversely", "Using",
            "Given", "Now", "Then", "Finally", "So", "The", "This", "We",
        ]
        for transition in transitions:
            text = re.sub(rf"\s+({transition}\b)", rf". \1", text)

        text = re.sub(r"\s+(?=([A-Za-z][A-Za-z0-9_()]*\s*=))", ". ", text)
        candidates = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)

        steps: list[str] = []
        for candidate in candidates:
            candidate = candidate.strip(" .")
            if not candidate:
                continue
            if len(candidate) <= 260:
                steps.append(candidate + ".")
                continue
            parts = [part.strip() for part in re.split(r"[,;]\s+", candidate) if part.strip()]
            current = ""
            for part in parts:
                if not current:
                    current = part
                elif len(current) + len(part) < 240:
                    current += "; " + part
                else:
                    steps.append(current.rstrip(" .") + ".")
                    current = part
            if current:
                steps.append(current.rstrip(" .") + ".")

        if len(steps) <= 1 and len(text) > 260:
            words = text.split()
            steps = []
            for start in range(0, len(words), 35):
                chunk = " ".join(words[start:start + 35]).strip()
                if chunk:
                    steps.append(chunk.rstrip(" .") + ".")

        return steps

    def _strip_latex(self, text: str) -> str:
        if not text:
            return ""
        text = self._repair_control_char_latex(str(text))
        text = re.sub(r"\\\[", "", text)
        text = re.sub(r"\\\]", "", text)
        text = re.sub(r"\$\$(.*?)\$\$", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"\$([^$]+?)\$", r"\1", text)
        text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", text)
        text = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", text)
        replacements = {
            r"\\alpha\b": "alpha",
            r"\\beta\b": "beta",
            r"\\gamma\b": "gamma",
            r"\\delta\b": "delta",
            r"\\theta\b": "theta",
            r"\\lambda\b": "lambda",
            r"\\mu\b": "mu",
            r"\\pi\b": "pi",
            r"\\rho\b": "rho",
            r"\\sigma\b": "sigma",
            r"\\tau\b": "tau",
            r"\\omega\b": "omega",
            r"\\Omega\b": "Omega",
        }
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        text = re.sub(r"\\(?:text|mathrm|mathbf|mathit)\{([^{}]+)\}", r"\1", text)
        text = re.sub(r"\\(?:begin|end)\{[^{}]+\}", " ", text)
        text = re.sub(r"\\[A-Za-z]+", " ", text)
        text = re.sub(r"[{}]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def _escape_strict_text(self, text: str) -> str:
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        return "".join(replacements.get(ch, ch) for ch in str(text or ""))

    def _format_solution_step_explanation(self, explanation: str) -> str:
        try:
            return self._escape_latex(explanation)
        except Exception:
            return self._escape_strict_text(self._strip_latex(explanation))

    def _format_explanation_lines(self, text: str) -> str:
        text = self._normalize_latex_text(text)
        text = self._close_math_envs(text)
        text = self._strip_wrapping_math_if_mixed(text)
        lines = self._split_explanation_lines(text)
        if not lines:
            return ""
        parts = ["\\begin{enumerate}[leftmargin=*, itemsep=2pt]"]
        for line in lines:
            parts.append(f"  \\item {self._escape_mixed_with_math(line)}")
        parts.append("\\end{enumerate}")
        return "\n".join(parts)

    def _strip_wrapping_math_if_mixed(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("$") and stripped.endswith("$") and self._math_is_prose(stripped[1:-1]):
            return stripped[1:-1].strip()
        return text

    def _split_explanation_lines(self, text: str) -> list[str]:
        text = re.sub(r"\s*\\\\\s*", "\n", text)
        lines: list[str] = []
        for raw in text.splitlines():
            raw = raw.strip(" ;")
            if not raw:
                continue
            lines.append(raw)
        return lines or [text.strip()]

    def _format_derivation(self, derivation: str) -> str:
        # Standardise EVERY derivation to one canonical form regardless of how the
        # model wrote it ($$, \[\], align*, aligned, or bare lines): strip any
        # math wrappers/environments, then re-wrap exactly once as a display
        # aligned block. This avoids the double-wrap (\begin{aligned}\begin{aligned})
        # and mixed-convention output we used to produce.
        derivation = self._normalize_latex_text(derivation)
        # A "derivation" the model wrote as a prose paragraph (rather than
        # equations) reads far better as flowing, wrappable text than as one
        # display block shrunk to an illegible sliver. Route it through the
        # mixed text/math escaper, which keeps real formula fragments as math.
        if self._contains_running_prose(derivation) or self._math_is_prose(derivation):
            return self._format_explanation_lines(derivation)
        inner = self._strip_math_wrappers(derivation)
        if not inner:
            return ""
        return self._format_equation_block(inner)

    def _strip_math_wrappers(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\\(?:begin|end)\{(?:aligned|align\*?|gather\*?|equation\*?|multline\*?|split)\}",
                      "", text)
        text = text.replace(r"\[", "").replace(r"\]", "")
        text = text.replace("$$", "")
        return text.strip()

    def _format_equation_block(self, text: str) -> str:
        if "\n" in text:
            text = " \\\\ ".join(line.strip() for line in text.splitlines() if line.strip())
        math = self._sanitize_math(text)
        lines = self._split_math_derivation(math)
        if len(lines) <= 1:
            return self._display_math(lines[0], align="left")
        return self._display_math(
            "\\begin{aligned}\n" + " \\\\\n".join(lines) + "\n\\end{aligned}",
            align="left",
        )

    def _display_math(self, inner: str, align: str = "center") -> str:
        """Render a display-math block that can never overflow the text width.

        ``adjustbox`` scales the content down only when it is wider than the line
        (pathological / model-garbage derivations); normal-width math is left at
        full size. This is the definitive guard against the run-off-the-page
        display-math overflows."""
        inner = inner.strip()
        if not inner:
            return ""
        if align == "left":
            return "\\noindent\\fitmath{" + inner + "}\\par"
        return (
            "\\begin{center}\n"
            "\\fitmath{" + inner + "}\n"
            "\\end{center}"
        )

    def _split_math_derivation(self, math: str) -> list[str]:
        math = re.sub(r"\s+", " ", math).strip()
        if not math:
            return [r"\text{ }"]
        math = math.replace(r"\\", "\n")
        math = math.replace(r"\newline", "\n")
        math = math.replace(r"\Rightarrow", "\n" + r"\Rightarrow")
        math = math.replace(r"\Leftarrow", "\n" + r"\Leftarrow")
        math = math.replace(r"\implies", "\n" + r"\implies")
        math = math.replace(r"\iff", "\n" + r"\iff")
        raw_lines = []
        for line in math.splitlines():
            line = line.strip(" ,;")
            # drop empty rows and stray alignment-only rows (e.g. "&", "& &")
            if not line or not line.replace("&", "").strip():
                continue
            raw_lines.append(line)
        return raw_lines or [math]

    def _format_solution_step(self, step: Any) -> str:
        if isinstance(step, dict):
            parts: list[str] = []
            explanation = str(step.get("explanation", "")).strip()
            if explanation:
                parts.append(self._format_solution_step_explanation(explanation))
            equations = step.get("equations", [])
            if isinstance(equations, str):
                equations = [equations]
            if isinstance(equations, list):
                for equation in equations:
                    equation_text = str(equation or "").strip()
                    if not equation_text:
                        continue
                    if self._contains_running_prose(equation_text):
                        parts.append(self._format_solution_step_explanation(equation_text))
                    else:
                        parts.append(self._format_equation_block(equation_text))
            return "\n\n".join(part for part in parts if part) or r"\textit{Step unavailable.}"

        step_text = self._normalize_latex_text(str(step))
        if self._contains_markdown_table(step_text):
            return self._format_mixed_text_with_tables(step_text)
        if "$" in step_text:
            return self._escape_mixed_with_math(step_text)
        stripped = self._strip_outer_math_delimiters(step_text)
        if self._looks_like_standalone_math(stripped):
            return "\\(\n" + self._sanitize_math(stripped) + "\n\\)"
        # Fallback via _escape_latex (not _escape_text) so a bare math command
        # the model left unwrapped in prose (e.g. "in \triangle OPA") gets
        # wrapped in $...$ instead of erroring as an undefined text-mode command.
        return self._escape_latex(step_text)

    def _looks_like_equation(self, text: str) -> bool:
        markers = ("\\frac", "\\sqrt", "\\int", "\\sum", "^", "_", "=")
        return any(marker in text for marker in markers)

    def _looks_like_standalone_math(self, text: str) -> bool:
        if not self._looks_like_equation(text):
            return False
        if ":" in text:
            return False
        if re.search(r"[.!?]\s", text):
            return False
        words = re.findall(r"[A-Za-z]{2,}", re.sub(r"\\[A-Za-z]+", " ", text))
        prose_words = {
            "where", "using", "therefore", "hence", "since",
            "substitute", "solving", "gives", "with", "and",
            "or", "the", "is", "are", "calculate", "find", "use",
            "identify", "set", "solve", "simplify", "verify",
        }
        return not any(word.lower() in prose_words for word in words)

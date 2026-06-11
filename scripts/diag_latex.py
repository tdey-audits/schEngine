"""Diagnostic: render real generated questions through CBSELaTeXRenderer,
compile with pdflatex, and report every error/warning the engine emits.

Usage: .backend-venv/bin/python scripts/diag_latex.py [batch_size]
"""
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from renderer.latex_renderer import CBSELaTeXRenderer

ROOT = Path(__file__).resolve().parent.parent
DIAG = ROOT / "pdfs" / "diag"
DIAG.mkdir(parents=True, exist_ok=True)


def load_questions():
    qs = []
    for f in sorted(glob.glob(str(ROOT / "output" / "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if isinstance(d, dict) and isinstance(d.get("questions"), list):
            qs += d["questions"]
    return qs


ERR_RE = re.compile(r"^(?:! |.*?Error:|.*?Undefined control sequence)", re.M)


def compile_tex(tex: str, name: str):
    tex_path = DIAG / f"{name}.tex"
    tex_path.write_text(tex)
    r = CBSELaTeXRenderer(output_dir=str(DIAG), build_dir=str(DIAG))
    # compile in place, keep logs
    subprocess.run(
        [r.pdflatex_path, "-interaction=nonstopmode", "-halt-on-error",
         f"-output-directory={DIAG}", str(tex_path)],
        capture_output=True, text=False, timeout=60,
    )
    log = (DIAG / f"{name}.log")
    pdf = (DIAG / f"{name}.pdf")
    errors = []
    if log.exists():
        text = log.read_text(errors="ignore")
        for m in re.finditer(r"^! (.+)$", text, re.M):
            # capture the offending line that follows
            errors.append(m.group(1).strip())
        for m in re.finditer(r"^(.*Undefined control sequence.*)$", text, re.M):
            errors.append(m.group(1).strip())
    return pdf.exists() and pdf.stat().st_size > 0, errors


def main():
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    qs = load_questions()
    print(f"Loaded {len(qs)} questions; testing in batches of {batch}\n")

    renderer = CBSELaTeXRenderer(output_dir=str(DIAG), build_dir=str(DIAG))
    failed_batches = 0
    all_errors = {}
    # Test question paper + solutions for each batch
    for bi in range(0, len(qs), batch):
        chunk = qs[bi:bi + batch]
        for kind, builder in (
            ("qp", lambda c: renderer._build_question_paper_tex(c, "Diag", None, "3 Hours", "80")),
            ("sol", lambda c: renderer._build_solution_booklet_tex(c, "Diag Solutions")),
        ):
            tex = renderer._repair_tex(builder(chunk))
            name = f"b{bi:04d}_{kind}"
            ok, errors = compile_tex(tex, name)
            if not ok or errors:
                failed_batches += 1
                for e in errors:
                    all_errors[e] = all_errors.get(e, 0) + 1
                if not ok:
                    all_errors[f"<NO PDF PRODUCED: {name}>"] = all_errors.get(f"<NO PDF PRODUCED: {name}>", 0) + 1

    print(f"\n===== {failed_batches} batch-docs had errors =====\n")
    for e, c in sorted(all_errors.items(), key=lambda x: -x[1]):
        print(f"[{c:3}x] {e[:160]}")


if __name__ == "__main__":
    main()

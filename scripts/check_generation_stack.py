#!/usr/bin/env python3
"""Development sanity checks for the generation stack.

This is intentionally lightweight: it avoids LLM calls and verifies the parts
that usually regress when corpora or prompt plumbing changes.
"""

from __future__ import annotations

import json
import py_compile
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.generator import QuestionGenerator
from generator.prompts import build_prompt
from graph.source_pattern_graph import get_source_patterns
from syllabus.ncert_class10 import normalize_question_type


MODULES = [
    "config/settings.py",
    "ingest/exemplar_chunker.py",
    "ingest/exemplar_pipeline.py",
    "ingest/pyq_chunker.py",
    "ingest/pyq_pipeline.py",
    "rag/exemplar_retriever.py",
    "rag/pyq_retriever.py",
    "graph/math_graph.py",
    "graph/source_pattern_graph.py",
    "graph/graph_rag.py",
    "generator/prompts.py",
    "generator/generator.py",
    "api/schemas.py",
    "api/routes.py",
    "generate.py",
]


def main() -> int:
    _compile_modules()
    _check_aliases()
    _check_corpora()
    _check_source_patterns()
    _check_prompt_wiring()
    print("generation stack checks passed")
    return 0


def _compile_modules() -> None:
    for module in MODULES:
        py_compile.compile(str(ROOT / module), doraise=True)


def _check_aliases() -> None:
    assert normalize_question_type("sa_i") == "vsa"
    assert normalize_question_type("sa_ii") == "sa"


def _check_corpora() -> None:
    exemplar = _load_json("data/exemplar_metadata.json")
    pyq = _load_json("data/pyq_metadata.json")
    assert len(exemplar) >= 600, f"expected >=600 exemplar chunks, got {len(exemplar)}"
    assert len(pyq) >= 700, f"expected >=700 pyq chunks, got {len(pyq)}"
    exemplar_types = Counter(row.get("question_type") for row in exemplar)
    for qtype in ("mcq", "vsa", "sa", "la"):
        assert exemplar_types[qtype] > 0, f"missing exemplar type {qtype}"


def _check_source_patterns() -> None:
    trig = get_source_patterns(
        "Introduction to Trigonometry",
        question_type="sa",
        paper_level="challenging",
        limit=5,
    )
    assert trig, "missing source-derived patterns for trigonometry"
    assert any(p.get("relation") == "concept_depth" for p in trig), (
        "trigonometry challenging patterns should include Exemplar concept_depth"
    )


def _check_prompt_wiring() -> None:
    gen = QuestionGenerator()
    query = "Introduction to Trigonometry trigonometric identities"
    graph = gen._retrieve_graph_context(
        query,
        "Introduction to Trigonometry",
        "hard",
        question_type="sa",
        paper_level="challenging",
    )
    pyq = gen._retrieve_pyq_patterns(query, "sa", "standard", True)
    exemplar = gen._retrieve_exemplar_depth(
        query,
        "Introduction to Trigonometry",
        "sa",
        "challenging",
    )
    graph_contexts = gen._attach_reference_profiles(
        graph.get("graph_contexts", {}),
        pyq,
        exemplar,
        "challenging",
    )
    _, prompt = build_prompt(
        chapter="Introduction to Trigonometry",
        subtopic=None,
        question_type="sa",
        marks=3,
        count=1,
        retrieved_context=graph.get("chunks", []),
        difficulty="hard",
        graph_rag_contexts=graph_contexts,
        pyq_context=pyq,
        exemplar_context=exemplar,
        paper_level="challenging",
    )
    required = [
        "PAPER DIFFICULTY BAND: CHALLENGING",
        "Source-derived question pattern nodes",
        "Retrieved reference profiles",
        "NCERT EXEMPLAR CONCEPTUAL DEPTH CONTEXT",
    ]
    for needle in required:
        assert needle in prompt, f"prompt missing {needle!r}"


def _load_json(path: str) -> list[dict]:
    p = ROOT / path
    assert p.exists(), f"missing {path}; run ingestion first"
    data = json.loads(p.read_text())
    assert isinstance(data, list), f"{path} must contain a JSON list"
    return data


if __name__ == "__main__":
    raise SystemExit(main())

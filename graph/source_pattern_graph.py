"""Source-derived question pattern graph.

This layer turns ingested question corpora (PYQ, Exemplar, later RD Sharma)
into reusable pattern nodes attached to syllabus concepts. It does not make
the corpora authoritative for content; it makes their question designs visible
to GraphRAG.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from config.settings import settings


@dataclass
class SourcePatternNode:
    id: str
    concept: str
    pattern: str
    relation: str
    source_counts: Counter[str] = field(default_factory=Counter)
    question_type_counts: Counter[str] = field(default_factory=Counter)
    depth_counts: Counter[str] = field(default_factory=Counter)
    paper_variant_counts: Counter[str] = field(default_factory=Counter)
    reasoning_moves: Counter[str] = field(default_factory=Counter)
    examples: list[dict[str, Any]] = field(default_factory=list)

    @property
    def support(self) -> int:
        return sum(self.source_counts.values())

    def to_context(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "concept": self.concept,
            "pattern": self.pattern,
            "relation": self.relation,
            "support": self.support,
            "sources": dict(self.source_counts),
            "question_types": dict(self.question_type_counts),
            "depths": dict(self.depth_counts),
            "paper_variants": dict(self.paper_variant_counts),
            "reasoning_moves": [m for m, _ in self.reasoning_moves.most_common(5)],
            "examples": self.examples[:2],
        }


CHAPTER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Real Numbers": ("hcf", "lcm", "euclid", "prime factor", "irrational", "decimal expansion"),
    "Polynomials": ("polynomial", "zero", "coefficient", "degree", "division algorithm"),
    "Pair of Linear Equations in Two Variables": ("linear equation", "pair of equations", "consistent", "inconsistent"),
    "Quadratic Equations": ("quadratic", "discriminant", "roots", "real and equal"),
    "Arithmetic Progressions": ("arithmetic progression", " ap ", "common difference", "nth term"),
    "Triangles": ("similar", "bpt", "pythagoras", "triangle", "proportional"),
    "Coordinate Geometry": ("coordinate", "distance formula", "section formula", "midpoint", "collinear"),
    "Introduction to Trigonometry": ("sin", "cos", "tan", "cot", "sec", "cosec", "trigonometric"),
    "Some Applications of Trigonometry": ("angle of elevation", "angle of depression", "height", "line of sight"),
    "Circles": ("circle", "tangent", "radius", "point of contact"),
    "Constructions": ("construct", "construction", "draw a", "divide a line segment"),
    "Areas Related to Circles": ("sector", "segment", "arc", "shaded region", "area of circle"),
    "Surface Areas and Volumes": ("surface area", "volume", "cylinder", "cone", "sphere", "hemisphere", "frustum"),
    "Statistics": ("mean", "median", "mode", "frequency", "ogive", "class interval"),
    "Probability": ("probability", "coin", "dice", "card", "ball", "random"),
}


def get_source_patterns(concept: str, question_type: str | None = None,
                        paper_level: str | None = None,
                        limit: int = 6) -> list[dict[str, Any]]:
    graph = _build_source_pattern_graph()
    candidates = [
        node for node in graph
        if _same_concept(node.concept, concept)
    ]

    if question_type:
        qtype = question_type.lower()
        matching = [n for n in candidates if n.question_type_counts.get(qtype)]
        if matching:
            candidates = matching

    if paper_level == "challenging":
        scored = sorted(
            candidates,
            key=lambda n: (
                n.depth_counts.get("challenging", 0),
                n.source_counts.get("ncert_exemplar", 0),
                n.support,
            ),
            reverse=True,
        )
    elif paper_level == "medium":
        scored = sorted(
            candidates,
            key=lambda n: (
                n.source_counts.get("ncert_exemplar", 0),
                n.depth_counts.get("medium", 0) + n.depth_counts.get("challenging", 0),
                n.support,
            ),
            reverse=True,
        )
    else:
        scored = sorted(
            candidates,
            key=lambda n: (
                n.source_counts.get("pyq", 0),
                n.support,
            ),
            reverse=True,
        )

    return [node.to_context() for node in scored[:limit]]


@lru_cache(maxsize=1)
def _build_source_pattern_graph() -> tuple[SourcePatternNode, ...]:
    rows = []
    rows.extend(_load_metadata(settings.exemplar_metadata_path))
    rows.extend(_load_metadata(settings.pyq_metadata_path))

    nodes: dict[tuple[str, str, str], SourcePatternNode] = {}
    for row in rows:
        text = _clean(row.get("text", ""))
        if not text:
            continue
        concept = _infer_concept(row, text)
        if not concept:
            continue
        pattern = _infer_pattern(text, concept)
        source_type = row.get("source_type") or _infer_source_type(row)
        relation = "concept_depth" if source_type == "ncert_exemplar" else "exam_pattern"
        key = (concept, pattern, relation)
        if key not in nodes:
            nodes[key] = SourcePatternNode(
                id=_node_id(concept, pattern, relation),
                concept=concept,
                pattern=pattern,
                relation=relation,
            )
        node = nodes[key]
        qtype = str(row.get("question_type") or "unknown").lower()
        depth = str(row.get("estimated_depth") or ("standard" if source_type == "pyq" else "unknown")).lower()
        variant = str(row.get("paper_level") or "").lower()
        node.source_counts[source_type] += 1
        node.question_type_counts[qtype] += 1
        node.depth_counts[depth] += 1
        if variant:
            node.paper_variant_counts[variant] += 1
        for move in _infer_reasoning_moves(text):
            node.reasoning_moves[move] += 1
        if len(node.examples) < 3:
            node.examples.append({
                "source": row.get("source", ""),
                "question_no": row.get("question_no"),
                "question_type": qtype,
                "text_preview": text[:220],
            })

    return tuple(nodes.values())


def _load_metadata(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _infer_source_type(row: dict[str, Any]) -> str:
    source = str(row.get("source", "")).lower()
    if "exemplar" in source:
        return "ncert_exemplar"
    if "pyq" in source or row.get("paper_level"):
        return "pyq"
    return "unknown"


def _infer_concept(row: dict[str, Any], text: str) -> str | None:
    chapter = str(row.get("chapter", "")).strip()
    if chapter == "Introduction to Trigonometry" and _is_application_trig(text):
        return "Some Applications of Trigonometry"
    if chapter in CHAPTER_KEYWORDS:
        return chapter

    lower = f" {text.lower()} "
    scores: dict[str, int] = {}
    for concept, keywords in CHAPTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.strip() in lower:
                score += 2 if len(kw) > 6 else 1
        if score:
            scores[concept] = score
    if not scores:
        return None
    concept = max(scores.items(), key=lambda item: item[1])[0]
    if concept == "Introduction to Trigonometry" and _is_application_trig(text):
        return "Some Applications of Trigonometry"
    return concept


def _infer_pattern(text: str, concept: str) -> str:
    lower = text.lower()
    if concept == "Introduction to Trigonometry":
        if "prove" in lower or "show that" in lower:
            return "identity proof through transformation"
        if "90" in lower or "complement" in lower:
            return "complementary-angle expression evaluation"
        if "evaluate" in lower or "find the value" in lower:
            return "hidden identity evaluation"
        return "trigonometric ratio relation"
    if concept == "Some Applications of Trigonometry":
        if lower.count("angle of elevation") + lower.count("angle of depression") >= 2:
            return "two-observation height-distance setup"
        if "angle of depression" in lower and "angle of elevation" in lower:
            return "mixed elevation-depression setup"
        return "right-triangle height-distance application"
    if "prove" in lower or "show that" in lower:
        return "proof-based reasoning"
    if "find the value" in lower or "evaluate" in lower:
        return "expression evaluation"
    if "case" in lower or len(text) > 700:
        return "case-style multi-step application"
    if "missing" in lower or "unknown" in lower:
        return "unknown parameter from condition"
    return "standard application pattern"


def _infer_reasoning_moves(text: str) -> list[str]:
    lower = text.lower()
    moves = []
    if "prove" in lower or "show that" in lower:
        moves.append("transform one side before comparing")
    if "if" in lower and ("find" in lower or "evaluate" in lower):
        moves.append("derive an intermediate relation from the condition")
    if "90" in lower or "complement" in lower:
        moves.append("convert complementary angles first")
    if "sin" in lower and "cos" in lower and ("tan" in lower or "sec" in lower or "cot" in lower):
        moves.append("reduce mixed ratios using identities")
    if "angle of elevation" in lower or "angle of depression" in lower:
        moves.append("model the situation as linked right triangles")
    if not moves:
        moves.append("choose the relevant formula before computation")
    return moves


def _is_application_trig(text: str) -> bool:
    lower = text.lower()
    return "angle of elevation" in lower or "angle of depression" in lower or "line of sight" in lower


def _same_concept(a: str, b: str) -> bool:
    a_l = a.lower()
    b_l = b.lower()
    if a_l in b_l or b_l in a_l:
        return True
    if a_l == "introduction to trigonometry" and b_l == "trigonometry":
        return True
    if b_l == "introduction to trigonometry" and a_l == "trigonometry":
        return True
    return False


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text


def _node_id(concept: str, pattern: str, relation: str) -> str:
    raw = f"{concept}:{relation}:{pattern}".lower()
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_")

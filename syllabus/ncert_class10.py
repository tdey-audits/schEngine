from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower().replace("-", " ").replace("_", " "))


CBSE_QUESTION_TYPES = (
    "mcq",           # 1 mark — Multiple Choice
    "assertion_reason",  # 1 mark — Assertion-Reason
    "vsa",           # 2 marks — Very Short Answer
    "sa",            # 3 marks — Short Answer
    "la",            # 5 marks — Long Answer
    "case_study",    # 4 marks — Case Study (multiple sub-questions)
)

TYPE_MARKS_MAP: dict[str, int] = {
    "mcq": 1, "assertion_reason": 1,
    "vsa": 2, "sa": 3, "la": 5, "case_study": 4,
}

QUESTION_TYPE_ALIASES = {
    "sa_i": "vsa",
    "sa_ii": "sa",
}

HARDNESS_LEVELS = ("simple", "medium", "hard")

HARDNESS_MARKS: dict[str, tuple[int, int]] = {
    "simple": (1, 2),
    "medium": (2, 3),
    "hard": (4, 5),
}


@dataclass(frozen=True)
class Subtopic:
    name: str
    aliases: tuple[str, ...] = ()
    focus_terms: tuple[str, ...] = ()
    cbse_types: tuple[str, ...] = ("vsa", "sa")
    hardness_default: str = "medium"


@dataclass(frozen=True)
class Chapter:
    number: int
    name: str
    aliases: tuple[str, ...]
    focus_terms: tuple[str, ...]
    subtopics: tuple[Subtopic, ...]
    suggested_types: tuple[str, ...] = CBSE_QUESTION_TYPES
    marks_distribution: tuple[int, ...] = (1, 2, 3, 4, 5)


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(1, "Real Numbers", ("real numbers", "number system"),
        ("euclid", "lemma", "algorithm", "hcf", "lcm", "prime", "composite", "irrational", "rational"),
        (
            Subtopic("euclid division lemma", ("euclid", "division lemma"), ("lemma", "algorithm", "hcf"), ("vsa", "sa"), "medium"),
            Subtopic("fundamental theorem of arithmetic", ("prime factorisation",), ("prime", "factor", "hcf", "lcm"), ("vsa", "sa", "la"), "medium"),
            Subtopic("irrational numbers", ("irrational",), ("sqrt", "irrational", "contradiction"), ("vsa", "sa", "la"), "hard"),
            Subtopic("rational numbers and decimal expansions", ("decimal", "terminating", "non-terminating"), ("terminating", "recurring", "decimal"), ("mcq", "vsa"), "simple"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la")),
    Chapter(2, "Polynomials", ("polynomials",),
        ("zero", "coefficient", "degree", "quadratic", "cubic", "graph", "zeros"),
        (
            Subtopic("geometrical meaning of zeros", ("zeros of polynomial",), ("graph", "zero", "x-intercept"), ("mcq", "vsa"), "simple"),
            Subtopic("relationship between zeros and coefficients", ("relation zeros coefficients",), ("sum", "product", "zero", "coefficient"), ("vsa", "sa", "la"), "medium"),
            Subtopic("division algorithm for polynomials", ("division algorithm",), ("quotient", "remainder", "divide", "polynomial"), ("sa", "la"), "hard"),
        ),
        suggested_types=("mcq", "vsa", "sa", "la")),
    Chapter(3, "Pair of Linear Equations in Two Variables",
        ("linear equations", "pair of linear equations", "two variables"),
        ("consistent", "inconsistent", "intersecting", "parallel", "coincident", "substitution", "elimination", "cross-multiplication"),
        (
            Subtopic("graphical method", ("graphical",), ("graph", "intersection", "coincident", "parallel"), ("mcq", "vsa"), "simple"),
            Subtopic("substitution method", ("substitution",), ("substitute", "solve"), ("vsa", "sa"), "medium"),
            Subtopic("elimination method", ("elimination",), ("eliminate", "add", "subtract"), ("vsa", "sa", "la"), "medium"),
            Subtopic("cross-multiplication method", ("cross multiplication",), ("cross-multiply", "formula"), ("sa",), "hard"),
            Subtopic("equations reducible to linear form", ("reducible",), ("reduce", "substitute", "linear"), ("la",), "hard"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la", "case_study")),
    Chapter(4, "Quadratic Equations", ("quadratic", "quadratic equations"),
        ("discriminant", "roots", "nature", "real", "imaginary", "sridharacharya", "completing square"),
        (
            Subtopic("standard form and roots", ("standard form",), ("discriminant", "nature", "real", "equal"), ("mcq", "vsa"), "simple"),
            Subtopic("factorisation method", ("factorisation", "splitting middle term"), ("factor", "zero", "root"), ("vsa", "sa"), "simple"),
            Subtopic("completing the square", ("completing square",), ("complete", "square", "perfect"), ("sa", "la"), "medium"),
            Subtopic("quadratic formula", ("sridharacharya", "quadratic formula"), ("formula", "discriminant", "root"), ("vsa", "sa", "la"), "medium"),
            Subtopic("nature of roots", ("nature of roots",), ("discriminant", "real", "distinct", "equal", "imaginary"), ("mcq", "vsa", "sa"), "simple"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la", "case_study")),
    Chapter(5, "Arithmetic Progressions", ("arithmetic progression", "ap", "arithmetic sequence"),
        ("common difference", "ap", "nth term", "sum", "first term", "sequence"),
        (
            Subtopic("general term of an AP", ("nth term", "general term"), ("ap", "nth", "term", "common difference"), ("vsa", "sa"), "simple"),
            Subtopic("sum of n terms of an AP", ("sum of ap", "sum of n terms"), ("sum", "ap", "n terms"), ("vsa", "sa", "la"), "medium"),
            Subtopic("arithmetic mean", ("arithmetic mean",), ("mean", "insert"), ("mcq", "vsa"), "simple"),
        ),
        suggested_types=("mcq", "vsa", "sa", "la")),
    Chapter(6, "Triangles", ("triangles",),
        ("similar", "congruent", "pythagoras", "thales", "basic proportionality", "ratio"),
        (
            Subtopic("similarity of triangles", ("similar triangles", "similarity"), ("similar", "corresponding", "ratio"), ("vsa", "sa", "la"), "medium"),
            Subtopic("basic proportionality theorem", ("thales theorem", "bpt"), ("proportionality", "ratio", "parallel"), ("sa", "la"), "hard"),
            Subtopic("criteria for similarity", ("aaa similarity", "sss similarity", "sas similarity"), ("aaa", "sss", "sas", "similar"), ("mcq", "vsa"), "simple"),
            Subtopic("pythagoras theorem", ("pythagoras", "pythagorean"), ("pythagoras", "right", "hypotenuse"), ("vsa", "sa", "la"), "medium"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la", "case_study")),
    Chapter(7, "Coordinate Geometry", ("coordinate geometry", "coordinate"),
        ("distance", "section", "midpoint", "area", "triangle", "collinear"),
        (
            Subtopic("distance formula", ("distance",), ("distance", "coordinates", "formula"), ("vsa", "sa", "la"), "simple"),
            Subtopic("section formula", ("section",), ("section", "ratio", "midpoint"), ("vsa", "sa", "la"), "medium"),
            Subtopic("area of triangle", ("area coordinate",), ("area", "triangle", "collinear"), ("vsa", "sa", "la", "case_study"), "medium"),
        ),
        suggested_types=("mcq", "vsa", "sa", "la", "case_study")),
    Chapter(8, "Introduction to Trigonometry", ("trigonometry", "trigonometric ratios"),
        ("sin", "cos", "tan", "cosec", "sec", "cot", "angle", "right triangle"),
        (
            Subtopic("trigonometric ratios", ("t-ratios",), ("sin", "cos", "tan", "ratio"), ("mcq", "vsa", "sa"), "simple"),
            Subtopic("trigonometric identities", ("identities",), ("identity", "proof", "sec", "cosec"), ("vsa", "sa", "la"), "hard"),
            Subtopic("trigonometric ratios of complementary angles", ("complementary",), ("complementary", "90"), ("mcq", "vsa"), "simple"),
            Subtopic("trigonometric table", ("trigonometric table",), ("table", "angle", "value"), ("mcq", "vsa"), "simple"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la")),
    Chapter(9, "Some Applications of Trigonometry", ("applications of trigonometry", "heights and distances"),
        ("line of sight", "angle of elevation", "angle of depression", "height", "distance"),
        (
            Subtopic("angle of elevation", ("elevation",), ("elevation", "height", "distance"), ("sa", "la", "case_study"), "medium"),
            Subtopic("angle of depression", ("depression",), ("depression", "height", "distance"), ("sa", "la", "case_study"), "medium"),
        ),
        suggested_types=("sa", "la", "case_study")),
    Chapter(10, "Circles", ("circles",),
        ("tangent", "radius", "secant", "theorem"),
        (
            Subtopic("tangent to a circle", ("tangent",), ("tangent", "radius", "perpendicular"), ("vsa", "sa", "la"), "medium"),
            Subtopic("number of tangents from a point", ("tangent from point",), ("external", "tangent", "length"), ("mcq", "vsa"), "simple"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la")),
    Chapter(11, "Constructions", ("constructions",),
        ("divide", "tangent", "triangle", "scale"),
        (
            Subtopic("division of line segment", ("divide segment",), ("divide", "ratio", "segment"), ("vsa", "sa"), "simple"),
            Subtopic("construction of tangents", ("construct tangent",), ("tangent", "circle", "construct"), ("sa", "la"), "medium"),
            Subtopic("construction of similar triangles", ("similar construction",), ("similar", "construct", "scale"), ("sa", "la"), "medium"),
        ),
        suggested_types=("vsa", "sa", "la")),
    Chapter(12, "Areas Related to Circles", ("areas related to circles", "area of circles"),
        ("circle", "sector", "segment", "area", "circumference", "arc"),
        (
            Subtopic("area of sector", ("sector",), ("sector", "area", "angle"), ("vsa", "sa"), "simple"),
            Subtopic("area of segment", ("segment",), ("segment", "area"), ("sa", "la"), "medium"),
            Subtopic("areas of combinations of figures", ("combination",), ("combination", "area", "shaded"), ("sa", "la", "case_study"), "hard"),
        ),
        suggested_types=("mcq", "vsa", "sa", "la", "case_study")),
    Chapter(13, "Surface Areas and Volumes", ("surface areas", "volumes"),
        ("cube", "cuboid", "cylinder", "cone", "sphere", "hemisphere", "frustum", "volume", "surface area"),
        (
            Subtopic("surface area of solids", ("surface area",), ("csa", "tsa", "lateral"), ("vsa", "sa"), "simple"),
            Subtopic("volume of solids", ("volume",), ("volume", "capacity"), ("vsa", "sa", "la"), "simple"),
            Subtopic("conversion of solids", ("conversion",), ("melt", "recast", "convert"), ("sa", "la"), "medium"),
            Subtopic("frustum of cone", ("frustum",), ("frustum", "cone", "volume"), ("sa", "la"), "hard"),
            Subtopic("combination of solids", ("combination solid",), ("combined", "total"), ("sa", "la", "case_study"), "hard"),
        ),
        suggested_types=("mcq", "vsa", "sa", "la", "case_study")),
    Chapter(14, "Statistics", ("statistics",),
        ("mean", "median", "mode", "ogive", "cumulative frequency", "class"),
        (
            Subtopic("mean of grouped data", ("mean",), ("mean", "direct method", "assumed mean", "step deviation"), ("vsa", "sa", "la"), "medium"),
            Subtopic("mode of grouped data", ("mode",), ("mode", "modal class"), ("vsa", "sa", "la"), "medium"),
            Subtopic("median of grouped data", ("median",), ("median", "cumulative frequency"), ("vsa", "sa", "la", "case_study"), "medium"),
            Subtopic("ogive and graphical representation", ("ogive", "cumulative frequency curve"), ("ogive", "cumulative", "graph"), ("sa", "la", "case_study"), "hard"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la", "case_study")),
    Chapter(15, "Probability", ("probability",),
        ("probability", "event", "outcome", "random", "dice", "card", "coin"),
        (
            Subtopic("probability basics", ("basic probability",), ("probability", "event", "outcome"), ("mcq", "vsa"), "simple"),
            Subtopic("complementary events", ("complementary",), ("complementary", "not", "p"), ("mcq", "vsa"), "simple"),
            Subtopic("applications of probability", ("real life probability",), ("coin", "die", "card", "ball"), ("vsa", "sa", "la", "case_study"), "medium"),
        ),
        suggested_types=("mcq", "assertion_reason", "vsa", "sa", "la", "case_study")),
)


def resolve(query: str) -> tuple[Chapter, Subtopic | None]:
    query_norm = _normalize(query)
    best_chapter: Chapter | None = None
    best_subtopic: Subtopic | None = None
    best_score = 0

    for ch in CHAPTERS:
        ch_terms = {_normalize(t) for t in (ch.name, *ch.aliases, *ch.focus_terms)}
        score = _phrase_score(query_norm, ch_terms)
        if score > best_score:
            best_chapter, best_subtopic, best_score = ch, None, score

        for sub in ch.subtopics:
            sub_terms = {_normalize(t) for t in (sub.name, *sub.aliases, *sub.focus_terms)}
            combined = ch_terms | sub_terms
            score = _phrase_score(query_norm, combined)
            if score > best_score:
                best_chapter, best_subtopic, best_score = ch, sub, score

    if best_chapter is None:
        best_chapter = CHAPTERS[0]

    return best_chapter, best_subtopic


def _phrase_score(query: str, terms: set[str]) -> float:
    score = 0.0
    for term in terms:
        if not term:
            continue
        if term == query:
            score += 4.0
        elif term in query:
            score += 2.0
    return score


def suggest_types(chapter: Chapter, subtopic: Subtopic | None = None,
                  marks: int | None = None) -> tuple[str, ...]:
    if subtopic:
        return subtopic.cbse_types
    if marks:
        return tuple(k for k, v in TYPE_MARKS_MAP.items() if v == marks)
    return chapter.suggested_types


def normalize_question_type(question_type: str) -> str:
    return QUESTION_TYPE_ALIASES.get(question_type, question_type)


def marks_for_type(question_type: str) -> int:
    question_type = normalize_question_type(question_type)
    return TYPE_MARKS_MAP.get(question_type, 3)


def hardness_from_marks(marks: int) -> str:
    for level, (lo, hi) in HARDNESS_MARKS.items():
        if lo <= marks <= hi:
            return level
    return "medium"


def list_chapters() -> list[dict[str, Any]]:
    return [
        {
            "number": ch.number,
            "name": ch.name,
            "aliases": list(ch.aliases),
            "subtopics": [s.name for s in ch.subtopics],
            "question_types": list(ch.suggested_types),
        }
        for ch in CHAPTERS
    ]


def list_question_types() -> list[dict[str, Any]]:
    return [
        {"type": t, "marks": TYPE_MARKS_MAP[t],
         "description": _TYPE_DESC[t], "example": _TYPE_EXAMPLE[t]}
        for t in CBSE_QUESTION_TYPES
    ]


_TYPE_DESC = {
    "mcq": "Multiple Choice Question — select correct option",
    "assertion_reason": "Assertion (A) and Reason (R) — mark correct option",
    "vsa": "Very Short Answer — 2-mark short response",
    "sa": "Short Answer — multi-step solution",
    "la": "Long Answer — detailed derivation and answer",
    "case_study": "Case Study — real-life scenario with 4-5 sub-questions",
}

_TYPE_EXAMPLE = {
    "mcq": "The HCF of 12 and 18 is:\n(A) 2  (B) 3  (C) 6  (D) 9",
    "assertion_reason": "Assertion (A): √2 is irrational.\nReason (R): √2 can be expressed as p/q.",
    "vsa": "Find the zeros of x² - 5x + 6 and verify the relationship.",
    "sa": "Solve 2x + 3y = 11 and x - 2y = -12 using elimination method.",
    "la": "Prove that √3 is irrational. A train travels 360 km at uniform speed...",
    "case_study": "A survey of 100 students was conducted... (4 sub-questions)",
}


def hardness_marks_range(hardness: str) -> tuple[int, int]:
    return HARDNESS_MARKS.get(hardness, (2, 3))

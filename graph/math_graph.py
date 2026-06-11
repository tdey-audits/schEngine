"""Simple knowledge graph for NCERT Class 10 Mathematics.

Nodes are concepts (chapters/subtopics/formulas).
Edges capture prerequisites, related concepts, and topical relationships.
Used by the generator to inject concept context into prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConceptNode:
    id: str
    name: str
    formulas: tuple[str, ...] = ()
    key_concepts: tuple[str, ...] = ()
    typical_patterns: tuple[str, ...] = ()
    hardness_hints: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ConceptEdge:
    source: str
    relation: str  # "prerequisite", "related", "builds_on"
    target: str


NODES: dict[str, ConceptNode] = {}

EDGES: list[ConceptEdge] = []


def _node(uid: str, name: str, formulas: tuple[str, ...] = (),
          key_concepts: tuple[str, ...] = (),
          typical_patterns: tuple[str, ...] = (),
          hardness_hints: dict[str, str] | None = None) -> ConceptNode:
    n = ConceptNode(
        id=uid,
        name=name,
        formulas=formulas,
        key_concepts=key_concepts,
        typical_patterns=typical_patterns,
        hardness_hints=hardness_hints or {},
    )
    NODES[uid] = n
    return n


def _edge(source: str, relation: str, target: str):
    EDGES.append(ConceptEdge(source=source, relation=relation, target=target))


# ── Real Numbers (Ch 1) ──────────────────────────────────────────────
_node("real_numbers", "Real Numbers",
    formulas=("hcf × lcm = a × b",),
    key_concepts=("Euclid's division lemma", "prime factorisation",
                  "irrational numbers", "terminating/non-terminating decimals"),
    typical_patterns=("find HCF/LCM using prime factorisation",
                      "prove √2/√3/√5 is irrational",
                      "check if decimal expansion terminates",
                      "word problem using Euclid's algorithm",
                      "find the largest number satisfying two remainder conditions",
                      "decide terminating decimal from prime factorisation of denominator",
                      "prove irrationality of an expression using contradiction",
                      "use HCF × LCM relation with one missing quantity"),
    hardness_hints={
        "simple": "Direct HCF/LCM computation, identifying rational/irrational",
        "medium": "Word problems using Euclid's algorithm, decimal expansion classification",
        "hard": "Exemplar-style proof or condition problem: contradiction for irrationality, remainder-based Euclid setup, or hidden use of HCF × LCM with clean numbers",
    })

# ── Polynomials (Ch 2) ──────────────────────────────────────────────
_node("polynomials", "Polynomials",
    formulas=("sum_of_zeros = -b/a", "product_of_zeros = c/a",
              "sum_of_zeros_cubic = -b/a", "product_of_zeros_cubic = -d/a",
              "sum_of_pairwise_products_cubic = c/a"),
    key_concepts=("degree of polynomial", "zeros of polynomial", "relationship between zeros and coefficients",
                  "division algorithm for polynomials"),
    typical_patterns=("find zeros of quadratic by factorisation",
                      "find polynomial given sum and product of zeros",
                      "division algorithm: p(x) = g(x)q(x) + r(x)",
                      "graphical meaning of zeros",
                      "find an unknown coefficient using a relation between zeros",
                      "construct a polynomial from transformed zeros such as reciprocals or shifted zeros",
                      "use division algorithm with an unknown remainder/coefficient condition",
                      "interpret number of zeros from a graph description"),
    hardness_hints={
        "simple": "Find zeros from factored form, identify degree",
        "medium": "Find polynomial from sum/product, division algorithm with small remainders",
        "hard": "Board-aligned challenge: unknown coefficient or transformed-zero relation requiring sum/product reasoning before routine calculation",
    })

# ── Linear Equations (Ch 3) ──────────────────────────────────────────
_node("linear_equations", "Pair of Linear Equations in Two Variables",
    formulas=("a₁x + b₁y = c₁", "a₂x + b₂y = c₂",
              "unique: a₁/a₂ ≠ b₁/b₂", "no solution: a₁/a₂ = b₁/b₂ ≠ c₁/c₂",
              "infinite: a₁/a₂ = b₁/b₂ = c₁/c₂",
              "x = (b₁c₂ - b₂c₁)/(a₁b₂ - a₂b₁)",
              "y = (c₁a₂ - c₂a₁)/(a₁b₂ - a₂b₁)"),
    key_concepts=("consistent vs inconsistent", "graphical method",
                  "substitution method", "elimination method",
                  "cross-multiplication method"),
    typical_patterns=("solve graphically and find intersection point",
                      "solve using substitution/elimination",
                      "word problem: ages, money, speeds",
                      "determine consistency without solving",
                      "find an unknown parameter for unique/no/infinite solutions",
                      "form equations from a condition where variables are not named directly",
                      "solve equations reducible to linear form",
                      "interpret solution as a real-world constraint and reject invalid values"),
    hardness_hints={
        "simple": "Solve given pair, identify consistent/inconsistent from ratios",
        "medium": "Word problems (ages, numbers) with 2 variables, solve by any method",
        "hard": "School pre-board challenge: parameter-based consistency, indirect word problems, or equations reducible to linear form without ugly arithmetic",
    })

# ── Quadratic Equations (Ch 4) ──────────────────────────────────────
_node("quadratic_equations", "Quadratic Equations",
    formulas=("x = [-b ± √(b² - 4ac)] / 2a", "D = b² - 4ac",
              "D > 0 → real distinct", "D = 0 → real equal", "D < 0 → no real roots",
              "sum_of_roots = -b/a", "product_of_roots = c/a"),
    key_concepts=("standard form ax²+bx+c=0", "factorisation method",
                  "completing the square", "quadratic formula",
                  "nature of roots (discriminant)"),
    typical_patterns=("solve by factorisation",
                      "solve by completing the square",
                      "solve using quadratic formula",
                      "find nature of roots without solving",
                      "word problem: area, speed, time, numbers",
                      "find an unknown coefficient from root nature",
                      "form a quadratic from a two-stage real-world condition",
                      "use sum/product of roots to derive a parameter relation",
                      "choose a valid root after interpreting the context"),
    hardness_hints={
        "simple": "Solve given quadratic, find discriminant, find nature of roots",
        "medium": "Word problems forming quadratic equations, completing the square",
        "hard": "Exemplar-style board challenge: hidden formation of quadratic or parameter from discriminant/root relation, with contextual rejection of invalid root",
    })

# ── Arithmetic Progressions (Ch 5) ──────────────────────────────────
_node("arithmetic_progressions", "Arithmetic Progressions",
    formulas=("aₙ = a + (n-1)d", "Sₙ = n/2 [2a + (n-1)d]",
              "Sₙ = n/2 (a + l)", "l = a + (n-1)d"),
    key_concepts=("common difference", "nth term", "sum of n terms",
                  "arithmetic mean"),
    typical_patterns=("find nth term given a and d",
                      "find sum of n terms",
                      "find a and d given two terms",
                      "word problem on AP (saving money, seating arrangement)",
                      "find number of terms from a sum condition",
                      "use two independent conditions to determine a and d",
                      "prove a derived sequence is or is not an AP",
                      "find missing terms using arithmetic mean relations"),
    hardness_hints={
        "simple": "Find nth term or sum with given a,d,n directly",
        "medium": "Find a,d from given conditions, word problems on AP",
        "hard": "Conceptual AP challenge: combine nth-term and sum constraints, infer number of terms, or prove/disprove AP behavior from a derived sequence",
    })

# ── Triangles (Ch 6) ────────────────────────────────────────────────
_node("triangles", "Triangles",
    formulas=("BPT: AD/DB = AE/EC", "Pythagoras: a² + b² = c²",
              "area_ratio = (side_ratio)²"),
    key_concepts=("similarity of triangles", "basic proportionality theorem",
                  "AAA, SSS, SAS similarity", "Pythagoras theorem",
                  "converse of Pythagoras theorem"),
    typical_patterns=("prove triangles are similar using criteria",
                      "find unknown side using BPT/proportionality",
                      "prove Pythagoras theorem",
                      "find height/distance using Pythagoras",
                      "prove a triangle is right using converse",
                      "combine similarity with area ratio",
                      "prove proportionality using an auxiliary parallel line",
                      "use two similar triangle pairs in one figure",
                      "derive an unknown length through chained ratios"),
    hardness_hints={
        "simple": "Identify similar triangles by given angles, apply Pythagoras directly",
        "medium": "Find unknown sides using similarity/Pythagoras, apply BPT",
        "hard": "Exemplar-style geometry: prove a hidden similarity/proportionality relation, combine two triangle results, or use area-ratio reasoning from similarity",
    })

# ── Coordinate Geometry (Ch 7) ─────────────────────────────────────
_node("coordinate_geometry", "Coordinate Geometry",
    formulas=("d = √[(x₂-x₁)² + (y₂-y₁)²]",
              "P(x,y) = [(m₁x₂+m₂x₁)/(m₁+m₂), (m₁y₂+m₂y₁)/(m₁+m₂)]",
              "midpoint = [(x₁+x₂)/2, (y₁+y₂)/2]",
              "area = ½|x₁(y₂-y₃) + x₂(y₃-y₁) + x₃(y₁-y₂)|"),
    key_concepts=("distance formula", "section formula", "midpoint formula",
                  "area of triangle", "collinearity"),
    typical_patterns=("find distance between points",
                      "find point dividing segment in given ratio",
                      "find if points are collinear",
                      "find area of triangle given vertices",
                      "find ratio in which point divides line",
                      "find an unknown coordinate from distance/area/collinearity condition",
                      "prove a quadrilateral type using distance formula",
                      "use area equality to find a missing coordinate",
                      "combine midpoint/section formula with another geometric condition"),
    hardness_hints={
        "simple": "Find distance/midpoint, find area of triangle",
        "medium": "Section formula with unknown ratio, check collinearity",
        "hard": "Board-aligned challenge: unknown coordinate or ratio from area, distance, collinearity, or quadrilateral classification conditions",
    })

# ── Trigonometry (Ch 8) ────────────────────────────────────────────
_node("trigonometry", "Introduction to Trigonometry",
    formulas=("sin²θ + cos²θ = 1", "1 + tan²θ = sec²θ",
              "1 + cot²θ = cosec²θ",
              "sin(90-θ) = cosθ", "tan(90-θ) = cotθ",
              "sec(90-θ) = cosecθ"),
    key_concepts=("trigonometric ratios (sin, cos, tan, cosec, sec, cot)",
                  "trigonometric identities",
                  "complementary angles"),
    typical_patterns=("find all T-ratios given one",
                      "prove trigonometric identities",
                      "evaluate expressions using complementary angles",
                      "find value of expression using identities",
                      "derive a hidden relation from a given ratio before evaluating",
                      "transform one side of an identity using reciprocal and Pythagorean identities",
                      "combine complementary-angle conversion with identities in one expression",
                      "compare two expressions after reducing both to sin/cos form"),
    hardness_hints={
        "simple": "Find T-ratio values, evaluate using complementary angles",
        "medium": "Simplify expressions using identities, prove basic identities",
        "hard": "Exemplar-style board challenge: indirect givens, hidden identity choice, complementary-angle transformation plus identity use, or proof by transforming one side without lengthy algebra",
    })

# ── Applications of Trigonometry (Ch 9) ───────────────────────────
_node("applications_trigonometry", "Some Applications of Trigonometry",
    formulas=("tanθ = opposite/adjacent",
              "angle_of_elevation: tanθ = height/distance",
              "angle_of_depression: tanθ = height/distance"),
    key_concepts=("line of sight", "angle of elevation", "angle of depression",
                  "height and distance problems"),
    typical_patterns=("find height given angle of elevation and distance",
                      "find distance given angle of depression",
                      "two-angle problem (find height from two elevations)",
                      "find height/distance with two observers",
                      "combine elevation and depression in a single diagram",
                      "find an unknown distance after eliminating the height",
                      "case-style setup with two observation points and one shared vertical object"),
    hardness_hints={
        "simple": "Find height/distance from single angle",
        "medium": "Two-angle problems, find height/distance using tan",
        "hard": "School-exam challenge: two linked right triangles, one hidden distance/height eliminated through simultaneous tan relations, clean standard angles only",
    })

# ── Circles (Ch 10) ────────────────────────────────────────────────
_node("circles", "Circles",
    formulas=("tangent ⟂ radius at point of contact",
              "tangents from external point are equal: PT₁ = PT₂"),
    key_concepts=("tangent to circle", "secant", "number of tangents from a point",
                  "tangent perpendicular to radius"),
    typical_patterns=("prove tangent is perpendicular to radius",
                      "find length of tangent from external point",
                      "find distance between centres given tangent length",
                      "prove lengths of tangents from external point equal",
                      "combine tangent equality with triangle congruence/similarity",
                      "find an unknown radius or distance using tangent plus Pythagoras",
                      "prove a quadrilateral formed by tangents has a required property",
                      "use two tangents from the same external point in a proof"),
    hardness_hints={
        "simple": "Find length of tangent using Pythagoras, identify tangents",
        "medium": "Prove tangent properties, find distance with tangent conditions",
        "hard": "Exemplar-style tangent proof: combine equal tangents, radius-perpendicular property, and triangle reasoning to derive an unknown or prove a relation",
    })

# ── Areas Related to Circles (Ch 12) ──────────────────────────────
_node("areas_circles", "Areas Related to Circles",
    formulas=("area = πr²", "circumference = 2πr",
              "sector_area = (θ/360) × πr²", "arc_length = (θ/360) × 2πr",
              "segment_area = sector_area - triangle_area"),
    key_concepts=("sector of circle", "segment of circle", "arc length",
                  "combinations of figures with circles"),
    typical_patterns=("find area of sector given radius and angle",
                      "find area of segment",
                      "find area of shaded region (combinations)",
                      "find area of designs involving circles",
                      "subtract sector/triangle/rectangle components to get a shaded region",
                      "find radius or angle from area/arc-length condition",
                      "combine semicircles or quadrants built on sides of a polygon",
                      "compare two areas after decomposing the same figure"),
    hardness_hints={
        "simple": "Find area/circumference, find sector area",
        "medium": "Find segment area, area of shaded regions from basic combinations",
        "hard": "School-exam challenge: decompose a shaded figure into standard parts, infer a missing radius/angle, or compare areas using clean sector/segment relations",
    })

# ── Surface Areas and Volumes (Ch 13) ──────────────────────────────
_node("surface_areas_volumes", "Surface Areas and Volumes",
    formulas=("cube: TSA=6a², V=a³", "cuboid: TSA=2(lb+bh+hl), V=lbh",
              "cylinder: CSA=2πrh, TSA=2πr(h+r), V=πr²h",
              "cone: CSA=πrl, TSA=πr(l+r), V=⅓πr²h",
              "sphere: SA=4πr², V=⁴⁄₃πr³",
              "hemisphere: CSA=2πr², TSA=3πr², V=⅔πr³",
              "frustum: V=⅓πh(R²+Rr+r²)",
              "l² = r² + h²"),
    key_concepts=("surface area of solids", "volume of solids",
                  "conversion of solids (melt and recast)",
                  "frustum of cone",
                  "combination of solids"),
    typical_patterns=("find CSA/TSA/volume of solid",
                      "find volume after melting and recasting",
                      "find dimensions after converting shape",
                      "volume of combination of solids",
                      "find height/slant height of frustum",
                      "combine two or more solids and subtract a hollow part",
                      "find an unknown dimension from equal-volume conversion",
                      "compare surface area before and after reshaping",
                      "use slant height relation before applying cone/frustum formula"),
    hardness_hints={
        "simple": "Direct CSA/TSA/volume computation from given dimensions",
        "medium": "Melt and recast problems, find unknown dimension given volume",
        "hard": "Board-aligned challenge: linked volume/surface-area conditions, frustum or combination of solids, or conversion where the unknown must be inferred before formula substitution",
    })

# ── Statistics (Ch 14) ──────────────────────────────────────────────
_node("statistics", "Statistics",
    formulas=("mean(direct) = Σfᵢxᵢ/Σfᵢ",
              "mean(assumed) = A + (Σfᵢdᵢ/Σfᵢ)",
              "mean(step) = A + h(Σfᵢuᵢ/Σfᵢ)",
              "mode = l + [(f₁-f₀)/(2f₁-f₀-f₂)] × h",
              "median = l + [(n/2 - cf)/f] × h"),
    key_concepts=("mean of grouped data", "mode of grouped data",
                  "median of grouped data", "cumulative frequency",
                  "ogive curves"),
    typical_patterns=("find mean using direct/assumed mean/step deviation method",
                      "find mode given frequency distribution",
                      "find median from cumulative frequency table",
                      "draw ogive and find median",
                      "find missing frequency given mean/mode/median",
                      "choose the efficient mean method from class intervals",
                      "convert raw grouped data to cumulative frequency before median",
                      "compare mean/median/mode for the same grouped distribution",
                      "infer a missing class frequency from total and central tendency"),
    hardness_hints={
        "simple": "Find mean by direct method, find mode from simple distribution",
        "medium": "Find mean by step deviation, find median, find missing frequency",
        "hard": "Exemplar-style statistics: missing-frequency or comparison problem requiring the correct central-tendency formula and one table transformation before calculation",
    })

# ── Probability (Ch 15) ────────────────────────────────────────────
_node("probability", "Probability",
    formulas=("P(E) = n(E)/n(S)", "P(E) + P(not E) = 1",
              "0 ≤ P(E) ≤ 1"),
    key_concepts=("probability of event", "complementary events",
                  "experimental vs theoretical probability",
                  "equally likely outcomes"),
    typical_patterns=("tossing one/two/three coins (combinations of heads/tails)",
                      "rolling one or two dice (sum, product, or difference conditions)",
                      "drawing a card from a deck (suit, face card, number, colour)",
                      "bag of coloured balls (find probability or find unknown count)",
                      "defective items in a lot (bulbs, pens, eggs, shirts)",
                      "selecting a number with a property (perfect square, prime, divisible)",
                      "complementary events (at least one, not equal to)",
                      "spinner / random ticket / dartboard scenarios",
                      "find probability through complement instead of direct counting",
                      "infer an unknown count from a given probability",
                      "combine two simple conditions using careful favourable-outcome counting",
                      "case-style random experiment from a real-life set"),
    hardness_hints={
        "simple": "Find probability of single random experiment (coin, die, ball)",
        "medium": "Find probability with conditions, complementary events, deck of cards",
        "hard": "School-exam challenge: complementary-event reasoning, unknown count from probability, or multi-condition favourable-outcome counting without compound probability rules",
    })

# ── Constructions (Ch 11) ──────────────────────────────────────────
_node("constructions", "Constructions",
    formulas=(),
    key_concepts=("division of line segment", "construction of tangents",
                  "construction of similar triangles"),
    typical_patterns=("divide line segment in given ratio",
                      "construct tangents to circle from external point",
                      "construct triangle similar to given triangle",
                      "construct a reduced/enlarged similar triangle with a given scale factor",
                      "justify construction steps using similarity or tangent properties",
                      "combine a triangle construction with a circle/tangent condition",
                      "identify required construction from a described target figure"),
    hardness_hints={
        "simple": "Divide segment in ratio, construct tangents",
        "medium": "Construct similar triangle with given scale factor",
        "hard": "Board-aligned construction challenge: combine similar-triangle construction with a tangent/circle condition and include a concise justification of why it works",
    })


# ── Edges: Prerequisites (directional) ──────────────────────────────
_edges = [
    ("real_numbers", "prerequisite", "polynomials"),
    ("polynomials", "prerequisite", "quadratic_equations"),
    ("linear_equations", "prerequisite", "quadratic_equations"),
    ("quadratic_equations", "prerequisite", "arithmetic_progressions"),
    ("triangles", "prerequisite", "coordinate_geometry"),
    ("triangles", "prerequisite", "trigonometry"),
    ("trigonometry", "prerequisite", "applications_trigonometry"),
    ("trigonometry", "prerequisite", "circles"),
    ("triangles", "prerequisite", "areas_circles"),
    ("areas_circles", "prerequisite", "surface_areas_volumes"),
    ("statistics", "prerequisite", "probability"),
    ("real_numbers", "builds_on", "linear_equations"),
    ("coordinate_geometry", "builds_on", "linear_equations"),
    ("quadratic_equations", "builds_on", "polynomials"),
    ("quadratic_equations", "builds_on", "linear_equations"),
]

for s, r, t in _edges:
    if s in NODES and t in NODES:
        _edge(s, r, t)

# Related edges (bidirectional topical relation)
_related_pairs = [
    ("surface_areas_volumes", "areas_circles"),
    ("coordinate_geometry", "triangles"),
    ("arithmetic_progressions", "statistics"),
    ("trigonometry", "applications_trigonometry"),
    ("real_numbers", "statistics"),
]
for a, b in _related_pairs:
    if a in NODES and b in NODES:
        _edge(a, "related", b)
        _edge(b, "related", a)


def get_node(node_id: str) -> ConceptNode | None:
    return NODES.get(node_id)


def find_node_by_name(name: str) -> ConceptNode | None:
    name_lower = name.lower()
    for node in NODES.values():
        if name_lower in node.name.lower():
            return node
    return None


def get_prerequisites(node_id: str) -> list[ConceptNode]:
    prereqs = []
    for edge in EDGES:
        if edge.target == node_id and edge.relation == "prerequisite":
            if edge.source in NODES:
                prereqs.append(NODES[edge.source])
    return prereqs


def get_builds_on(node_id: str) -> list[ConceptNode]:
    builds = []
    for edge in EDGES:
        if edge.target == node_id and edge.relation == "builds_on":
            if edge.source in NODES:
                builds.append(NODES[edge.source])
    return builds


def get_related(node_id: str) -> list[ConceptNode]:
    related = []
    for edge in EDGES:
        if edge.source == node_id and edge.relation == "related":
            if edge.target in NODES:
                related.append(NODES[edge.target])
    return related


def build_context(chapter_name: str, hardness: str) -> dict[str, Any]:
    node = find_node_by_name(chapter_name)
    if node is None:
        return {}

    prereqs = get_prerequisites(node.id)
    builds_on = get_builds_on(node.id)
    related = get_related(node.id)

    context: dict[str, Any] = {
        "main_concept": node.name,
        "formulas": node.formulas,
        "key_concepts": node.key_concepts,
        "typical_patterns": node.typical_patterns,
        "hardness_hint": node.hardness_hints.get(hardness, ""),
        "prerequisites": [p.name for p in prereqs],
        "builds_on": [b.name for b in builds_on],
        "related_concepts": [r.name for r in related],
    }
    return context

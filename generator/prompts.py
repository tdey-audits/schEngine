from typing import Any

QUESTION_TYPE_TEMPLATES = {
    "mcq": """QUESTION FORMAT: Multiple Choice (1 mark)
- 4 options labelled (A), (B), (C), (D)
- Exactly one correct option
- Include options array in JSON: "options": ["opt A", "opt B", "opt C", "opt D"]
- Answer in "answer" field (e.g. "(C)")""",

    "assertion_reason": """QUESTION FORMAT: Assertion-Reason (1 mark)
- Assertion (A): statement
- Reason (R): statement
- Options are:
  (A) Both A and R are true and R is the correct explanation of A
  (B) Both A and R are true but R is NOT the correct explanation of A
  (C) A is true but R is false
  (D) A is false but R is true
- Answer in "answer" field (e.g. "(A)")""",

    "vsa": """QUESTION FORMAT: Very Short Answer (2 marks)
- 2-step solution required
- Moderate difficulty
- Brief but complete reasoning""",

    "sa": """QUESTION FORMAT: Short Answer (3 marks)
- Multi-step solution (3-4 steps)
- Standard application problem
- Complete step-by-step reasoning""",

    "la": """QUESTION FORMAT: Long Answer (4-5 marks)
- Extended multi-step solution (5+ steps)
- Often includes real-world application
- Detailed derivation required
- May be a proof or complex word problem""",

    "case_study": """QUESTION FORMAT: Case Study (4 marks)
- Real-life scenario paragraph (3-4 lines)
- 4 sub-questions labelled (i), (ii), (iii), (iv)
- Each sub-question: 1 mark, mix of MCQ/VSA
- Sub-questions form: "questions": [{...}, {...}, {...}, {...}]
- Each sub-question has its own type, question, answer, solution""",
}

HARDNESS_GUIDES = {
    "simple": """HARDNESS: SIMPLE (1-2 marks)
- Direct recall or one-step application of a formula/concept
- Single step, clean numbers, answer falls out immediately
- Examples: find the discriminant, evaluate a T-ratio, compute HCF
- Style: straightforward formula substitution, no tricks
- Level: an average Class 10 student should solve it quickly""",

    "medium": """HARDNESS: MEDIUM (2-3 marks)
- Apply a concept in a typical NCERT-style problem
- 2-4 steps with moderate calculation
- Examples: a word problem forming a quadratic, find median from a table
- Style: standard exam problem with one clear line of reasoning
- Level: a prepared Class 10 student solves it with normal effort""",

    "hard": """HARDNESS: HARD (4-5 marks)
- The harder end of the NCERT textbook / board exam — NOT olympiad or HOTS
- Multi-step (4-6 steps): a word problem, a derivation, or a standard proof
- Uses ONLY Class 10 concepts; needs no unusual insight or trick
- Examples: solve a word problem that forms a quadratic, prove a standard theorem
  (e.g. BPT, irrationality of √2), a multi-step mensuration/combination problem
- Style: a well-set board exam question that a well-prepared student can solve
- Level: challenging but squarely within Class 10 CBSE syllabus""",
}

PAPER_LEVEL_GUIDES = {
    "standard": """PAPER DIFFICULTY BAND: STANDARD
- Match normal CBSE board-paper demand.
- Prefer direct or familiar NCERT/PYQ-style applications.
- Keep calculations clean and avoid artificial complexity.""",

    "medium": """PAPER DIFFICULTY BAND: MEDIUM
- Slightly above board-paper baseline, like a good school pre-board.
- Require one extra reasoning step before formula use.
- Use indirect givens, identity choice, or interpretation of a diagram/table.
- Stay fully within NCERT; do not make algebra lengthy just to look hard.""",

    "challenging": """PAPER DIFFICULTY BAND: CHALLENGING
- Make the question conceptually demanding but still CBSE Class 10 board-aligned.
- Require a non-obvious intermediate relation, identity choice, comparison, or transformation before the routine step.
- Prefer constraints that must be combined, e.g. two trig ratios/angles, complementary angles plus identity, or two right triangles in one height-distance setup.
- Avoid one-line substitutions such as "given one ratio, find another" unless the target expression hides the needed transformation.
- Avoid out-of-syllabus ideas, olympiad tricks, calculus, inverse trigonometry, or brute-force algebra.
- The difficulty should come from reasoning design, not from ugly arithmetic.""",
}

DIAGRAM_RULES = """DIAGRAM POLICY:
- For geometry/visual chapters, include a structured "diagram" object whenever a board-paper question would normally show a figure.
- Diagram-heavy chapters: Triangles, Coordinate Geometry, Some Applications of Trigonometry, Circles, Constructions, Areas Related to Circles, Surface Areas and Volumes, and Statistics ogive/graph questions.
- The diagram MUST match the exact labels, points, side names, angles, tangents, circles, axes, and measurements used in the question.
- Do NOT output TikZ, SVG, image URLs, base64, markdown images, or prose drawing instructions.
- If no diagram is needed, omit the "diagram" field.

Allowed diagram JSON shape:
"diagram": {
  "required": true,
  "type": "geometry|coordinate|trigonometry|circle|mensuration|construction",
  "caption": "optional short caption",
  "scale": 0.85,
  "elements": [
    {"kind": "point", "id": "A", "x": 0, "y": 0, "label": "A", "position": "below left"},
    {"kind": "segment", "from": "A", "to": "B", "label": "6 cm", "label_position": "below"},
    {"kind": "polygon", "points": ["A", "B", "C"]},
    {"kind": "circle", "center": "O", "radius": 2},
    {"kind": "arc", "center": "O", "radius": 2, "start_angle": 0, "end_angle": 90},
    {"kind": "angle", "points": ["A", "B", "C"], "label": "60^\\circ"},
    {"kind": "right_angle", "points": ["A", "B", "C"]},
    {"kind": "parallel_mark", "from": "D", "to": "E"},
    {"kind": "equal_mark", "from": "A", "to": "B"},
    {"kind": "axis"},
    {"kind": "grid"}
  ]
}

Diagram requirements:
- Every segment/angle/circle reference must use point ids defined in point elements.
- Coordinates are layout coordinates only; choose simple values that make the figure readable.
- For BPT/similarity questions, show the full triangle and the internal parallel segment.
- For tangent-circle questions, show centre, radius to point of contact, tangent, and external point.
- For height-and-distance questions, show ground, vertical object, line of sight, and angle mark.
- For coordinate geometry, show axes/grid and the plotted labelled points/polygon when useful.
"""

SYSTEM_PROMPT = """You are an expert CBSE Class 10 Mathematics question paper setter.
You generate high-quality exam-style questions based strictly on the NCERT syllabus.

OUTPUT FORMAT:
Return valid JSON per question with these fields:
{
  "question": "Question text with LaTeX math in $...$",
  "answer": "Final answer with LaTeX",
  "solution": {
    "steps": ["Step 1 explanation", "Step 2 explanation", ...],
    "derivation": "Line-by-line LaTeX derivation"
  },
  "topic": "Chapter name",
  "subtopic": "Specific topic name",
  "marks": 4,
  "type": "la",
  "difficulty": "hard",
  "options": ["(A) ...", "(B) ...", "(C) ...", "(D) ..."],  // only for MCQ
  "diagram": {"required": true, "type": "geometry", "elements": []}  // optional, only when a figure is needed
}

For case_study type:
{
  "question": "Scenario paragraph...",
  "type": "case_study",
  "marks": 4,
  "questions": [
    {"id": "i", "type": "mcq", "question": "...", "answer": "...", "options": [...]},
    {"id": "ii", "type": "vsa", "question": "...", "answer": "..."}
  ]
}

CRITICAL RULES:
- Every question MUST be from CBSE Class 10 NCERT syllabus only
- Question must be self-contained and unambiguous
- Provide complete step-by-step solution
- Match the question type format exactly
- For proof questions, the derivation must be complete
- DO NOT ask out-of-syllabus or advanced topics

LATEX FORMATTING RULES (follow EXACTLY — output is compiled with LaTeX):
- Wrap EVERY mathematical expression, symbol, variable, number-with-operator,
  fraction, power or root in $...$ . Even inline, e.g. write "the value of $x^2$",
  "in $\\triangle ABC$", "$D = b^2 - 4ac$". Never leave math outside $...$.
- Use $...$ for inline math ONLY. Do NOT use \\( \\), \\[ \\], $$...$$, or
  \\begin{align}/\\begin{aligned} anywhere.
- For the "derivation" field, write the steps as ONE string with lines separated
  by \\\\ , each line valid math, all inside a single $...$ — e.g.
  "$x^2 - 5x + 6 = 0 \\\\ (x-2)(x-3) = 0 \\\\ x = 2, 3$".
- Use LaTeX commands, NEVER unicode math symbols: write \\times not ×, \\div not ÷,
  \\Rightarrow not ⇒, \\geq not ≥, \\sqrt{} not √, \\pi not π, \\theta not θ,
  x^2 not x², a_1 not a₁, \\triangle not △, ^\\circ not °.
- Use \\\\ (double backslash) for line breaks, never a literal "\\n".
- For MCQ/Assertion-Reason, the "answer" field is ONLY the option label: "(C)".
"""

SCIENCE_SYSTEM_PROMPT = """You are an expert CBSE Class 10 Science question paper setter.
You generate high-quality exam-style questions based strictly on the NCERT syllabus.

OUTPUT FORMAT:
Return valid JSON per question with these fields:
{
  "question": "Question text with necessary scientific notation or equations",
  "answer": "Final answer",
  "solution": {
    "steps": ["Step 1 explanation", "Step 2 explanation", ...],
    "derivation": "Optional equation/process derivation"
  },
  "topic": "Chapter name",
  "subtopic": "Specific topic name",
  "marks": 4,
  "type": "la",
  "difficulty": "hard",
  "options": ["(A) ...", "(B) ...", "(C) ...", "(D) ..."]  // only for MCQ
}

For case_study type:
{
  "question": "Source/case paragraph...",
  "type": "case_study",
  "marks": 4,
  "questions": [
    {"id": "i", "type": "mcq", "question": "...", "answer": "...", "options": [...]},
    {"id": "ii", "type": "vsa", "question": "...", "answer": "..."}
  ]
}

CRITICAL RULES:
- Every question MUST be from CBSE Class 10 NCERT Science syllabus only
- Question must be self-contained and unambiguous
- Provide complete step-by-step solution or explanation
- Match the question type format exactly
- Prefer NCERT language, activities, observations, diagrams, reasoning, and applications
- DO NOT ask out-of-syllabus or advanced topics
- For MCQ/Assertion-Reason, the "answer" field is ONLY the option label: "(C)".
- Use LaTeX for every chemical formula, chemical equation, unit expression, physics
  formula, and calculation: "$H_2O$", "$Na_2CO_3$", "$Ca(OH)_2$".
- Use "$\\rightarrow$" for reaction arrows. Never use plain "->" in final output.
- In chemical equations, keep physical states inside math:
  "$CaO(s) + H_2O(l) \\rightarrow Ca(OH)_2(aq)$".
"""


def _format_chunks(retrieved_context: list[dict[str, Any]]) -> str:
    if not retrieved_context:
        return ""
    parts = ["REFERENCE CONTEXT FROM NCERT TEXTBOOK (style reference, DO NOT copy directly):"]
    for i, c in enumerate(retrieved_context, 1):
        text = c.get("text", "")[:500]
        source = c.get("source", "ncert")
        parts.append(f"\n--- Excerpt {i} ({source}) ---\n{text}\n")
    return "\n".join(parts)


def _format_kg_context(kg_context: dict[str, Any] | None) -> str:
    if not kg_context:
        return ""
    parts = ["KNOWLEDGE GRAPH CONTEXT (use as grounding):"]
    if kg_context.get("formulas"):
        parts.append("Key formulas: " + "; ".join(kg_context["formulas"]))
    if kg_context.get("key_concepts"):
        parts.append("Core concepts: " + ", ".join(kg_context["key_concepts"]))
    if kg_context.get("typical_patterns"):
        parts.append("Typical problem patterns (pick one):")
        for p in kg_context["typical_patterns"]:
            parts.append(f"- {p}")
    if kg_context.get("prerequisites"):
        parts.append("Prerequisite topics: " + ", ".join(kg_context["prerequisites"]))
    if kg_context.get("builds_on"):
        parts.append("Builds on: " + ", ".join(kg_context["builds_on"]))
    if kg_context.get("related_concepts"):
        parts.append("Related concepts: " + ", ".join(kg_context["related_concepts"]))
    if kg_context.get("hardness_hint"):
        parts.append(f"\nDifficulty-specific guidance: {kg_context['hardness_hint']}")
    return "\n".join(parts)


def _format_graph_rag_contexts(graph_contexts: dict[str, dict[str, Any]] | None,
                                difficulty: str | None = None) -> str:
    if not graph_contexts:
        return ""
    parts = ["KNOWLEDGE GRAPH CONTEXT (use as grounding):"]
    for cid, ctx in graph_contexts.items():
        label = ""
        if ctx.get("relation_to_primary") == "primary":
            label = " [PRIMARY CONCEPT]"
        relation = ctx.get("relation_to_primary", "related")
        parts.append(f"\nTopic: {ctx['name']}{label} ({relation})")
        if ctx.get("formulas"):
            parts.append("  Key formulas: " + "; ".join(ctx["formulas"][:5]))
        if ctx.get("key_concepts"):
            parts.append("  Core concepts: " + ", ".join(ctx["key_concepts"]))
        if ctx.get("typical_patterns"):
            parts.append("  Typical problem patterns:")
            for p in ctx["typical_patterns"]:
                parts.append(f"  - {p}")
        if ctx.get("source_patterns"):
            parts.append("  Source-derived question pattern nodes:")
            for p in ctx["source_patterns"]:
                parts.append(
                    f"  - {p.get('pattern')} [{p.get('relation')}, support={p.get('support')}]"
                )
                moves = p.get("reasoning_moves") or []
                if moves:
                    parts.append("    Reasoning moves: " + "; ".join(moves))
                qtypes = p.get("question_types") or {}
                if qtypes:
                    parts.append(
                        "    Seen as: " + ", ".join(f"{k}={v}" for k, v in qtypes.items())
                    )
        if difficulty and ctx.get("hardness_hint"):
            h = ctx["hardness_hint"].get(difficulty)
            if h:
                parts.append(f"  Difficulty guidance ({difficulty}): {h}")
        if ctx.get("reference_profiles"):
            parts.append("  Retrieved reference profiles:")
            for profile in ctx["reference_profiles"]:
                parts.append(f"  - {profile.get('role')}: {profile.get('use')}")
                if profile.get("reasoning_moves"):
                    parts.append("    Reasoning moves: " + "; ".join(profile["reasoning_moves"]))
                if profile.get("types"):
                    parts.append("    Question types: " + ", ".join(profile["types"]))
                if profile.get("depths"):
                    parts.append("    Depth labels: " + ", ".join(profile["depths"]))
    return "\n".join(parts)


def _format_pyq_context(pyq_context: list[dict[str, Any]] | None) -> str:
    if not pyq_context:
        return ""
    parts = [
        "CBSE PYQ PATTERN CONTEXT (style reference only, DO NOT copy or paraphrase directly):",
        "Use these only to match board-paper phrasing, mark depth, section style, and scenario complexity.",
        "Create new numbers, contexts, and wording.",
    ]
    for i, item in enumerate(pyq_context, 1):
        text = str(item.get("text", "")).strip()
        text = text[:900]
        source = item.get("source", "pyq")
        level = item.get("paper_level", "")
        qtype = item.get("question_type", "")
        marks = item.get("marks", "")
        qno = item.get("question_no", "")
        parts.append(
            f"\n--- PYQ Pattern {i} ({level}, {qtype}, {marks} mark(s), Q{qno}, {source}) ---\n{text}\n"
        )
    return "\n".join(parts)


def _format_exemplar_context(exemplar_context: list[dict[str, Any]] | None) -> str:
    if not exemplar_context:
        return ""
    parts = [
        "NCERT EXEMPLAR CONCEPTUAL DEPTH CONTEXT (board-aligned challenge reference only):",
        "Use these to raise conceptual demand while staying strictly inside Class 10 NCERT/CBSE scope.",
        "Do NOT copy or paraphrase directly. Create fresh values, contexts, and wording.",
        "The goal is Exemplar-like reasoning, not lengthy algebra, olympiad tricks, or out-of-syllabus ideas.",
    ]
    for i, item in enumerate(exemplar_context, 1):
        text = str(item.get("text", "")).strip()[:900]
        source = item.get("source", "ncert_exemplar")
        chapter = item.get("chapter", "")
        exercise = item.get("exercise", "")
        qtype = item.get("question_type", "")
        depth = item.get("estimated_depth", "")
        qno = item.get("question_no", "")
        parts.append(
            f"\n--- Exemplar Depth {i} ({chapter}, Ex {exercise}, {qtype}, {depth}, Q{qno}, {source}) ---\n{text}\n"
        )
    return "\n".join(parts)


def build_prompt(chapter: str, subtopic: str | None, question_type: str,
                 marks: int, count: int, retrieved_context: list[dict[str, Any]] | None = None,
                 kg_context: dict[str, Any] | None = None,
                 difficulty: str | None = None,
                 graph_rag_contexts: dict[str, dict[str, Any]] | None = None,
                 pyq_context: list[dict[str, Any]] | None = None,
                 exemplar_context: list[dict[str, Any]] | None = None,
                 paper_level: str | None = None,
                 subject: str = "maths") -> tuple[str, str]:
    topic_str = f"{chapter}" + (f" > {subtopic}" if subtopic else "")
    subject_label = "Science" if subject == "science" else "Mathematics"

    type_template = QUESTION_TYPE_TEMPLATES.get(question_type, "")
    hardness_guide = HARDNESS_GUIDES.get(difficulty or "medium", HARDNESS_GUIDES["medium"])
    paper_level_guide = PAPER_LEVEL_GUIDES.get(
        paper_level or "standard",
        PAPER_LEVEL_GUIDES["standard"],
    )

    context_str = _format_chunks(retrieved_context or [])
    pyq_str = _format_pyq_context(pyq_context or [])
    exemplar_str = _format_exemplar_context(exemplar_context or [])
    diagram_rules = DIAGRAM_RULES

    if graph_rag_contexts:
        kg_str = _format_graph_rag_contexts(graph_rag_contexts, difficulty)
    else:
        kg_str = _format_kg_context(kg_context)

    # The whole set is generated in one call, so uniqueness is enforced here by
    # asking the model to plan all N together — the way a paper-setter does.
    if count > 1:
        set_instruction = (
            f"Generate a practice SET of {count} DISTINCT questions.\n"
            f"The {count} questions MUST differ from each other: different real-world scenarios/"
            f"contexts, different numbers, and different sub-aspects of the topic. No two should "
            f"test the same idea in the same way. Vary them like a teacher building a worksheet."
        )
        output_instruction = (
            f'Output a single JSON object of the form {{"questions": [ ... ]}} '
            f"whose \"questions\" array holds exactly {count} question objects."
        )
    else:
        set_instruction = "Generate 1 CBSE exam-style question."
        output_instruction = "Output a single valid JSON object (the question)."

    user_prompt = f"""Generate {count} CBSE Class 10 {subject_label} question(s).

TOPIC: {topic_str}
QUESTION TYPE: {question_type}
MARKS: {marks}
DIFFICULTY LEVEL: {difficulty or "medium"}
PAPER LEVEL: {paper_level or "standard"}

{type_template}

{hardness_guide}

{paper_level_guide}

{diagram_rules}

{kg_str}

{context_str}

{pyq_str}

{exemplar_str}

{set_instruction}
All questions must be on "{topic_str}" and adhere strictly to the QUESTION FORMAT above.
Use NCERT/graph context for subject correctness. Use PYQ context only for exam pattern, not for source content.
Use Exemplar context only to tune conceptual depth for the requested paper level.
Do not copy PYQ or Exemplar questions, options, case-study scenarios, or numbers verbatim.
{output_instruction}"""

    system_prompt = SCIENCE_SYSTEM_PROMPT if subject == "science" else SYSTEM_PROMPT
    return system_prompt, user_prompt

import json
import logging
import uuid
import re
from datetime import datetime
from typing import Any

from config.settings import normalize_subject, settings
from generator.llm_client import LLMClient
from generator.prompts import build_prompt
from graph.graph_rag import GraphRAG
from rag.exemplar_retriever import ExemplarRetriever
from rag.pyq_retriever import PYQRetriever
from rag.retriever import Retriever
from syllabus.registry import (
    resolve, list_chapters, marks_for_type, hardness_from_marks,
    normalize_question_type,
)

logger = logging.getLogger(__name__)


class QuestionGenerator:
    def __init__(self):
        self.llm = LLMClient()
        self._retrievers = {}
        self._graph_rags = {}
        self._pyq_retrievers = {}
        self._exemplar_retrievers = {}
        self._rag_available = False

    def retriever(self, subject: str = "maths"):
        subject = normalize_subject(subject)
        if subject not in self._retrievers:
            try:
                self._retrievers[subject] = Retriever(subject=subject)
                self._rag_available = True
            except Exception as e:
                logger.warning(f"RAG not available: {e}")
                self._rag_available = False
        return self._retrievers.get(subject)

    def graph_rag(self, subject: str = "maths"):
        subject = normalize_subject(subject)
        if subject not in self._graph_rags:
            try:
                self._graph_rags[subject] = GraphRAG(subject=subject)
                self._rag_available = True
            except Exception as e:
                logger.warning(f"GraphRAG not available: {e}")
                self._rag_available = False
        return self._graph_rags.get(subject)

    def pyq_retriever(self, subject: str = "maths"):
        subject = normalize_subject(subject)
        if subject not in self._pyq_retrievers:
            self._pyq_retrievers[subject] = PYQRetriever(subject=subject)
        return self._pyq_retrievers[subject]

    def exemplar_retriever(self, subject: str = "maths"):
        subject = normalize_subject(subject)
        if subject not in self._exemplar_retrievers:
            self._exemplar_retrievers[subject] = ExemplarRetriever(subject=subject)
        return self._exemplar_retrievers[subject]

    def generate(self, topic: str, question_type: str = "sa",
                 marks: int | None = None, count: int = 1,
                 difficulty: str | None = None,
                 paper_level: str | None = "standard",
                 paper_variant: str | None = "standard",
                 use_pyq_patterns: bool = True,
                 subject: str = "maths") -> list[dict[str, Any]]:
        subject = normalize_subject(subject)
        count = max(1, min(count, 10))
        question_type = normalize_question_type(question_type, subject)
        chapter, subtopic = resolve(topic, subject)

        if marks is None:
            marks = marks_for_type(question_type, subject)

        if difficulty is None:
            difficulty = hardness_from_marks(marks, subject)

        query_terms = self._build_query(chapter, subtopic)
        graph_rag_result = self._retrieve_graph_context(
            query_terms, chapter.name, difficulty, question_type, paper_level, subject,
        )

        retrieved = graph_rag_result.get("chunks", [])
        graph_contexts = graph_rag_result.get("graph_contexts", {})
        pyq_context = self._retrieve_pyq_patterns(
            query_terms, question_type, paper_variant, enabled=use_pyq_patterns, subject=subject,
        )
        exemplar_context = self._retrieve_exemplar_depth(
            query_terms, chapter.name, question_type, paper_level, subject=subject,
        )
        graph_contexts = self._attach_reference_profiles(
            graph_contexts, pyq_context, exemplar_context, paper_level,
        )

        # Generate the whole set in a single call. Shown all N at once, the model
        # varies them like a human paper-setter would — far more diverse than
        # stitching N independent calls together.
        system_prompt, user_prompt = build_prompt(
            chapter=chapter.name,
            subtopic=subtopic.name if subtopic else None,
            question_type=question_type,
            marks=marks,
            count=count,
            retrieved_context=retrieved,
            difficulty=difficulty,
            graph_rag_contexts=graph_contexts if graph_contexts else None,
            pyq_context=pyq_context,
            exemplar_context=exemplar_context,
            paper_level=paper_level,
            subject=subject,
        )

        response_text = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )

        parsed = self._parse_response(response_text)
        questions: list[dict[str, Any]] = [
            self._normalize(q, chapter.name, subtopic.name if subtopic else None,
                            question_type, marks, difficulty, subject)
            for q in parsed
        ]

        questions = self._deduplicate(questions)

        # renumber ids within the batch
        ts_base = datetime.now().strftime('%Y%m%d_%H%M%S')
        for j, q in enumerate(questions):
            q["id"] = f"ncert_{subject}_{ts_base}_{uuid.uuid4().hex[:6]}_{j+1:02d}"

        if retrieved:
            for q in questions:
                q["metadata"]["retrieved_sources"] = list(
                    dict.fromkeys(r.get("source", "") for r in retrieved)
                )
        if pyq_context:
            for q in questions:
                q["metadata"]["pyq_pattern_sources"] = [
                    {
                        "source": r.get("source", ""),
                        "question_no": r.get("question_no"),
                        "paper_variant": r.get("paper_level"),
                        "question_type": r.get("question_type"),
                    }
                    for r in pyq_context
                ]
        if exemplar_context:
            for q in questions:
                q["metadata"]["exemplar_depth_sources"] = [
                    {
                        "source": r.get("source", ""),
                        "chapter": r.get("chapter"),
                        "exercise": r.get("exercise"),
                        "question_no": r.get("question_no"),
                        "question_type": r.get("question_type"),
                        "estimated_depth": r.get("estimated_depth"),
                    }
                    for r in exemplar_context
                ]

        self._save_batch(questions, chapter.name, subtopic.name if subtopic else None)
        return questions

    def generate_from_syllabus(self, chapter_number: int | None = None,
                                subtopic_name: str | None = None,
                                question_type: str = "sa",
                                marks: int | None = None,
                                count: int = 1,
                                difficulty: str | None = None,
                                paper_level: str | None = "standard",
                                paper_variant: str | None = "standard",
                                use_pyq_patterns: bool = True,
                                subject: str = "maths") -> list[dict[str, Any]]:
        subject = normalize_subject(subject)
        chapters = list_chapters(subject)
        if chapter_number:
            ch = next((c for c in chapters if c["number"] == chapter_number), chapters[0])
        else:
            ch = chapters[0]
        topic = ch["name"]
        if subtopic_name:
            topic = f"{ch['name']} {subtopic_name}"
        return self.generate(topic, question_type, marks, count, difficulty,
                             paper_level=paper_level,
                             paper_variant=paper_variant,
                             use_pyq_patterns=use_pyq_patterns,
                             subject=subject)

    def _build_query(self, chapter: Any, subtopic: Any) -> str:
        # Retrieval query is just the topic; question-type codes and the word
        # "CBSE" are noise to a semantic embedding and pull worse chunks.
        parts = [chapter.name]
        if subtopic:
            parts.append(subtopic.name)
        return " ".join(parts)

    def _deduplicate(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for q in questions:
            key = re.sub(r"\s+", " ", q.get("question", "")).strip().lower()[:120]
            if key and key in seen:
                logger.info(f"Dropping duplicate question: {key[:60]!r}")
                continue
            seen.add(key)
            unique.append(q)
        return unique

    def _retrieve_graph_context(self, query: str, chapter: str,
                                 difficulty: str,
                                 question_type: str | None = None,
                                 paper_level: str | None = None,
                                 subject: str = "maths") -> dict[str, Any]:
        try:
            graph_rag = self.graph_rag(subject)
            if graph_rag is None:
                return {"chunks": [], "graph_contexts": {}}
            return graph_rag.retrieve(
                query=query,
                top_k=settings.top_k_retrieved,
                chapter_filter=chapter,
                expand_depth=1,
                question_type=question_type,
                paper_level=paper_level,
            )
        except Exception as e:
            logger.warning(f"GraphRAG retrieval failed: {e}")
            return {"chunks": [], "graph_contexts": {}}

    def _retrieve_pyq_patterns(self, query: str, question_type: str,
                               paper_variant: str | None,
                               enabled: bool = True,
                               subject: str = "maths") -> list[dict[str, Any]]:
        if not enabled:
            return []
        subject = normalize_subject(subject)
        pyq_type = self._pyq_type_for(question_type)
        variant = paper_variant if subject == "maths" else None
        try:
            rows = self.pyq_retriever(subject).retrieve(
                query=query,
                top_k=3,
                paper_level=variant,
                question_type=pyq_type,
            )
            if not rows and variant:
                rows = self.pyq_retriever(subject).retrieve(
                    query=query,
                    top_k=3,
                    paper_level=None,
                    question_type=pyq_type,
                )
            return rows
        except Exception as e:
            logger.warning(f"PYQ pattern retrieval failed: {e}")
            return []

    def _retrieve_exemplar_depth(self, query: str, chapter: str, question_type: str,
                                 paper_level: str | None,
                                 subject: str = "maths") -> list[dict[str, Any]]:
        level = (paper_level or "standard").lower()
        if level == "standard":
            return []

        desired_depth = "challenging" if level == "challenging" else None
        top_k = 6 if level == "challenging" else 3
        try:
            rows = self.exemplar_retriever(subject).retrieve(
                query=query,
                top_k=top_k,
                chapter=chapter,
                question_type=question_type,
                estimated_depth=desired_depth,
            )
            if not rows:
                rows = self.exemplar_retriever(subject).retrieve(
                    query=query,
                    top_k=top_k,
                    chapter=chapter,
                    question_type=None,
                    estimated_depth=desired_depth,
                )
            if not rows:
                rows = self.exemplar_retriever(subject).retrieve(
                    query=query,
                    top_k=top_k,
                    chapter=None,
                    question_type=question_type,
                    estimated_depth=desired_depth,
                )
            return rows
        except Exception as e:
            logger.warning(f"NCERT Exemplar retrieval failed: {e}")
            return []

    def _attach_reference_profiles(self, graph_contexts: dict[str, dict[str, Any]],
                                   pyq_context: list[dict[str, Any]],
                                   exemplar_context: list[dict[str, Any]],
                                   paper_level: str | None) -> dict[str, dict[str, Any]]:
        if not graph_contexts:
            return graph_contexts

        primary = next(
            (ctx for ctx in graph_contexts.values() if ctx.get("relation_to_primary") == "primary"),
            next(iter(graph_contexts.values())),
        )
        profiles: list[dict[str, Any]] = []

        if pyq_context:
            profiles.append({
                "role": "PYQ pattern",
                "use": "board phrasing, section style, mark depth, and realistic constraint density",
                "types": sorted({str(r.get("question_type", "")) for r in pyq_context if r.get("question_type")}),
                "paper_variants": sorted({str(r.get("paper_level", "")) for r in pyq_context if r.get("paper_level")}),
            })

        if exemplar_context:
            moves = []
            for row in exemplar_context:
                moves.extend(self._infer_exemplar_moves(str(row.get("text", ""))))
            profiles.append({
                "role": "NCERT Exemplar conceptual depth",
                "use": "raise reasoning demand while staying strictly board-aligned",
                "paper_level": paper_level or "standard",
                "types": sorted({str(r.get("question_type", "")) for r in exemplar_context if r.get("question_type")}),
                "depths": sorted({str(r.get("estimated_depth", "")) for r in exemplar_context if r.get("estimated_depth")}),
                "reasoning_moves": list(dict.fromkeys(moves))[:6],
            })

        if profiles:
            primary["reference_profiles"] = profiles
        return graph_contexts

    def _infer_exemplar_moves(self, text: str) -> list[str]:
        lower = text.lower()
        moves = []
        if "prove" in lower or "show that" in lower:
            moves.append("prove a non-obvious identity by transforming one side")
        if "evaluate" in lower or "find the value" in lower:
            moves.append("evaluate through identities before substitution")
        if "tan" in lower and ("sin" in lower or "cos" in lower):
            moves.append("connect ratios through $\\sin^2\\theta + \\cos^2\\theta = 1$")
        if "90" in lower or "complement" in lower:
            moves.append("use complementary-angle conversion")
        if "if" in lower and ("=" in lower or "\\frac" in lower):
            moves.append("derive an intermediate relation from the given condition")
        if "angle of elevation" in lower or "angle of depression" in lower:
            moves.append("combine two right triangles from one real-world setup")
        return moves or ["require one intermediate reasoning step before applying a formula"]

    def _pyq_type_for(self, question_type: str) -> str:
        return normalize_question_type(question_type)

    @staticmethod
    def _fix_json_escapes(text: str) -> str:
        valid_escapes = {"n", "t", "r", "b", "f", '"', "/", "u"}
        result = []
        i = 0
        while i < len(text):
            if text[i] != "\\":
                result.append(text[i])
                i += 1
                continue
            # text[i] == backslash
            if i + 1 >= len(text):
                result.append(text[i])
                break
            nxt = text[i + 1]
            if nxt == "\\":
                # Already properly escaped backslash — pass through as-is
                result.append("\\\\")
                i += 2
                continue
            if nxt == "n" or nxt == "t" or nxt == "r":
                # Valid JSON control escapes
                result.append("\\" + nxt)
                i += 2
                continue
            if nxt.isalpha():
                # LaTeX command \sin, \circ, \angle etc. — must be \\sin, \\circ, \\angle
                j = i + 1
                while j < len(text) and text[j].isalpha():
                    j += 1
                result.append("\\\\" + text[i + 1:j])
                i = j
                continue
            # Any other backslash combo — pass through
            result.append(text[i])
            i += 1
        return "".join(result)

    def _parse_response(self, text: str) -> list[dict[str, Any]]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()

        def try_parse(s: str):
            s = self._fix_json_escapes(s)
            return json.loads(s)

        try:
            parsed = try_parse(text)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                try:
                    parsed = try_parse(match.group(0))
                except json.JSONDecodeError:
                    return []
            else:
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    try:
                        parsed = try_parse(match.group(0))
                    except json.JSONDecodeError:
                        return []
                else:
                    return []

        if isinstance(parsed, dict):
            # A batch wrapper {"questions": [...]} holds a list of full questions.
            # Distinguish it from a single case_study object, which ALSO has a
            # "questions" key (its sub-questions) but carries its own top-level
            # "question"/"type" — those must be preserved whole, not unwrapped.
            qs = parsed.get("questions")
            if isinstance(qs, list) and "question" not in parsed and "type" not in parsed:
                return qs
            return [parsed]
        if isinstance(parsed, list):
            return parsed
        return []

    def _normalize(self, q: dict[str, Any], chapter: str, subtopic: str | None,
                   question_type: str, marks: int, difficulty: str,
                   subject: str = "maths") -> dict[str, Any]:
        if "question" not in q:
            q["question"] = q.get("text", "")
        q["topic"] = q.get("topic") or chapter
        q["subtopic"] = q.get("subtopic") or subtopic or ""
        q["type"] = normalize_question_type(q.get("type") or question_type, subject)
        q["marks"] = q.get("marks") or marks
        q["difficulty"] = q.get("difficulty") or difficulty
        # For MCQ / Assertion-Reason the answer is just the option label.
        # Strip any trailing option text the model appended, e.g. "(C) $16-24$" -> "(C)".
        if q["type"] in ("mcq", "assertion_reason"):
            m = re.match(r"\s*\(([A-Da-d])\)", str(q.get("answer", "")))
            if m:
                q["answer"] = f"({m.group(1).upper()})"
        if "metadata" not in q:
            q["metadata"] = {}
        q["metadata"]["generated_at"] = datetime.now().isoformat()
        q["metadata"]["model"] = settings.llm_model
        q["metadata"]["subject"] = subject
        q["id"] = f"ncert_{subject}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        return q

    def _save_batch(self, questions: list[dict[str, Any]], chapter: str, subtopic: str | None):
        from pathlib import Path
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_id = f"{ts}_{uuid.uuid4().hex[:8]}"
        batch = {
            "batch_id": batch_id,
            "generated_at": datetime.now().isoformat(),
            "model": settings.llm_model,
            "provider": settings.llm_provider,
            "chapter": chapter,
            "subtopic": subtopic,
            "difficulty": questions[0].get("difficulty") if questions else None,
            "question_type": questions[0].get("type") if questions else None,
            "question_count": len(questions),
            "mechanisms": [q.get("metadata", {}).get("mechanism") for q in questions],
            "subject": questions[0].get("metadata", {}).get("subject") if questions else None,
            "questions": questions,
        }
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{batch_id}.json"
        path.write_text(json.dumps(batch, indent=2))
        logger.info(f"Saved {len(questions)} questions to {path}")
        self._append_to_generations_log(batch, str(path))

    def _append_to_generations_log(self, batch: dict[str, Any], path: str):
        from pathlib import Path
        output_dir = Path(settings.output_dir)
        log_path = output_dir / "generations.json"
        entry = {k: batch[k] for k in (
            "batch_id", "generated_at", "model", "provider",
            "chapter", "subtopic", "difficulty", "question_type",
            "question_count", "mechanisms",
        )}
        entry["subject"] = batch.get("subject")
        entry["file"] = path
        if log_path.exists():
            log = json.loads(log_path.read_text())
        else:
            log = []
        log.append(entry)
        log_path.write_text(json.dumps(log, indent=2))
        logger.info(f"Generation logged: {log_path} ({len(log)} total)")

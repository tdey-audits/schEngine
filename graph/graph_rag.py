"""Graph RAG — integrates knowledge graph traversal with vector search."""

import logging
from typing import Any

from config.settings import settings
from graph.math_graph import (
    NODES, EDGES, ConceptNode, find_node_by_name,
    get_prerequisites, get_builds_on, get_related,
)
from graph.source_pattern_graph import get_source_patterns
from ingest.embedder import Embedder
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class GraphRAG:
    def __init__(self, store: VectorStore | None = None,
                 embedder: Embedder | None = None):
        self._store = store
        self._embedder = embedder

    @property
    def store(self) -> VectorStore:
        if self._store is None:
            self._store = VectorStore(
                dim=settings.embedding_dim,
                index_path=settings.faiss_index_path,
                meta_path=settings.faiss_metadata_path,
            )
        return self._store

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder(model_name=settings.embedding_model)
        return self._embedder

    def retrieve(self, query: str, top_k: int = 5,
                 chapter_filter: str | None = None,
                 expand_depth: int = 1,
                 question_type: str | None = None,
                 paper_level: str | None = None) -> dict[str, Any]:
        primary_concept = self._resolve_concept(query, chapter_filter)

        expanded_nodes = self._expand_concepts(primary_concept, depth=expand_depth)

        search_queries = self._build_search_queries(query, expanded_nodes)
        all_results = self._multi_query_search(search_queries, top_k=top_k * 2)

        final_results = self._rerank_by_graph(
            all_results, primary_concept, expanded_nodes, top_k,
        )

        graph_contexts = self._build_graph_contexts(
            primary_concept, expanded_nodes,
            question_type=question_type,
            paper_level=paper_level,
        )

        return {
            "chunks": final_results,
            "primary_concept": primary_concept,
            "expanded_concepts": [n.name for n in expanded_nodes],
            "graph_contexts": graph_contexts,
        }

    def build_prompt_context(self, query: str, top_k: int = 5,
                             chapter_filter: str | None = None,
                             difficulty: str | None = None) -> str:
        result = self.retrieve(query, top_k=top_k, chapter_filter=chapter_filter)
        parts = []

        if result["graph_contexts"]:
            ctx_parts = ["KNOWLEDGE GRAPH CONTEXT (use as grounding):"]
            primary = result["primary_concept"]
            for cid, ctx in result["graph_contexts"].items():
                label = " [PRIMARY]" if primary and cid == primary.id else ""
                relation = ctx.get("relation_to_primary", "related")
                ctx_parts.append(f"\nTopic: {ctx['name']}{label} ({relation})")
                if ctx["formulas"]:
                    ctx_parts.append("  Formulas: " + "; ".join(ctx["formulas"]))
                if ctx["key_concepts"]:
                    ctx_parts.append("  Key concepts: " + ", ".join(ctx["key_concepts"]))
                if ctx["typical_patterns"]:
                    ctx_parts.append("  Typical patterns:")
                    for p in ctx["typical_patterns"]:
                        ctx_parts.append(f"  - {p}")
                if ctx.get("source_patterns"):
                    ctx_parts.append("  Source-derived patterns:")
                    for p in ctx["source_patterns"]:
                        ctx_parts.append(
                            f"  - {p['pattern']} ({p['relation']}, support={p['support']})"
                        )
                        moves = p.get("reasoning_moves") or []
                        if moves:
                            ctx_parts.append("    Moves: " + "; ".join(moves))
                if difficulty and ctx.get("hardness_hint"):
                    h = ctx["hardness_hint"].get(difficulty)
                    if h:
                        ctx_parts.append(f"  Difficulty guidance ({difficulty}): {h}")
            parts.append("\n".join(ctx_parts))

        if result["chunks"]:
            chunk_parts = ["\nREFERENCE CONTEXT FROM NCERT TEXTBOOK (style reference, DO NOT copy directly):"]
            for i, c in enumerate(result["chunks"], 1):
                text = c.get("text", "")[:500]
                source = c.get("source", "ncert")
                chunk_parts.append(f"\n--- Excerpt {i} ({source}) ---\n{text}")
            parts.append("\n".join(chunk_parts))

        for r in result["chunks"]:
            r.pop("graph_boost", None)
            r.pop("combined_score", None)

        return "\n".join(parts), result["chunks"], result.get("graph_contexts", {})

    def _resolve_concept(self, query: str, chapter_filter: str | None = None) -> ConceptNode | None:
        name = chapter_filter or query
        node = find_node_by_name(name)
        if node:
            return node
        for n in NODES.values():
            for keyword in n.key_concepts:
                if keyword.lower() in query.lower():
                    return n
        return None

    def _expand_concepts(self, node: ConceptNode | None, depth: int = 1) -> list[ConceptNode]:
        if node is None:
            return []

        seen = {node.id}
        result = []
        queue = [node]

        for _ in range(depth):
            current = queue
            queue = []
            for n in current:
                for neighbor_fn in (get_prerequisites, get_builds_on, get_related):
                    for neighbor in neighbor_fn(n.id):
                        if neighbor.id not in seen:
                            seen.add(neighbor.id)
                            result.append(neighbor)
                            queue.append(neighbor)
        return result

    def _build_search_queries(self, query: str, expanded_nodes: list[ConceptNode]) -> list[str]:
        queries = [query]
        for node in expanded_nodes:
            name_lower = node.name.lower()
            if name_lower not in query.lower():
                queries.append(f"{query} {node.name}")
        return queries

    def _multi_query_search(self, queries: list[str], top_k: int) -> list[dict[str, Any]]:
        all_results = []
        seen_texts = set()

        for q in queries:
            qv = self.embedder.embed(q)
            results = self.store.search(qv, k=top_k)
            for r in results:
                text = r.get("text", "")
                if text not in seen_texts:
                    seen_texts.add(text)
                    all_results.append(r)
        return all_results

    def _rerank_by_graph(self, results: list[dict[str, Any]],
                         primary: ConceptNode | None,
                         expanded: list[ConceptNode],
                         top_k: int) -> list[dict[str, Any]]:
        expanded_names = {n.name.lower() for n in expanded}
        if primary:
            expanded_names.add(primary.name.lower())

        for r in results:
            chapter = r.get("chapter", "").lower()
            boost = 1.0
            for ename in expanded_names:
                if ename in chapter or chapter in ename:
                    boost = 2.0
                    break
            if primary and primary.name.lower() in chapter:
                boost = 3.0
            r["graph_boost"] = boost
            r["combined_score"] = r.get("score", 0) * boost

        results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        return results[:top_k]

    def _build_graph_contexts(self, primary: ConceptNode | None,
                               expanded: list[ConceptNode],
                               question_type: str | None = None,
                               paper_level: str | None = None) -> dict[str, dict[str, Any]]:
        contexts = {}
        primary_id = primary.id if primary else None

        all_nodes = [primary] if primary else []
        all_nodes.extend(expanded)
        seen_ids = set()

        for node in all_nodes:
            if node is None or node.id in seen_ids:
                continue
            seen_ids.add(node.id)
            contexts[node.id] = {
                "id": node.id,
                "name": node.name,
                "formulas": list(node.formulas),
                "key_concepts": list(node.key_concepts),
                "typical_patterns": list(node.typical_patterns),
                "source_patterns": get_source_patterns(
                    node.name,
                    question_type=question_type,
                    paper_level=paper_level,
                    limit=6 if node.id == primary_id else 3,
                ),
                "hardness_hint": dict(node.hardness_hints),
                "relation_to_primary": (
                    self._get_relation(primary_id, node.id) if primary_id and node.id != primary_id else "primary"
                ),
            }
        return contexts

    def _get_relation(self, source_id: str, target_id: str) -> str:
        for edge in EDGES:
            if edge.source == source_id and edge.target == target_id:
                return edge.relation
            if edge.source == target_id and edge.target == source_id:
                return f"reverse_{edge.relation}"
        return "related"

# schEngine — CBSE Class 10 Math Question Generator

Generate NCERT-aligned CBSE exam papers with RAG, knowledge graph, CBSE question types, difficulty bands, and PDF export.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest NCERT PDFs (run once)
python3 ingest.py

# Optional reference corpora
python3 ingest_pyqs.py
python3 ingest_exemplar.py

# Generate questions
python3 generate.py --topic "Quadratic Equations" --type la --marks 5 --count 5 --pdf
python3 generate.py --topic "Quadratic Equations" --type mcq --count 10 --pdf
python3 generate.py --topic "Trigonometry" --type sa --paper-level challenging --pdf

# Full paper
python3 generate.py --paper --paper-level medium --pdf
```

## Features

| Feature | Description |
|---------|-------------|
| **RAG** | FAISS vector store (all-MiniLM-L6-v2) over all 14 NCERT Class 10 Math PDFs |
| **Knowledge Graph** | 15 concept nodes with formulas, patterns, hardness hints, prerequisite edges |
| **6 CBSE Question Types** | mcq, assertion_reason, vsa, sa, la, case_study |
| **Hardness Levels** | simple / medium / hard — maps cleanly to mark bands |
| **Paper Difficulty Bands** | standard / medium / challenging — standard uses NCERT + graph + PYQ pattern; medium/challenging also retrieve Exemplar conceptual depth |
| **PYQ Pattern Corpus** | CBSE Basic/Standard PYQs are retrieved only as paper-style references, not chapter content |
| **Exemplar Depth Corpus** | NCERT Exemplar is retrieved separately for board-aligned conceptual challenge |
| **Pattern Rotation** | Rotates through KG typical_patterns to prevent repeated question setups |
| **Diversity Injection** | Tracks used mechanisms across a batch, injects avoidance into subsequent prompts |
| **PDF Export** | `exam` document class with CBSE sections A–E, proper inline/display math |
| **CLI + API** | `generate.py` CLI and FastAPI server |
| **Validators** | Structural checks per question type |

## Usage

### CLI

```bash
python3 generate.py --topic "Quadratic Equations" --type la --marks 5 --count 5 --pdf
python3 generate.py --topic "Real Numbers" --type assertion_reason --count 5
python3 generate.py --topic "Triangles" --type case_study --count 2 --pdf
```

Options:
- `--topic` — Chapter name or "Chapter Subtopic" (e.g. "Quadratic Equations", "Real Numbers Euclid division lemma")
- `--type` — Question type: mcq, assertion_reason, vsa, sa, la, case_study
- `--marks` — Override marks (defaults from type)
- `--count` — Number of questions (1–10)
- `--difficulty` — simple, medium, hard
- `--paper-level` — standard, medium, challenging; controls overall conceptual demand
- `--paper-variant` — standard, basic; controls PYQ Basic/Standard pattern retrieval
- `--pdf` — Export question paper and answer key PDFs to `pdfs/`
- `--paper` — Generate full CBSE paper: `python3 generate.py --paper --paper-level medium --pdf`

Export rules:
- PDFs use short project-level names, e.g. `trig_chal_std_qp.pdf`
- JSON metadata is written under `output/`, not under `pdfs/`
- Markdown question papers and answer keys are not exported

### API

```bash
uvicorn api.main:app --reload
```

POST `/generate` with JSON body:
```json
{
  "topic": "Quadratic Equations",
  "question_type": "la",
  "marks": 5,
  "count": 5,
  "difficulty": "hard",
  "paper_level": "challenging",
  "paper_variant": "standard"
}
```

## Project Structure

```
schEngine/
├── api/              # FastAPI server
├── config/           # Settings (env, provider, model)
├── data/             # FAISS index + metadata
├── generator/        # Core: resolve → RAG → KG → prompt → LLM → parse → normalize
│   ├── generator.py  # Main orchestrator + pattern rotation + diversity tracking
│   ├── prompts.py    # System/user prompts with CBSE templates + hardness guides
│   └── llm_client.py # Multi-provider LLM client (OpenRouter, OpenAI, Anthropic, Groq, HF)
├── graph/            # Knowledge graph (15 concept nodes, edges)
├── ingest/           # PDF ingestion pipeline (PyMuPDF + chunker + embedder)
├── ncert_maths_chapters/ # Source PDFs (14 chapters)
├── output/           # Generated question batches (JSON)
├── pdfs/             # Compiled LaTeX PDFs
├── rag/              # FAISS vector store + retriever
├── renderer/         # CBSELaTeXRenderer (exam class, pdflatex)
├── syllabus/         # NCERT Class 10 syllabus catalog (chapters, subtopics, type mappings)
└── validator/        # Structural validation per question type
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-v4-flash
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K_RETRIEVED=5
```

Supported providers: `openrouter`, `openai`, `anthropic`, `groq`, `huggingface`.

## Corpus Roles

| Corpus | Role in generation | What it must not do |
|--------|--------------------|---------------------|
| NCERT textbook | Content grounding and syllabus authority | Expand syllabus beyond Class 10 CBSE |
| GraphRAG concept graph | Formulas, prerequisites, concept relations, pattern guidance | Replace source corpora with hard-coded examples |
| CBSE PYQ | Board-paper pattern, phrasing, mark depth, Basic/Standard variant style | Act as chapter teaching content or be copied |
| NCERT Exemplar | Board-aligned conceptual depth for medium/challenging papers | Become olympiad/out-of-syllabus difficulty |
| RD Sharma (planned) | Pattern expansion and large question-bank coverage | Become syllabus or difficulty authority |

## Development Checks

After changing ingestion, GraphRAG, prompt logic, question types, or corpus metadata:

```bash
python3 scripts/check_generation_stack.py
```

This verifies:
- core modules compile
- old aliases still normalize: `sa_i -> vsa`, `sa_ii -> sa`
- PYQ and Exemplar metadata are present
- source-derived pattern nodes are available to GraphRAG
- the challenging prompt includes graph patterns, PYQ profile, and Exemplar depth context

For a corpus update, use this sequence:

```bash
python3 ingest.py
python3 ingest_pyqs.py
python3 ingest_exemplar.py
python3 scripts/check_generation_stack.py
```

For one-paper-per-chapter batch generation:

```bash
python3 scripts/generate_chapter_batch.py --pdf-dir pdfs/batch1 --meta-dir output/batch1
```

## Question Types (CBSE Class 10 pattern)

| Code | Type | Marks | Section |
|------|------|-------|---------|
| mcq | Multiple Choice | 1 | A |
| assertion_reason | Assertion-Reason | 1 | A |
| vsa | Very Short Answer | 2 | B |
| sa | Short Answer | 3 | C |
| la | Long Answer | 4-5 | D |
| case_study | Case Study | 4 | E |

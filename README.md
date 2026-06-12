# schEngine — CBSE Class 10 Question Generator

Generate NCERT-aligned CBSE Maths, Science, and Social Science exam papers with RAG, subject-specific corpora, CBSE question types, difficulty bands, and PDF export.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest Maths NCERT PDFs (run once)
python3 ingest.py

# Optional Maths reference corpora
python3 ingest_pyqs.py
python3 ingest_exemplar.py

# Science corpora
python3 ingest.py --subject science
python3 ingest_pyqs.py --subject science
python3 ingest_exemplar.py --subject science

# Social Science corpora
python3 ingest.py --subject sst
python3 ingest_pyqs.py --subject sst

# Generate questions
python3 generate.py --topic "Quadratic Equations" --type la --marks 5 --count 5 --pdf
python3 generate.py --topic "Quadratic Equations" --type mcq --count 10 --pdf
python3 generate.py --topic "Trigonometry" --type sa --paper-level challenging --pdf
python3 generate.py --subject science --topic "Electricity" --type sa --paper-level challenging --pdf
python3 generate.py --subject sst --topic "Nationalism in India" --type la --paper-level medium --pdf
python3 generate.py --subject sst --topic "Agriculture" --type map_skill --pdf

# Full paper
python3 generate.py --paper --paper-level medium --pdf
python3 generate.py --subject science --paper --paper-level medium --pdf
python3 generate.py --subject sst --paper --paper-level medium --pdf
```

## Features

| Feature | Description |
|---------|-------------|
| **RAG** | FAISS vector stores (all-MiniLM-L6-v2) over subject-specific NCERT Class 10 PDFs |
| **Knowledge Graph** | Maths concept graph with formulas, patterns, hardness hints, prerequisite edges; Science and SST use vector-grounded syllabus retrieval |
| **7 CBSE Question Types** | mcq, assertion_reason, vsa, sa, la, case_study, map_skill |
| **Hardness Levels** | simple / medium / hard — maps cleanly to mark bands |
| **Paper Difficulty Bands** | standard / medium / challenging — standard uses NCERT + graph + PYQ pattern; medium/challenging also retrieve Exemplar conceptual depth |
| **PYQ Pattern Corpus** | CBSE Maths Basic/Standard, Science, and SST PYQs are retrieved only as paper-style references, not chapter content |
| **Exemplar Depth Corpus** | NCERT Exemplar is retrieved separately for board-aligned conceptual challenge where available; SST uses PYQs for demand calibration |
| **Pattern Rotation** | Rotates through KG typical_patterns to prevent repeated question setups |
| **Diversity Injection** | Tracks used mechanisms across a batch, injects avoidance into subsequent prompts |
| **PDF Export** | `exam` document class with CBSE sections A-F, proper inline/display math |
| **CLI + API** | `generate.py` CLI and FastAPI server |
| **Validators** | Structural checks per question type |

## Usage

### CLI

```bash
python3 generate.py --topic "Quadratic Equations" --type la --marks 5 --count 5 --pdf
python3 generate.py --topic "Real Numbers" --type assertion_reason --count 5
python3 generate.py --topic "Triangles" --type case_study --count 2 --pdf
python3 generate.py --subject science --topic "Chemical Reactions and Equations" --type sa --count 5
python3 generate.py --subject sst --topic "Money and Credit" --type case_study --count 2
```

Options:
- `--subject` — `maths`, `science`, or `sst` (defaults to `maths`)
- `--topic` — Chapter name or "Chapter Subtopic" (e.g. "Quadratic Equations", "Real Numbers Euclid division lemma")
- `--type` — Question type: mcq, assertion_reason, vsa, sa, la, case_study, map_skill
- `--marks` — Override marks (defaults from type)
- `--count` — Number of questions (1–10)
- `--difficulty` — simple, medium, hard
- `--paper-level` — standard, medium, challenging; controls overall conceptual demand
- `--paper-variant` — standard, basic; controls Maths PYQ Basic/Standard pattern retrieval
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
├── content/          # Source PDFs organized by board/subject
│   └── ncert/        # NCERT Maths/Science/SST chapters, exemplar where available, and CBSE PYQs
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
| GraphRAG concept graph | Maths formulas, prerequisites, concept relations, pattern guidance | Replace source corpora with hard-coded examples |
| CBSE PYQ | Board-paper pattern, phrasing, mark depth, Maths Basic/Standard variant style, and SST demand calibration | Act as chapter teaching content or be copied |
| NCERT Exemplar | Board-aligned conceptual depth for medium/challenging papers where available | Become olympiad/out-of-syllabus difficulty |
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
python3 ingest.py --subject science
python3 ingest_pyqs.py --subject science
python3 ingest_exemplar.py --subject science
python3 ingest.py --subject sst
python3 ingest_pyqs.py --subject sst
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
| map_skill | Map Skill | 5 | F |

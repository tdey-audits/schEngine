# Diagram Generation Strategy for CBSE Question Papers

## Core Principle

The LLM never draws. It emits a small, schema-constrained JSON spec; a deterministic renderer owns the actual output.

This is the same pattern already used in `renderer/diagrams/tikz.py` — extend it per category rather than letting the model write raw TikZ, SVG, or image prompts directly.

---

## Category 1: Spec → Deterministic Renderer

For diagrams that are fundamentally parametric (a small number of values fully determine the picture), the LLM emits a validated JSON spec and a renderer converts it to LaTeX/SVG.

### Geometry / Coordinate / Trigonometry
- **LLM emits:** points, segments, angles, labels
- **Renderer:** TikZ — already implemented in `renderer/diagrams/tikz.py`
- **Status:** Done

---

### Electrical Circuits
- **LLM emits:** netlist-style JSON
  ```json
  {
    "type": "circuit",
    "topology": "series",
    "components": [
      {"kind": "cell", "emf": "6V"},
      {"kind": "resistor", "label": "R1", "value": "4Ω"},
      {"kind": "resistor", "label": "R2", "value": "6Ω", "topology": "parallel_with_R1"},
      {"kind": "ammeter", "position": "main_line"},
      {"kind": "voltmeter", "across": "R1"}
    ]
  }
  ```
- **Renderer:** `circuitikz` (LaTeX) or `schemdraw` (Python → SVG/PDF)
- **Why not raw LLM TikZ:** Compiles ~70–80% of the time; failures are silent layout garbage, not just errors
- **Note:** This is the highest-frequency diagram type in Class 10 Physics papers after geometry

---

### Graphs (Distance–Time, V–I, Heating Curves, Population)
- **LLM emits:** axes labels, ranges, data points or function type
  ```json
  {
    "type": "graph",
    "x_axis": {"label": "Time (s)", "range": [0, 10]},
    "y_axis": {"label": "Distance (m)", "range": [0, 50]},
    "curve": {"kind": "linear", "points": [[0, 0], [10, 50]]}
  }
  ```
- **Renderer:** `pgfplots` (LaTeX) or `matplotlib` (Python → SVG/PDF)

---

### Ray Optics (Mirrors and Lenses)
- **LLM emits:** optic type, focal length, object distance and height
  ```json
  {
    "type": "ray_optics",
    "optic": "convex_lens",
    "focal_length": 10,
    "object_distance": 15,
    "object_height": 3
  }
  ```
- **Renderer:** Parameterized TikZ template — CBSE has ~8 canonical ray diagram cases; compute image position using the lens/mirror formula and draw the standard rays deterministically
- **No LLM geometry needed:** The physics fully determines the diagram

---

### Flowcharts / Cycles / Classification Trees
- **LLM emits:** nodes and edges
  ```json
  {
    "type": "flowchart",
    "nodes": [
      {"id": "A", "label": "Sun"},
      {"id": "B", "label": "Grass"},
      {"id": "C", "label": "Grasshopper"},
      {"id": "D", "label": "Frog"}
    ],
    "edges": [["A","B"], ["B","C"], ["C","D"]],
    "layout": "horizontal"
  }
  ```
- **Renderer:** Graphviz DOT or TikZ node graph

---

### Chemical Structures (Class 11/12 scope)
- **LLM emits:** SMILES string or formula
- **Renderer:** RDKit (Python) or `chemfig` (LaTeX)

---

## Category 2: Curated Asset Library

Biology and apparatus diagrams cannot be generated reliably by any programmatic or AI method. They also don't need to be — CBSE draws from a closed, well-known set of NCERT figures.

**Examples:** Human heart, digestive system, neuron, plant cell, electrolysis setup, distillation apparatus, Bohr model, etc.

### Approach

1. Build a library of canonical SVGs, tagged with metadata
   - Source: Wikimedia Commons (open-license NCERT-style figures), or a one-time commissioned set
   - Metadata: `chapter`, `topic`, `asset_id`, `labelable_parts`

2. The LLM's job is **selection + labeling only**:
   ```json
   {
     "type": "asset",
     "asset_id": "human_heart_v1",
     "labels": {
       "A": "Right Atrium",
       "B": "Left Ventricle",
       "C": "Aorta"
     },
     "blank_labels": ["A", "C"]
   }
   ```

3. Labels are rendered as an overlay programmatically — the same asset serves:
   - "Label the parts" questions
   - "Identify part X" questions
   - Fully labeled reference diagrams

This matches how CBSE reuses figures across exam years, and mirrors the RAG approach already used for PYQ patterns.

---

## Pipeline Shape

```
Question generation
  └─ diagram spec (JSON, validated against schema)
       └─ router by diagram.type
            ├─ geometry/trig     → TikZ (existing)
            ├─ circuit           → circuitikz / schemdraw
            ├─ graph             → pgfplots / matplotlib
            ├─ ray_optics        → parameterized TikZ template
            ├─ flowchart         → Graphviz / TikZ nodes
            └─ asset             → SVG overlay renderer
       └─ compile check (latexmk dry run)
            ├─ success → include in paper
            └─ failure → drop diagram + regenerate question, never ship broken TeX
```

---

## Schema Validation Rules (apply to every backend)

Following the pattern in `renderer/diagrams/tikz.py`:

- Maintain an `ALLOWED_TYPES` whitelist per renderer
- Validate all numeric values with bounded floats (no unbounded user input to LaTeX)
- Strip/escape all text fields before embedding in TeX
- Any unrecognised `type` or missing required field → renderer returns `""` silently
- Never pass raw LLM-generated TeX strings through to compilation

---

## What to Avoid

| Approach | Reason to Avoid |
|---|---|
| Diffusion/image-model generation (DALL-E, Imagen, etc.) | Wrong style, physically incorrect, unlabelable, not reproducible, cannot be edited |
| LLM writing raw TikZ/SVG/circuitikz directly | ~70–80% compile rate; silent layout failures; maintenance nightmare |
| Generating biology diagrams programmatically | Too complex, too varied — curate instead |
| Ignoring diagram failures silently | Must either compile successfully or be dropped; broken TeX in a PDF is worse than no diagram |

---

## Implementation Priority

1. **Circuits** — highest frequency in Class 10 Physics; `circuitikz` spec + renderer
2. **Ray optics** — finite canonical cases; one parameterized TikZ template covers all CBSE variations
3. **Graphs** — straightforward `pgfplots` templates for the 4–5 graph types CBSE uses
4. **Asset library** — biology figures; one-time curation effort, high reuse
5. **Flowcharts** — lower frequency; Graphviz handles it simply

"""Deterministic TikZ rendering for generated question diagrams.

The LLM supplies a small JSON diagram spec; this module owns the LaTeX output.
That keeps board-paper diagrams crisp and prevents raw model-generated TikZ from
breaking PDF compilation.
"""

from __future__ import annotations

import math
import re
from typing import Any


class TikZDiagramRenderer:
    ALLOWED_TYPES = {
        "geometry", "coordinate", "trigonometry", "circle", "mensuration", "construction"
    }
    ALLOWED_KINDS = {
        "point", "segment", "line", "ray", "circle", "arc", "angle", "right_angle",
        "parallel_mark", "equal_mark", "label", "axis", "grid", "polygon",
    }
    POSITIONS = {
        "above", "below", "left", "right", "above left", "above right",
        "below left", "below right",
    }
    STYLES = {
        "solid": "thick",
        "dashed": "thick,dashed",
        "dotted": "thick,dotted",
        "thin": "thin",
        "thick": "thick",
        "parallel_marked": "thick",
        "auxiliary": "thin,dashed",
    }

    def render(self, diagram: dict[str, Any] | None) -> str:
        if not isinstance(diagram, dict) or not diagram.get("required", True):
            return ""
        if diagram.get("type") not in self.ALLOWED_TYPES:
            return ""

        elements = diagram.get("elements", [])
        if not isinstance(elements, list):
            return ""

        points = self._collect_points(elements)
        lines: list[str] = []
        draw_after: list[str] = []

        if not points and diagram.get("type") == "trigonometry":
            points = {"A": (0.0, 0.0), "B": (4.0, 0.0), "C": (4.0, 3.0)}

        for pid, (x, y) in points.items():
            lines.append(rf"\coordinate ({pid}) at ({self._num(x)},{self._num(y)});")

        for el in elements:
            if not isinstance(el, dict):
                continue
            kind = el.get("kind")
            if kind not in self.ALLOWED_KINDS:
                continue
            rendered = self._render_element(el, points)
            if not rendered:
                continue
            if kind == "point":
                draw_after.append(rendered)
            else:
                lines.append(rendered)

        if not lines and not draw_after:
            return ""

        scale = self._bounded_float(diagram.get("scale", 0.85), 0.35, 1.4, 0.85)
        body = "\n".join(lines + draw_after)
        caption = self._text(diagram.get("caption", ""))
        caption_tex = rf"\\[-0.15cm]\scriptsize {caption}" if caption else ""
        return (
            "\n\\begin{center}\n"
            rf"\begin{{tikzpicture}}[scale={self._num(scale)}, line cap=round, line join=round]"
            "\n"
            f"{body}\n"
            "\\end{tikzpicture}"
            f"{caption_tex}\n"
            "\\end{center}\n"
        )

    def validate(self, diagram: Any) -> list[str]:
        if diagram in (None, {}, False):
            return []
        if not isinstance(diagram, dict):
            return ["diagram must be an object"]
        if diagram.get("type") not in self.ALLOWED_TYPES:
            return [f"diagram.type must be one of {sorted(self.ALLOWED_TYPES)}"]
        elements = diagram.get("elements", [])
        if not isinstance(elements, list):
            return ["diagram.elements must be an array"]

        errors: list[str] = []
        points = self._collect_points(elements)
        for i, el in enumerate(elements):
            if not isinstance(el, dict):
                errors.append(f"diagram element {i+1} must be an object")
                continue
            kind = el.get("kind")
            if kind not in self.ALLOWED_KINDS:
                errors.append(f"diagram element {i+1} has invalid kind: {kind}")
                continue
            for endpoint_key in ("from", "to", "center"):
                ref = el.get(endpoint_key)
                if ref and isinstance(ref, str) and ref not in points:
                    errors.append(f"diagram element {i+1} references unknown point {ref!r}")
            refs = el.get("points", [])
            if refs and (not isinstance(refs, list) or any(r not in points for r in refs if isinstance(r, str))):
                errors.append(f"diagram element {i+1} has invalid points reference")
        return errors

    def _collect_points(self, elements: list[Any]) -> dict[str, tuple[float, float]]:
        points: dict[str, tuple[float, float]] = {}
        for el in elements:
            if not isinstance(el, dict) or el.get("kind") != "point":
                continue
            pid = self._id(el.get("id"))
            if not pid:
                continue
            x = self._bounded_float(el.get("x"), -10.0, 10.0, 0.0)
            y = self._bounded_float(el.get("y"), -10.0, 10.0, 0.0)
            points[pid] = (x, y)
        return points

    def _render_element(self, el: dict[str, Any], points: dict[str, tuple[float, float]]) -> str:
        kind = el.get("kind")
        if kind == "point":
            return self._render_point(el)
        if kind in {"segment", "line", "ray"}:
            return self._render_segment(el, points, kind)
        if kind == "polygon":
            refs = [self._id(r) for r in el.get("points", [])]
            if len(refs) >= 3 and all(r in points for r in refs):
                style = self._style(el.get("style"))
                return rf"\draw[{style}] " + " -- ".join(f"({r})" for r in refs) + " -- cycle;"
        if kind == "circle":
            center = self._id(el.get("center"))
            radius = self._bounded_float(el.get("radius"), 0.1, 8.0, 1.0)
            if center in points:
                return rf"\draw[{self._style(el.get('style'))}] ({center}) circle ({self._num(radius)});"
        if kind == "arc":
            center = self._id(el.get("center"))
            radius = self._bounded_float(el.get("radius"), 0.1, 8.0, 1.0)
            start = self._bounded_float(el.get("start_angle"), -360.0, 360.0, 0.0)
            end = self._bounded_float(el.get("end_angle"), -360.0, 360.0, 90.0)
            if center in points:
                return (
                    rf"\draw[{self._style(el.get('style'))}] ({center}) ++({self._num(start)}:{self._num(radius)}) "
                    rf"arc ({self._num(start)}:{self._num(end)}:{self._num(radius)});"
                )
        if kind == "angle":
            refs = [self._id(r) for r in el.get("points", [])]
            if len(refs) == 3 and all(r in points for r in refs):
                label = self._math_label(el.get("label", ""))
                radius = self._bounded_float(el.get("radius"), 0.25, 1.2, 0.45)
                pic = rf'pic [draw, angle radius={self._num(radius)}cm'
                if label:
                    pic += rf', "$ {label} $"'
                pic += rf"] {{{self._angle_name(refs)}}}"
                return rf"\path ({refs[0]}) -- ({refs[1]}) -- ({refs[2]}) {pic};"
        if kind == "right_angle":
            refs = [self._id(r) for r in el.get("points", [])]
            if len(refs) == 3 and all(r in points for r in refs):
                return rf"\path ({refs[0]}) -- ({refs[1]}) -- ({refs[2]}) pic [draw, angle radius=0.28cm] {{right angle={refs[0]}--{refs[1]}--{refs[2]}}};"
        if kind == "parallel_mark":
            return self._mark_on_segment(el, points, "parallel")
        if kind == "equal_mark":
            return self._mark_on_segment(el, points, "equal")
        if kind == "label":
            at = self._id(el.get("at"))
            if at in points:
                return rf"\node[{self._position(el.get('position'))}] at ({at}) {{{self._text(el.get('text', ''))}}};"
        if kind == "axis":
            return r"\draw[->, thin] (-0.4,0) -- (5.2,0) node[right] {$x$}; \draw[->, thin] (0,-0.4) -- (0,4.2) node[above] {$y$};"
        if kind == "grid":
            return r"\draw[step=1cm, gray!30, very thin] (-0.1,-0.1) grid (5.1,4.1);"
        return ""

    def _render_point(self, el: dict[str, Any]) -> str:
        pid = self._id(el.get("id"))
        if not pid:
            return ""
        label = self._math_label(el.get("label", pid))
        pos = self._position(el.get("position"))
        show_dot = bool(el.get("dot", True))
        dot = rf"\fill ({pid}) circle (1.3pt);" if show_dot else ""
        return dot + "\n" + rf"\node[{pos}] at ({pid}) {{$ {label} $}};"

    def _render_segment(self, el: dict[str, Any], points: dict[str, tuple[float, float]], kind: str) -> str:
        start = self._id(el.get("from"))
        end = self._id(el.get("to"))
        if start not in points or end not in points:
            return ""
        style = self._style(el.get("style"))
        arrow = "->," if kind == "ray" else ""
        draw = rf"\draw[{arrow}{style}] ({start}) -- ({end})"
        label = self._math_label(el.get("label", ""))
        if label:
            draw += rf" node[midway,{self._position(el.get('label_position', 'above'))}] {{$ {label} $}}"
        return draw + ";"

    def _mark_on_segment(self, el: dict[str, Any], points: dict[str, tuple[float, float]], mark: str) -> str:
        start = self._id(el.get("from"))
        end = self._id(el.get("to"))
        if start not in points or end not in points:
            return ""
        x1, y1 = points[start]
        x2, y2 = points[end]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1)) + 90
        if mark == "parallel":
            return rf"\draw[thin] ({self._num(mx)},{self._num(my)}) ++({self._num(angle)}:0.10) -- ++({self._num(angle + 180)}:0.20);"
        return rf"\draw[thin] ({self._num(mx)},{self._num(my)}) ++({self._num(angle)}:0.11) -- ++({self._num(angle + 180)}:0.22);"

    def _style(self, value: Any) -> str:
        return self.STYLES.get(str(value or "solid"), "thick")

    def _position(self, value: Any) -> str:
        value = str(value or "above")
        return value if value in self.POSITIONS else "above"

    def _id(self, value: Any) -> str:
        text = str(value or "")
        text = re.sub(r"[^A-Za-z0-9_]", "", text)
        if not text or text[0].isdigit():
            return ""
        return text[:24]

    def _text(self, value: Any) -> str:
        text = str(value or "")
        return (
            text.replace("\\", r"\textbackslash{}")
            .replace("&", r"\&")
            .replace("%", r"\%")
            .replace("#", r"\#")
            .replace("_", r"\_")
            .replace("{", r"\{")
            .replace("}", r"\}")
        )

    def _math_label(self, value: Any) -> str:
        text = str(value or "")
        text = text.replace("$", "")
        text = re.sub(r"[^A-Za-z0-9_+\-=/\\^{}().,:\s]", "", text)
        return text[:80]

    def _bounded_float(self, value: Any, low: float, high: float, default: float) -> float:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return default
        if not math.isfinite(num):
            return default
        return max(low, min(high, num))

    def _num(self, value: float) -> str:
        return f"{value:.3f}".rstrip("0").rstrip(".")

    def _angle_name(self, refs: list[str]) -> str:
        return f"angle={refs[0]}--{refs[1]}--{refs[2]}"

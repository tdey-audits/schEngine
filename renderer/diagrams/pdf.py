"""Vector PDF diagram rendering for generated board-paper questions."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.pdfgen import canvas


class PDFDiagramRenderer:
    ALLOWED_TYPES = {
        "geometry", "coordinate", "trigonometry", "circle", "mensuration", "construction"
    }
    ALLOWED_KINDS = {
        "point", "segment", "line", "ray", "circle", "arc", "angle", "right_angle",
        "parallel_mark", "equal_mark", "label", "axis", "grid", "polygon",
    }

    def __init__(self, asset_dir: str | Path):
        self.asset_dir = Path(asset_dir)
        self.asset_dir.mkdir(parents=True, exist_ok=True)

    def render_asset(self, diagram: dict[str, Any] | None, name: str) -> Path | None:
        if not isinstance(diagram, dict) or not diagram.get("required", True):
            return None
        if diagram.get("type") not in self.ALLOWED_TYPES:
            return None
        elements = diagram.get("elements", [])
        if not isinstance(elements, list):
            return None

        points = self._collect_points(elements)
        if not points and diagram.get("type") == "trigonometry":
            points = {"A": (0.0, 0.0), "B": (4.0, 0.0), "C": (4.0, 3.0)}
        if not points and not any(isinstance(e, dict) and e.get("kind") in {"axis", "grid"} for e in elements):
            return None

        width_pt = self._bounded_float(diagram.get("width_pt"), 180, 360, 235)
        height_pt = self._bounded_float(diagram.get("height_pt"), 120, 300, 165)
        path = self.asset_dir / f"{self._safe_name(name)}.pdf"
        c = canvas.Canvas(str(path), pagesize=(width_pt, height_pt))
        c.setTitle(name)
        c.setLineJoin(1)
        c.setLineCap(1)

        mapper = _Mapper(points, elements, width_pt, height_pt)
        self._draw_grid_and_axes(c, elements, mapper, width_pt, height_pt)

        for el in elements:
            if not isinstance(el, dict):
                continue
            kind = el.get("kind")
            if kind == "polygon":
                self._draw_polygon(c, el, points, mapper)
            elif kind in {"segment", "line", "ray"}:
                self._draw_segment(c, el, points, mapper)
            elif kind == "circle":
                self._draw_circle(c, el, points, mapper)
            elif kind == "arc":
                self._draw_arc(c, el, points, mapper)
            elif kind == "angle":
                self._draw_angle(c, el, points, mapper)
            elif kind == "right_angle":
                self._draw_right_angle(c, el, points, mapper)
            elif kind == "parallel_mark":
                self._draw_mark(c, el, points, mapper, parallel=True)
            elif kind == "equal_mark":
                self._draw_mark(c, el, points, mapper, parallel=False)
            elif kind == "label":
                self._draw_label(c, el, points, mapper)

        for el in elements:
            if isinstance(el, dict) and el.get("kind") == "point":
                self._draw_point(c, el, points, mapper)

        c.showPage()
        c.save()
        return path

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
            for key in ("from", "to", "center", "at"):
                ref = el.get(key)
                if ref and isinstance(ref, str) and ref not in points:
                    errors.append(f"diagram element {i+1} references unknown point {ref!r}")
            refs = el.get("points", [])
            if refs and (not isinstance(refs, list) or any(not isinstance(r, str) or r not in points for r in refs)):
                errors.append(f"diagram element {i+1} has invalid points reference")
        return errors

    def _collect_points(self, elements: list[Any]) -> dict[str, tuple[float, float]]:
        points = {}
        for el in elements:
            if not isinstance(el, dict) or el.get("kind") != "point":
                continue
            pid = self._id(el.get("id"))
            if pid:
                points[pid] = (
                    self._bounded_float(el.get("x"), -100, 100, 0),
                    self._bounded_float(el.get("y"), -100, 100, 0),
                )
        return points

    def _draw_grid_and_axes(self, c, elements, mapper, width, height):
        kinds = {e.get("kind") for e in elements if isinstance(e, dict)}
        if "grid" in kinds:
            c.setStrokeColor(colors.lightgrey)
            c.setLineWidth(0.35)
            for i in range(7):
                x = mapper.margin + i * (width - 2 * mapper.margin) / 6
                c.line(x, mapper.margin, x, height - mapper.margin)
            for i in range(5):
                y = mapper.margin + i * (height - 2 * mapper.margin) / 4
                c.line(mapper.margin, y, width - mapper.margin, y)
        if "axis" in kinds:
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.8)
            ox, oy = mapper.map((0, 0))
            c.line(mapper.margin, oy, width - mapper.margin, oy)
            c.line(ox, mapper.margin, ox, height - mapper.margin)
            c.drawString(width - mapper.margin + 2, oy - 3, "x")
            c.drawString(ox + 3, height - mapper.margin + 1, "y")

    def _draw_polygon(self, c, el, points, mapper):
        refs = [self._id(r) for r in el.get("points", [])]
        if len(refs) < 3 or any(r not in points for r in refs):
            return
        c.setStrokeColor(colors.black)
        c.setLineWidth(self._line_width(el))
        path = c.beginPath()
        x, y = mapper.map(points[refs[0]])
        path.moveTo(x, y)
        for ref in refs[1:]:
            x, y = mapper.map(points[ref])
            path.lineTo(x, y)
        path.close()
        c.drawPath(path, stroke=1, fill=0)

    def _draw_segment(self, c, el, points, mapper):
        a, b = self._id(el.get("from")), self._id(el.get("to"))
        if a not in points or b not in points:
            return
        self._apply_style(c, el)
        x1, y1 = mapper.map(points[a])
        x2, y2 = mapper.map(points[b])
        c.line(x1, y1, x2, y2)
        c.setDash()
        label = self._label(el.get("label"))
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = self._segment_label_offset(x1, y1, x2, y2, el.get("label_position"))
            self._draw_text_box(c, label, mx + dx, my + dy, font_size=8, align="center")

    def _draw_circle(self, c, el, points, mapper):
        center = self._id(el.get("center"))
        if center not in points:
            return
        radius = self._bounded_float(el.get("radius"), 0.05, 100, 1)
        x, y = mapper.map(points[center])
        c.setStrokeColor(colors.black)
        c.setLineWidth(self._line_width(el))
        c.circle(x, y, radius * mapper.scale, stroke=1, fill=0)

    def _draw_arc(self, c, el, points, mapper):
        center = self._id(el.get("center"))
        if center not in points:
            return
        radius = self._bounded_float(el.get("radius"), 0.05, 100, 1) * mapper.scale
        start = self._bounded_float(el.get("start_angle"), -360, 360, 0)
        end = self._bounded_float(el.get("end_angle"), -360, 360, 90)
        x, y = mapper.map(points[center])
        c.setStrokeColor(colors.black)
        c.setLineWidth(self._line_width(el))
        c.arc(x - radius, y - radius, x + radius, y + radius, start, end - start)

    def _draw_angle(self, c, el, points, mapper):
        refs = [self._id(r) for r in el.get("points", [])]
        if len(refs) != 3 or any(r not in points for r in refs):
            return
        a, b, d = (points[refs[0]], points[refs[1]], points[refs[2]])
        bx, by = mapper.map(b)
        ang1 = math.degrees(math.atan2(a[1] - b[1], a[0] - b[0]))
        ang2 = math.degrees(math.atan2(d[1] - b[1], d[0] - b[0]))
        radius = self._bounded_float(el.get("radius"), 0.15, 2, 0.45) * mapper.scale
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.arc(bx - radius, by - radius, bx + radius, by + radius, ang1, ang2 - ang1)
        label = self._label(el.get("label"))
        if label:
            mid = math.radians((ang1 + ang2) / 2)
            lx = bx + math.cos(mid) * (radius + 12)
            ly = by + math.sin(mid) * (radius + 10)
            self._draw_text_box(c, label, lx, ly, font_size=8, align="center")

    def _draw_right_angle(self, c, el, points, mapper):
        refs = [self._id(r) for r in el.get("points", [])]
        if len(refs) != 3 or any(r not in points for r in refs):
            return
        a, b, d = (points[refs[0]], points[refs[1]], points[refs[2]])
        size = 0.28
        ux = self._unit((a[0] - b[0], a[1] - b[1]))
        vx = self._unit((d[0] - b[0], d[1] - b[1]))
        pts = [b, (b[0] + ux[0]*size, b[1] + ux[1]*size), (b[0] + ux[0]*size + vx[0]*size, b[1] + ux[1]*size + vx[1]*size), (b[0] + vx[0]*size, b[1] + vx[1]*size)]
        mapped = [mapper.map(pt) for pt in pts]
        c.setLineWidth(0.7)
        c.line(*mapped[1], *mapped[2])
        c.line(*mapped[2], *mapped[3])

    def _draw_mark(self, c, el, points, mapper, parallel):
        a, b = self._id(el.get("from")), self._id(el.get("to"))
        if a not in points or b not in points:
            return
        x1, y1 = mapper.map(points[a])
        x2, y2 = mapper.map(points[b])
        mx, my = (x1+x2)/2, (y1+y2)/2
        dx, dy = self._unit((x2-x1, y2-y1))
        nx, ny = -dy, dx
        length = 8 if parallel else 9
        c.setLineWidth(0.7)
        c.line(mx - nx*length/2, my - ny*length/2, mx + nx*length/2, my + ny*length/2)

    def _draw_label(self, c, el, points, mapper):
        at = self._id(el.get("at"))
        if at not in points:
            return
        x, y = mapper.map(points[at])
        dx, dy = self._label_offset(el.get("position", "above right"))
        self._draw_text_box(c, self._label(el.get("text")), x + dx, y + dy, font_size=8, align="center")

    def _draw_point(self, c, el, points, mapper):
        pid = self._id(el.get("id"))
        if pid not in points:
            return
        x, y = mapper.map(points[pid])
        if el.get("dot", True):
            c.setFillColor(colors.black)
            c.circle(x, y, 1.4, stroke=0, fill=1)
        label = self._label(el.get("label", pid))
        dx, dy = self._point_label_offset(el, points[pid], mapper)
        self._draw_text_box(c, label, x + dx, y + dy, font_size=8.5, align="center")

    def _draw_text_box(self, c, text: str, x: float, y: float, font_size: float = 8, align: str = "center"):
        if not text:
            return
        c.setFont("Helvetica", font_size)
        padding_x = 2.4
        padding_y = 1.6
        width = c.stringWidth(text, "Helvetica", font_size)
        height = font_size
        if align == "center":
            left = x - width / 2 - padding_x
            draw_x = x - width / 2
        else:
            left = x - padding_x
            draw_x = x
        bottom = y - height / 2 - padding_y
        c.saveState()
        c.setFillColor(colors.white)
        c.rect(left, bottom, width + 2 * padding_x, height + 2 * padding_y, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.drawString(draw_x, y - height / 2 + 1.5, text)
        c.restoreState()

    def _segment_label_offset(self, x1: float, y1: float, x2: float, y2: float, position: Any) -> tuple[float, float]:
        dx, dy = self._unit((x2 - x1, y2 - y1))
        nx, ny = -dy, dx
        pos = str(position or "above")
        distance = 12.0
        along = 0.0
        if "below" in pos:
            nx, ny = -nx, -ny
        if "left" in pos:
            along = -10.0
        elif "right" in pos:
            along = 10.0
        return nx * distance + dx * along, ny * distance + dy * along

    def _point_label_offset(self, el: dict[str, Any], point: tuple[float, float], mapper) -> tuple[float, float]:
        position = el.get("position")
        if position:
            return self._label_offset(position)
        cx = (mapper.min_x + mapper.max_x) / 2
        cy = (mapper.min_y + mapper.max_y) / 2
        vx, vy = point[0] - cx, point[1] - cy
        if abs(vx) < 0.05 and abs(vy) < 0.05:
            return 0, 13
        ux, uy = self._unit((vx, vy))
        return ux * 15, uy * 13

    def _apply_style(self, c, el):
        c.setStrokeColor(colors.black)
        c.setLineWidth(self._line_width(el))
        style = str(el.get("style", "solid"))
        if style in {"dashed", "auxiliary"}:
            c.setDash(4, 3)
        elif style == "dotted":
            c.setDash(1, 2)
        else:
            c.setDash()

    def _line_width(self, el):
        return 0.65 if str(el.get("style")) in {"thin", "auxiliary"} else 1.0

    def _label_offset(self, pos):
        pos = str(pos or "above")
        x = (-13 if "left" in pos else 13 if "right" in pos else 0)
        y = (-14 if "below" in pos else 13)
        return x, y

    def _id(self, value: Any) -> str:
        text = re.sub(r"[^A-Za-z0-9_]", "", str(value or ""))
        return text[:24] if text and not text[0].isdigit() else ""

    def _label(self, value: Any) -> str:
        text = str(value or "")
        replacements = {r"\\circ": "°", r"^\\circ": "°", r"\\parallel": "∥", r"\\perp": "⊥"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = text.replace("$", "")
        text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
        return text[:80]

    def _safe_name(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", value)[:80] or "diagram"

    def _bounded_float(self, value: Any, low: float, high: float, default: float) -> float:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return default
        return max(low, min(high, num)) if math.isfinite(num) else default

    def _unit(self, vec):
        x, y = vec
        mag = math.hypot(x, y) or 1.0
        return x / mag, y / mag


class _Mapper:
    def __init__(self, points: dict[str, tuple[float, float]], elements: list[Any], width: float, height: float):
        # Padding protects labels, angle marks, tangent endpoints and circle strokes
        # from being clipped by the PDF asset boundary.
        self.margin = 26
        if points:
            xs = [p[0] for p in points.values()]
            ys = [p[1] for p in points.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
        else:
            min_x, max_x, min_y, max_y = -0.5, 5.5, -0.5, 4.5

        for el in elements:
            if not isinstance(el, dict):
                continue
            center = el.get("center")
            if el.get("kind") in {"circle", "arc"} and isinstance(center, str) and center in points:
                radius = _bounded_float(el.get("radius"), 0.05, 100, 1)
                cx, cy = points[center]
                min_x = min(min_x, cx - radius)
                max_x = max(max_x, cx + radius)
                min_y = min(min_y, cy - radius)
                max_y = max(max_y, cy + radius)

        span_x = max(max_x - min_x, 1.0)
        span_y = max(max_y - min_y, 1.0)
        # Add coordinate-space breathing room as a second guard against labels
        # and marks that sit just outside the mathematical figure.
        pad_x = max(span_x * 0.08, 0.28)
        pad_y = max(span_y * 0.10, 0.28)
        self.min_x, self.max_x = min_x - pad_x, max_x + pad_x
        self.min_y, self.max_y = min_y - pad_y, max_y + pad_y
        span_x = max(self.max_x - self.min_x, 1.0)
        span_y = max(self.max_y - self.min_y, 1.0)
        usable_w = max(width - 2*self.margin, width * 0.45)
        usable_h = max(height - 2*self.margin, height * 0.45)
        self.scale = min(usable_w / span_x, usable_h / span_y)
        self.width = width
        self.height = height
        self.offset_x = (width - span_x*self.scale) / 2
        self.offset_y = (height - span_y*self.scale) / 2

    def map(self, point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        return (
            self.offset_x + (x - self.min_x) * self.scale,
            self.offset_y + (y - self.min_y) * self.scale,
        )


def _bounded_float(value: Any, low: float, high: float, default: float) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, num)) if math.isfinite(num) else default

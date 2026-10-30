"""Downloadable results: an Excel workbook and a one-page PDF summary.

Both builders take already-translated labels, so this module knows nothing about the UI
language. The PDF embeds DejaVu Sans (assets/fonts) because the PDF core fonts cover only
Latin-1 and would fail on Turkish letters (ş, ğ, ı) and the lira sign (₺).
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from fpdf import FPDF

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def build_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    """One sheet per frame, in order, with readable column widths. Every cell is a value:
    text that starts with "=" (e.g. a product name from an uploaded file) is stored as text,
    never as a formula Excel would run."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            sheet = name[:31]  # Excel's limit
            frame.to_excel(writer, sheet_name=sheet, index=False)
            ws = writer.sheets[sheet]
            for row in ws.iter_rows():
                for cell in row:
                    if cell.data_type == "f":
                        cell.data_type = "s"
            for i, col in enumerate(frame.columns, start=1):
                width = max([len(str(col))] + [len(str(v)) for v in frame[col].head(200)])
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(max(width + 2, 10), 60)
            ws.freeze_panes = "A2"
    return buf.getvalue()


@dataclass
class Series:
    name: str
    y: np.ndarray
    color: str  # "#rrggbb"
    width: float = 0.5


@dataclass
class VLine:
    x: float
    label: str
    color: str
    dashed: bool = False


@dataclass
class Chart:
    title: str
    x: np.ndarray
    series: list[Series]
    xlabel: str = ""
    ylabel: str = ""
    vlines: list[VLine] = field(default_factory=list)
    band: tuple[float, float, str] | None = None  # (x0, x1, label) shaded range


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _ticks(lo: float, hi: float, n: int = 5) -> np.ndarray:
    return np.linspace(lo, hi, n)


def _fmt(v: float, span: float) -> str:
    return f"{v:,.0f}" if span >= 50 else f"{v:,.2f}"


class _PDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)


def _draw_chart(pdf: _PDF, chart: Chart, x0: float, y0: float, w: float, h: float) -> None:
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_xy(x0, y0)
    pdf.cell(w, 6, chart.title)
    top, left, bottom, right = y0 + 9, x0 + 18, y0 + h - 10, x0 + w
    xs = np.asarray(chart.x, dtype=float)
    ys = np.concatenate([np.asarray(s.y, dtype=float) for s in chart.series])
    xmin, xmax = float(xs.min()), float(xs.max())
    ymin, ymax = float(min(ys.min(), 0)), float(ys.max())
    if ymax - ymin < 1e-9:
        ymax = ymin + 1

    def px(x):
        return left + (x - xmin) / (xmax - xmin) * (right - left)

    def py(y):
        return bottom - (y - ymin) / (ymax - ymin) * (bottom - top)

    if chart.band:
        bx0, bx1, _ = chart.band
        pdf.set_fill_color(225, 236, 250)
        pdf.rect(px(max(bx0, xmin)), top, px(min(bx1, xmax)) - px(max(bx0, xmin)), bottom - top, style="F")

    # Grid and tick labels
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(110, 110, 110)
    pdf.set_draw_color(225, 225, 225)
    pdf.set_line_width(0.2)
    for yv in _ticks(ymin, ymax):
        pdf.line(left, py(yv), right, py(yv))
        pdf.set_xy(x0, py(yv) - 2)
        pdf.cell(left - x0 - 1, 4, _fmt(yv, ymax - ymin), align="R")
    for xv in _ticks(xmin, xmax):
        pdf.set_xy(px(xv) - 10, bottom + 1)
        pdf.cell(20, 4, _fmt(xv, xmax - xmin), align="C")
    if ymin < 0 < ymax:
        pdf.set_draw_color(140, 140, 140)
        pdf.line(left, py(0), right, py(0))

    # Series
    step = max(1, len(xs) // 400)  # ~400 points per line is plenty on paper
    for s in chart.series:
        pdf.set_draw_color(*_rgb(s.color))
        pdf.set_line_width(s.width)
        pdf.polyline([(px(x), py(y)) for x, y in zip(xs[::step], np.asarray(s.y)[::step])])

    for v in chart.vlines:
        if not xmin <= v.x <= xmax:
            continue
        pdf.set_draw_color(*_rgb(v.color))
        pdf.set_line_width(0.3)
        if v.dashed:
            pdf.set_dash_pattern(dash=1.2, gap=1.0)
        pdf.line(px(v.x), top, px(v.x), bottom)
        pdf.set_dash_pattern()
        pdf.set_text_color(*_rgb(v.color))
        pdf.set_xy(px(v.x) + 1, top)
        pdf.cell(40, 4, v.label)

    # Axis titles and legend
    pdf.set_text_color(110, 110, 110)
    pdf.set_xy(left, bottom + 5)
    pdf.cell(right - left, 4, chart.xlabel, align="C")
    lx = left
    pdf.set_font("DejaVu", "", 8)
    pdf.set_xy(lx, y0 + 4.5)
    for s in chart.series:
        pdf.set_draw_color(*_rgb(s.color))
        pdf.set_line_width(0.8)
        pdf.line(lx, y0 + 7, lx + 5, y0 + 7)
        pdf.set_text_color(60, 60, 60)
        pdf.set_xy(lx + 6, y0 + 5)
        label_w = pdf.get_string_width(s.name) + 4
        pdf.cell(label_w, 4, s.name)
        lx += 6 + label_w + 3
    if chart.band:
        pdf.set_fill_color(225, 236, 250)
        pdf.rect(lx, y0 + 5.5, 5, 3, style="F")
        pdf.set_xy(lx + 6, y0 + 5)
        pdf.cell(40, 4, chart.band[2])
    pdf.set_text_color(0, 0, 0)


def build_pdf(title: str, subtitle: str, summary: list[tuple[str, str]], chart: Chart,
              notes_title: str = "", notes: list[str] | None = None, footer: str = "") -> bytes:
    pdf = _PDF()
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Key figures as a two-column table
    pdf.set_font("DejaVu", "", 9)
    label_w = 75
    for i, (label, value) in enumerate(summary):
        fill = i % 2 == 0
        pdf.set_fill_color(245, 245, 243)
        pdf.cell(label_w, 6, label, fill=fill)
        pdf.set_font("DejaVu", "B", 9)
        pdf.cell(0, 6, value, fill=fill, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 9)

    pdf.ln(4)
    if pdf.get_y() + 95 > pdf.h - pdf.b_margin:  # the chart is drawn by hand, so page breaks are too
        pdf.add_page()
    _draw_chart(pdf, chart, pdf.l_margin, pdf.get_y(), pdf.epw, 95)
    pdf.set_y(pdf.get_y() + 95 + 4)

    if notes:
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 6, notes_title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 8)
        for note in notes:
            pdf.multi_cell(0, 4.5, f"• {note}", new_x="LMARGIN", new_y="NEXT")

    if footer:
        pdf.set_y(-20)
        pdf.set_font("DejaVu", "", 7)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 4, footer, align="C")
    return bytes(pdf.output())

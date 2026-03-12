from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Tuple

from reportlab.lib.pagesizes import portrait
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def mm_to_pt(mm: float) -> float:
    return mm * 72.0 / 25.4


TICKET_WIDTH_PT = mm_to_pt(80.0)


def _safe_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


@dataclass(frozen=True)
class TicketStyle:
    font: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"
    font_mono: str = "Courier"
    size: int = 9
    size_small: int = 8
    size_title: int = 10
    leading: float = 10.5
    margin_pt: float = 10.0


def register_font_if_present(font_name: str, ttf_path: str) -> None:
    """
    Registro opcional de una fuente TTF si existe.
    Si falla, se seguirá usando Helvetica/Courier.
    """
    try:
        pdfmetrics.registerFont(TTFont(font_name, ttf_path))
    except Exception:
        return


class TicketPDF:
    def __init__(self, height_pt: float, style: TicketStyle | None = None):
        self.style = style or TicketStyle()
        self.width = TICKET_WIDTH_PT
        self.height = max(height_pt, mm_to_pt(80))  # mínimo razonable
        self.buffer = None
        self._y = self.height - self.style.margin_pt
        self._c = None

    def build_canvas(self, buffer):
        self.buffer = buffer
        self._c = canvas.Canvas(buffer, pagesize=portrait((self.width, self.height)))
        self._c.setTitle("Comprobante")
        return self._c

    @property
    def c(self) -> canvas.Canvas:
        if self._c is None:
            raise RuntimeError("Canvas no inicializado")
        return self._c

    @property
    def y(self) -> float:
        return self._y

    def set_y(self, y: float) -> None:
        self._y = y

    def newline(self, lines: float = 1.0) -> None:
        self._y -= self.style.leading * lines

    def hr(self) -> None:
        x0 = self.style.margin_pt
        x1 = self.width - self.style.margin_pt
        self.c.setLineWidth(0.7)
        self.c.line(x0, self._y, x1, self._y)
        self.newline(0.6)

    def dashed_hr(self) -> None:
        x0 = self.style.margin_pt
        x1 = self.width - self.style.margin_pt
        self.c.setDash(1, 2)
        self.c.setLineWidth(0.7)
        self.c.line(x0, self._y, x1, self._y)
        self.c.setDash()
        self.newline(0.6)

    def text_center(self, text: str, bold: bool = False, size: int | None = None) -> None:
        font = self.style.font_bold if bold else self.style.font
        self.c.setFont(font, size or self.style.size_title)
        self.c.drawCentredString(self.width / 2.0, self._y, text)
        self.newline(1.0)

    def text_left(self, text: str, bold: bool = False, size: int | None = None) -> None:
        font = self.style.font_bold if bold else self.style.font
        self.c.setFont(font, size or self.style.size)
        self.c.drawString(self.style.margin_pt, self._y, text)
        self.newline(1.0)

    def kv(self, key: str, value: str) -> None:
        self.c.setFont(self.style.font_bold, self.style.size_small)
        x0 = self.style.margin_pt
        self.c.drawString(x0, self._y, key)
        self.c.setFont(self.style.font, self.style.size_small)
        self.c.drawRightString(self.width - self.style.margin_pt, self._y, value)
        self.newline(1.0)

    def wrap_text(self, text: str, max_width_pt: float, font: str, size: int) -> List[str]:
        words = (text or "").strip().split()
        if not words:
            return [""]
        lines: List[str] = []
        line = ""
        for w in words:
            candidate = (line + " " + w).strip()
            if pdfmetrics.stringWidth(candidate, font, size) <= max_width_pt:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines

    def money(self, amount) -> str:
        a = _safe_decimal(amount)
        return f"S/ {a:.2f}"


def estimate_height(lines: int, extra_pt: float = 0) -> float:
    # 1 línea ~ 10.5pt + márgenes; sumamos un poco para separadores
    base = mm_to_pt(20)  # top/bottom + cabecera mínima
    return base + (lines * 10.5) + extra_pt


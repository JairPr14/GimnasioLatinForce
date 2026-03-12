from __future__ import annotations

from decimal import Decimal


_UNIDADES = (
    "CERO", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE",
    "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE",
)

_DECENAS = (
    "", "", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"
)

_CENTENAS = (
    "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
    "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"
)


def _hasta_99(n: int) -> str:
    if n < 16:
        return _UNIDADES[n]
    if n < 20:
        return "DIECI" + _UNIDADES[n - 10].lower().upper()
    if n == 20:
        return "VEINTE"
    if n < 30:
        return "VEINTI" + _UNIDADES[n - 20].lower().upper()
    d, u = divmod(n, 10)
    if u == 0:
        return _DECENAS[d]
    return f"{_DECENAS[d]} Y {_UNIDADES[u]}"


def _hasta_999(n: int) -> str:
    if n == 0:
        return "CERO"
    if n == 100:
        return "CIEN"
    c, r = divmod(n, 100)
    if c == 0:
        return _hasta_99(r)
    if r == 0:
        return _CENTENAS[c]
    return f"{_CENTENAS[c]} {_hasta_99(r)}"


def _seccion(n: int, divisor: int, singular: str, plural: str) -> tuple[str, int]:
    q, r = divmod(n, divisor)
    if q == 0:
        return "", r
    if q == 1:
        return singular, r
    return f"{_hasta_999(q)} {plural}", r


def numero_a_letras(n: int) -> str:
    if n < 0:
        return "MENOS " + numero_a_letras(-n)
    if n == 0:
        return "CERO"

    partes = []
    texto, n = _seccion(n, 1_000_000, "UN MILLÓN", "MILLONES")
    if texto:
        partes.append(texto)
    texto, n = _seccion(n, 1000, "MIL", "MIL")
    if texto:
        partes.append(texto if texto == "MIL" else texto)
    if n:
        partes.append(_hasta_999(n))

    out = " ".join(partes).replace("  ", " ").strip()
    # En comprobantes se suele usar "UN" en lugar de "UNO" al final
    if out.endswith(" UNO"):
        out = out[:-4] + " UN"
    return out


def monto_soles_en_letras(monto) -> str:
    """
    Devuelve formato: "SON <LETRAS> Y <cc>/100 SOLES"
    """
    try:
        d = Decimal(str(monto)).quantize(Decimal("0.01"))
    except Exception:
        d = Decimal("0.00")
    entero = int(d)
    cent = int((d - Decimal(entero)) * 100)
    letras = numero_a_letras(entero)
    return f"SON {letras} Y {cent:02d}/100 SOLES"


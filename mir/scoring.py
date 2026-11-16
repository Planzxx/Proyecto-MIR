"""Conversión de nota en número de orden.

Las tablas son las referencias publicadas (netas necesarias por número de orden con un
expediente medio de 7,5). El número de orden se obtiene interpolando entre ellas, así que es
una estimación.
"""
ESCALAS = {
    "2026": {"puntos": 457.4, "expediente": 8.816, "tabla": [
        (100, 168.00), (1050, 149.00), (2100, 140.33), (3150, 133.33), (4200, 126.33), (5250, 119.33),
        (6300, 112.00), (7350, 103.33), (8400, 94.33), (9600, 82.33), (10700, 71.00)]},
    "2025": {"puntos": 385.2, "expediente": 8.802, "tabla": [
        (100, 144.33), (1050, 123.00), (2100, 113.67), (3150, 105.67), (4200, 99.00), (5250, 92.00),
        (6300, 84.33), (7350, 76.33), (8400, 68.33), (9600, 57.00), (10700, 46.00)]},
}
ORDEN_MAXIMO = 14000
EXPEDIENTE_REFERENCIA = 7.5


def redondear(x: float) -> int:
    """Redondeo «clásico» (0,5 hacia arriba), no el bancario de Python."""
    return int(x + 0.5)


def netas(aciertos: float, errores: float) -> float:
    return aciertos - errores / 3


def nota_total(netas_: float, expediente: float, escala: str) -> float:
    """Examen (sobre 90) + expediente (sobre 10)."""
    e = ESCALAS[escala]
    return netas_ * 3 * 90 / e["puntos"] + expediente * 10 / e["expediente"]


def orden_desde_nota(nota: float, escala: str) -> int:
    e = ESCALAS[escala]
    pts = [(o, nota_total(n, EXPEDIENTE_REFERENCIA, escala)) for o, n in e["tabla"]]
    pendiente0 = (pts[1][1] - pts[0][1]) / (pts[1][0] - pts[0][0])
    puntos = [(1, pts[0][1] - pendiente0 * (pts[0][0] - 1))] + pts
    if nota >= puntos[0][1]:
        return 1
    for (o1, t1), (o2, t2) in zip(puntos, puntos[1:]):
        if t2 <= nota <= t1:
            return redondear(o1 + (t1 - nota) / (t1 - t2) * (o2 - o1))
    (oa, ta), (ob, tb) = puntos[-2], puntos[-1]
    return min(ORDEN_MAXIMO, redondear(ob + (nota - tb) / ((tb - ta) / (ob - oa))))


def calcular(escala: str, netas_=None, expediente=None, orden=None, margen=10) -> dict | None:
    """Devuelve el nº de orden estimado y su rango, o None si faltan datos.

    Si se indica `orden`, sustituye al cálculo. `margen` es un porcentaje.
    Lanza ValueError si algún dato no es válido.
    """
    if escala not in ESCALAS:
        raise ValueError(f"Escala desconocida: {escala}")
    if not 0 <= margen <= 50:
        raise ValueError("El margen debe estar entre 0 y 50")
    nota = None
    if orden:
        if orden < 1:
            raise ValueError("El nº de orden debe ser 1 o mayor")
        n = int(orden)
    elif netas_ is not None and expediente is not None:
        if not 0 <= expediente <= 10:
            raise ValueError("El expediente debe estar entre 0 y 10")
        nota = nota_total(netas_, expediente, escala)
        n = orden_desde_nota(nota, escala)
    else:
        return None
    d = redondear(n * margen / 100)
    return {"orden": n, "mejor": max(1, n - d), "peor": n + d, "nota": nota, "margen": d}

"""Simulador de elección de plaza.

En el turno N estaban libres las plazas que, en la realidad, eligió alguien con un número de
orden igual o mayor que N: quienes iban antes ya habían elegido. Con esa premisa se reproduce
la elección de una lista de preferencias.
"""
from dataclasses import dataclass

from . import scoring
from .data import Catalogo, Plaza
from .texto import miles

# A partir de este número, una especialidad sigue eligiéndose después del último nº del listado,
# así que no se puede afirmar que esté agotada.
FIN_FIABLE = 4400
MAX_PREFERENCIAS = 12


@dataclass(frozen=True)
class Preferencia:
    e: int | None = None      # id de especialidad
    g: str | None = None      # comunidad
    c: int | None = None      # id de centro


def coincidencias(cat: Catalogo, p: Preferencia) -> list[Plaza]:
    return [x for x in cat.plazas
            if (p.e is None or x.e == p.e) and (p.c is None or x.c == p.c) and (not p.g or x.comunidad == p.g)]


def etiqueta(cat: Catalogo, p: Preferencia) -> str:
    sp = cat.especialidades[p.e] if p.e is not None else "Cualquier especialidad"
    donde = cat.centros[p.c] if p.c is not None else (p.g or "cualquier comunidad")
    return f"{sp} · {donde}"


def elegir(libres_desde: int, coinc: list[list[Plaza]]):
    """Primera preferencia con plaza libre; dentro de ella, la que antes eligieron los demás."""
    for i, lista in enumerate(coinc):
        libres = [x for x in lista if x.n >= libres_desde]
        if libres:
            return i, min(libres, key=lambda x: x.n), len(libres)
    return None


def _plural(n: int) -> str:
    return f"{n} plaza" + ("s" if n > 1 else "")


def estados(cat: Catalogo, turno: int, prefs: list[Preferencia], coinc, elegida) -> list[dict]:
    salida = []
    for i, (p, lista) in enumerate(zip(prefs, coinc)):
        if turno > cat.n_max:
            est, det = "sin_datos", "Tu turno queda fuera del listado."
        elif not lista:
            est, det = "sin_datos", "El listado no incluye plazas con estos criterios."
        else:
            libres = [x for x in lista if x.n >= turno]
            if libres:
                mejor = min(libres, key=lambda x: x.n)
                if elegida and elegida[0] == i:
                    est = "tu_plaza"
                    det = (f"Quedan {_plural(len(libres))} así en tu turno. "
                           f"La mejor: {cat.centros[mejor.c]}, que eligió el nº {miles(mejor.n)}.")
                else:
                    est = "libre"
                    det = f"Quedan {_plural(len(libres))}, pero ya tienes una preferencia mejor."
            else:
                ultimo = max(x.n for x in lista)
                tardia = p.e is None or cat.ultimo_n[p.e] >= FIN_FIABLE
                if tardia:
                    est = "sin_datos"
                    det = (f"En el listado se agotó en el nº {miles(ultimo)}, pero esta especialidad "
                           f"sigue eligiéndose después del {miles(cat.n_max)}.")
                else:
                    est = "agotada"
                    det = f"La última se eligió en el nº {miles(ultimo)}, antes de tu turno."
        salida.append({"pref": i + 1, "etiqueta": etiqueta(cat, p), "estado": est, "detalle": det})
    return salida


def escenario(cat, nombre, turno, coinc, principal):
    res = {"etiqueta": nombre, "orden": turno, "principal": principal,
           "fuera_de_rango": turno > cat.n_max, "resultado": None}
    if not res["fuera_de_rango"]:
        el = elegir(turno, coinc)
        if el:
            i, plaza, _ = el
            res["resultado"] = {**cat.dict_plaza(plaza), "preferencia": i + 1}
    return res


def que_quedaba(cat: Catalogo, turno: int) -> list[dict]:
    """Plazas libres por especialidad en el turno dado, de la más a la menos codiciada."""
    cuenta = {e: 0 for e in cat.primer_n}
    for p in cat.plazas:
        if p.n >= turno:
            cuenta[p.e] += 1
    filas = []
    for e in sorted(cat.primer_n, key=lambda k: cat.primer_n[k]):
        tardia = cat.ultimo_n[e] >= FIN_FIABLE
        if cuenta[e] > 0:
            est = "libres"
        elif not tardia:
            est = "agotada"
        else:
            est = "sin_datos"
        filas.append({"especialidad": cat.especialidades[e], "libres": cuenta[e], "mas": tardia,
                      "estado": est, "ultimo": cat.ultimo_n[e]})
    return filas


def cercanos(cat: Catalogo, turno: int, ventana: int = 6) -> list[dict]:
    """Lo que eligieron en la realidad los números alrededor del turno."""
    if turno > cat.n_max:
        return []
    idx = next((i for i, p in enumerate(cat.por_n) if p.n >= turno), len(cat.por_n) - 1)
    trozo = cat.por_n[max(0, idx - ventana): max(0, idx - ventana) + 2 * ventana + 1]
    primero = next((p.n for p in trozo if p.n >= turno), None)
    return [{**cat.dict_plaza(p), "tu_turno": p.n == primero} for p in trozo]


def simular(cat: Catalogo, escala: str, netas=None, expediente=None, orden=None, margen=10,
            prefs: list[Preferencia] | None = None) -> dict:
    prefs = prefs or []
    if len(prefs) > MAX_PREFERENCIAS:
        raise ValueError(f"Máximo {MAX_PREFERENCIAS} preferencias")
    calc = scoring.calcular(escala, netas, expediente, orden, margen)
    if calc is None:
        return {"calculo": None, "n_max": cat.n_max}
    coinc = [coincidencias(cat, p) for p in prefs]
    n = calc["orden"]
    if calc["mejor"] == calc["peor"]:
        escenarios = [escenario(cat, "Estimado", n, coinc, True)]
    else:
        escenarios = [escenario(cat, "Mejor caso", calc["mejor"], coinc, False),
                      escenario(cat, "Estimado", n, coinc, True),
                      escenario(cat, "Peor caso", calc["peor"], coinc, False)]
    elegida = None if n > cat.n_max else elegir(n, coinc)
    fuera = n > cat.n_max
    return {
        "calculo": calc,
        "n_max": cat.n_max,
        "escenarios": escenarios,
        "estados": estados(cat, n, prefs, coinc, elegida),
        "quedaba": [] if fuera else que_quedaba(cat, n),
        "cercanos": cercanos(cat, n),
    }

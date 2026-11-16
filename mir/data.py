"""Carga del listado y consultas: filtros, ordenación y resumen."""
import csv
from dataclasses import dataclass
from pathlib import Path

from .geo import region
from .texto import normalizar, titulo

RUTA_POR_DEFECTO = Path(__file__).resolve().parent.parent / "data" / "plazas.csv"


@dataclass(frozen=True)
class Plaza:
    adj: int          # orden de adjudicación
    n: int            # número de orden del aspirante
    e: int            # id de especialidad
    c: int            # id de centro
    localidad: str
    provincia: str
    comunidad: str
    busqueda: str     # texto normalizado para buscar


class Catalogo:
    def __init__(self, ruta=RUTA_POR_DEFECTO):
        with open(ruta, encoding="utf-8", newline="") as fh:
            filas = list(csv.DictReader(fh))
        raw_esp = sorted({f["especialidad"] for f in filas}, key=lambda s: titulo(s).casefold())
        raw_cen = sorted({f["centro"] for f in filas}, key=lambda s: titulo(s).casefold())
        self.especialidades = [titulo(s) for s in raw_esp]
        self.centros = [titulo(s) for s in raw_cen]
        id_e = {s: i for i, s in enumerate(raw_esp)}
        id_c = {s: i for i, s in enumerate(raw_cen)}
        self.plazas: list[Plaza] = []
        self.centro_localidad: dict[int, str] = {}
        for f in filas:
            prov, ccaa = region(f["localidad"])
            loc = titulo(f["localidad"])
            e, c = id_e[f["especialidad"]], id_c[f["centro"]]
            self.centro_localidad.setdefault(c, loc)
            busq = normalizar(" ".join((self.especialidades[e], self.centros[c], loc, prov, ccaa)))
            self.plazas.append(Plaza(int(f["adj"]), int(f["n"]), e, c, loc, prov, ccaa, busq))
        self.por_n = sorted(self.plazas, key=lambda p: p.n)
        self.n_max = self.por_n[-1].n
        self.comunidades = sorted({p.comunidad for p in self.plazas}, key=str.casefold)
        self.ultimo_n: dict[int, int] = {}
        self.primer_n: dict[int, int] = {}
        for p in self.plazas:
            self.ultimo_n[p.e] = max(self.ultimo_n.get(p.e, 0), p.n)
            self.primer_n[p.e] = min(self.primer_n.get(p.e, 10**9), p.n)

    # --- listas auxiliares para los desplegables ---
    def provincias(self, comunidad: str | None = None) -> list[str]:
        return sorted({p.provincia for p in self.plazas if not comunidad or p.comunidad == comunidad},
                      key=str.casefold)

    def centros_en(self, especialidad=None, comunidad=None, provincia=None) -> list[int]:
        ids = {p.c for p in self.plazas
               if (especialidad is None or p.e == especialidad)
               and (not comunidad or p.comunidad == comunidad)
               and (not provincia or p.provincia == provincia)}
        return sorted(ids, key=lambda i: self.centros[i].casefold())

    def id_especialidad(self, nombre: str) -> int | None:
        try:
            return self.especialidades.index(nombre)
        except ValueError:
            return None

    # --- consultas ---
    def filtrar(self, q="", e=None, g="", p="", c=None, n1=None, n2=None) -> list[Plaza]:
        terminos = normalizar(q.strip()).split()
        res = []
        for pl in self.plazas:
            if e is not None and pl.e != e:
                continue
            if c is not None and pl.c != c:
                continue
            if g and pl.comunidad != g:
                continue
            if p and pl.provincia != p:
                continue
            if n1 is not None and pl.n < n1:
                continue
            if n2 is not None and pl.n > n2:
                continue
            if any(t not in pl.busqueda for t in terminos):
                continue
            res.append(pl)
        return res

    def ordenar(self, plazas: list[Plaza], campo="a", descendente=False) -> list[Plaza]:
        clave = {
            "a": lambda x: x.adj,
            "n": lambda x: x.n,
            "e": lambda x: self.especialidades[x.e].casefold(),
            "c": lambda x: self.centros[x.c].casefold(),
            "l": lambda x: x.localidad.casefold(),
        }[campo]
        # Desempate por orden de adjudicación, como en la versión web original.
        ordenadas = sorted(plazas, key=lambda x: (clave(x), x.adj))
        if descendente:
            ordenadas = sorted(plazas, key=lambda x: (clave(x), x.adj), reverse=True)
        return ordenadas

    def resumen(self, plazas: list[Plaza], por="e") -> list[dict]:
        etiqueta = {"e": lambda x: self.especialidades[x.e], "c": lambda x: self.centros[x.c],
                    "a": lambda x: x.comunidad, "p": lambda x: x.provincia}[por]
        clave = {"e": lambda x: x.e, "c": lambda x: x.c, "a": lambda x: x.comunidad, "p": lambda x: x.provincia}[por]
        sub = {"c": lambda x: x.localidad, "p": lambda x: x.comunidad}.get(por)
        grupos: dict = {}
        for pl in plazas:
            k = clave(pl)
            g = grupos.get(k)
            if g is None:
                g = grupos[k] = {"k": k, "nombre": etiqueta(pl), "sub": sub(pl) if sub else "",
                                 "plazas": 0, "min": pl.n, "max": pl.n}
            g["plazas"] += 1
            g["min"] = min(g["min"], pl.n)
            g["max"] = max(g["max"], pl.n)
        return list(grupos.values())

    def dict_plaza(self, pl: Plaza) -> dict:
        return {"a": pl.adj, "n": pl.n, "e": pl.e, "c": pl.c,
                "especialidad": self.especialidades[pl.e], "centro": self.centros[pl.c],
                "localidad": pl.localidad, "provincia": pl.provincia, "comunidad": pl.comunidad}

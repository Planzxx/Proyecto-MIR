"""Importa el PDF «Listado de plazas adjudicadas» y lo convierte en data/plazas.csv.

Uso:
    python -m mir.pdf_import LISTADO.pdf -o data/plazas.csv

Requiere pdfplumber (solo para importar; la aplicación no lo necesita).
"""
import argparse
import csv
import re
import sys

COLUMNAS = ["adj", "n", "localidad", "centro", "especialidad"]

# Límites horizontales (puntos PDF) de las columnas del listado.
X_ORDEN_MAX = 105     # «Número de orden»
X_ADJ_MAX = 140       # «Orden de adjudicación»
X_CENTRO_MIN = 305
X_ESPEC_MIN = 445

# Correcciones de textos partidos por el salto de línea del PDF.
ARREGLOS_ESPECIALIDAD = {"CIRUGÍA PLÁSTICA ESTÉTICA Y": "CIRUGÍA PLÁSTICA ESTÉTICA Y REPARADORA"}


def _filas_de_pagina(pagina):
    palabras = pagina.extract_words(x_tolerance=1.2)
    anclas = []
    for a in sorted((w for w in palabras if w["x0"] < X_ORDEN_MAX and re.fullmatch(r"\d+", w["text"])),
                    key=lambda w: w["top"]):
        adj = [w for w in palabras if X_ORDEN_MAX <= w["x0"] < X_ADJ_MAX
               and abs(w["top"] - a["top"]) < 3 and re.fullmatch(r"\d+", w["text"])]
        if adj:
            anclas.append({"top": a["top"], "n": int(a["text"]), "adj": int(adj[0]["text"]),
                           "localidad": [], "centro": [], "especialidad": []})
    for w in sorted(palabras, key=lambda w: (round(w["top"]), w["x0"])):
        if w["x0"] < X_ADJ_MAX:
            continue
        if w["text"] in ("LOCALIDAD", "CENTRO", "ESPECIALIDAD") and w["top"] < 75:
            continue
        columna = "localidad" if w["x0"] < X_CENTRO_MIN else "centro" if w["x0"] < X_ESPEC_MIN else "especialidad"
        if w["x0"] <= 312 and w["text"] in ("P", "A") and w["top"] < 90 \
                and not any(abs(a["top"] - w["top"]) < 3 for a in anclas):
            continue  # marcas «P» y «A» de la cabecera
        destino = None
        for a in anclas:  # la última fila que empieza por encima (las líneas partidas van debajo)
            if a["top"] <= w["top"] + 2.5:
                destino = a
        if destino is not None:
            destino[columna].append(w["text"])
    return anclas


def importar(ruta_pdf: str) -> list[dict]:
    import pdfplumber  # import tardío: solo hace falta aquí

    filas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            filas.extend(_filas_de_pagina(pagina))
    vistos, limpias = {}, []
    for f in filas:
        fila = {"adj": f["adj"], "n": f["n"], "localidad": " ".join(f["localidad"]),
                "centro": " ".join(f["centro"]).replace("- INFANTIL", "-INFANTIL"),
                "especialidad": " ".join(f["especialidad"])}
        fila["especialidad"] = ARREGLOS_ESPECIALIDAD.get(fila["especialidad"], fila["especialidad"])
        if fila["n"] in vistos:   # el PDF repite algunas plazas en varias páginas
            if vistos[fila["n"]] != fila:
                raise ValueError(f"Fila repetida con datos distintos: {fila}")
            continue
        vistos[fila["n"]] = fila
        limpias.append(fila)
    return sorted(limpias, key=lambda f: f["adj"])


def guardar(filas: list[dict], destino: str) -> None:
    with open(destino, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf")
    ap.add_argument("-o", "--salida", default="data/plazas.csv")
    args = ap.parse_args(argv)
    filas = importar(args.pdf)
    guardar(filas, args.salida)
    print(f"{len(filas)} plazas guardadas en {args.salida}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

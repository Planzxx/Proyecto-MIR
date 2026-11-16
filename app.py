"""Servidor web de Plazas MIR.

    python app.py            # abre http://127.0.0.1:5000
    python app.py --puerto 8080 --datos otro.csv
"""
import argparse
import threading
import webbrowser

from flask import Flask, jsonify, render_template, request

from mir import scoring, simulator
from mir.data import RUTA_POR_DEFECTO, Catalogo
from mir.texto import miles

MAX_LIMITE = 500


class ErrorDeUso(ValueError):
    """Dato de entrada no válido (se responde con 400)."""


def _int(valor, nombre, minimo=None, maximo=None):
    if valor in (None, ""):
        return None
    try:
        v = int(valor)
    except (TypeError, ValueError):
        raise ErrorDeUso(f"«{nombre}» debe ser un número entero") from None
    if (minimo is not None and v < minimo) or (maximo is not None and v > maximo):
        raise ErrorDeUso(f"«{nombre}» fuera de rango")
    return v


def _float(valor, nombre):
    if valor in (None, ""):
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        raise ErrorDeUso(f"«{nombre}» debe ser un número") from None


def create_app(ruta_datos=RUTA_POR_DEFECTO) -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    cat = Catalogo(ruta_datos)

    def filtros(a):
        return dict(q=a.get("q", ""), e=_int(a.get("e"), "especialidad"), g=a.get("g", ""),
                    p=a.get("p", ""), c=_int(a.get("c"), "centro"),
                    n1=_int(a.get("n1"), "nº de orden desde"), n2=_int(a.get("n2"), "nº de orden hasta"))

    @app.errorhandler(ValueError)
    def error_valor(e):
        return jsonify(error=str(e)), 400

    @app.get("/")
    def inicio():
        return render_template("index.html", n_max=cat.n_max, total_txt=miles(len(cat.plazas)))

    @app.get("/api/meta")
    def meta():
        ejemplo = [("Cardiología", "Madrid"), ("Cardiología", None), ("Aparato Digestivo", "Madrid"),
                   ("Anestesiología y Reanimación", None), ("Medicina Interna", None)]
        return jsonify(
            total=len(cat.plazas), n_max=cat.n_max,
            especialidades=[{"id": i, "nombre": n} for i, n in enumerate(cat.especialidades)],
            comunidades=cat.comunidades,
            escalas=sorted(scoring.ESCALAS, reverse=True),
            prefs_ejemplo=[{"e": cat.id_especialidad(n), "g": g, "c": None} for n, g in ejemplo],
            max_preferencias=simulator.MAX_PREFERENCIAS)

    @app.get("/api/opciones")
    def opciones():
        """Provincias y centros disponibles para el filtro actual (desplegables dependientes)."""
        e = _int(request.args.get("e"), "especialidad")
        g, p = request.args.get("g", ""), request.args.get("p", "")
        return jsonify(
            provincias=cat.provincias(g),
            centros=[{"id": i, "nombre": cat.centros[i], "localidad": cat.centro_localidad[i]}
                     for i in cat.centros_en(e, g, p)])

    @app.get("/api/plazas")
    def plazas():
        f = filtros(request.args)
        res = cat.ordenar(cat.filtrar(**f), request.args.get("sort", "a"), request.args.get("dir") == "desc")
        offset = _int(request.args.get("offset"), "offset", 0) or 0
        limite = min(_int(request.args.get("limit"), "limit", 1) or 100, MAX_LIMITE)
        return jsonify(total=len(res), ultimo_n=max((p.n for p in res), default=None),
                       filas=[cat.dict_plaza(p) for p in res[offset: offset + limite]])

    @app.get("/api/resumen")
    def resumen():
        f = filtros(request.args)
        por = request.args.get("grp", "e")
        if por not in ("e", "c", "a", "p"):
            raise ErrorDeUso("Agrupación desconocida")
        orden = request.args.get("sort", "nombre")
        claves = {"nombre": lambda g: g["nombre"].casefold(), "plazas": lambda g: g["plazas"],
                  "min": lambda g: g["min"], "max": lambda g: g["max"]}
        if orden not in claves:
            raise ErrorDeUso("Orden desconocido")
        plazas_ = cat.filtrar(**f)
        grupos = sorted(cat.resumen(plazas_, por), key=claves[orden], reverse=request.args.get("dir") == "desc")
        return jsonify(total=len(plazas_), ultimo_n=max((p.n for p in plazas_), default=None), grupos=grupos)

    @app.get("/api/centros")
    def centros():
        """Centros para una preferencia del simulador (según especialidad y comunidad)."""
        e = _int(request.args.get("e"), "especialidad")
        g = request.args.get("g", "")
        return jsonify([{"id": i, "etiqueta": f"{cat.centros[i]} ({cat.centro_localidad[i]})"}
                        for i in cat.centros_en(e, g)])

    @app.post("/api/simulador")
    def simular():
        d = request.get_json(silent=True)
        if not isinstance(d, dict):
            raise ErrorDeUso("Se esperaba un JSON")
        prefs = []
        for p in d.get("prefs") or []:
            if not isinstance(p, dict):
                raise ErrorDeUso("Preferencia no válida")
            e, c = _int(p.get("e"), "especialidad"), _int(p.get("c"), "centro")
            if (e is not None and not 0 <= e < len(cat.especialidades)) or \
               (c is not None and not 0 <= c < len(cat.centros)):
                raise ErrorDeUso("Especialidad o centro desconocido")
            prefs.append(simulator.Preferencia(e, p.get("g") or None, c))
        return jsonify(simulator.simular(
            cat, str(d.get("escala", "2026")), _float(d.get("netas"), "netas"),
            _float(d.get("expediente"), "expediente"), _int(d.get("orden"), "nº de orden", 1),
            _int(d.get("margen", 10), "margen", 0, 50), prefs))

    return app


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--puerto", type=int, default=5000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--datos", default=str(RUTA_POR_DEFECTO), help="CSV de plazas")
    ap.add_argument("--no-abrir", action="store_true", help="No abrir el navegador")
    args = ap.parse_args(argv)
    app = create_app(args.datos)
    if not args.no_abrir:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{args.host}:{args.puerto}")).start()
    app.run(host=args.host, port=args.puerto)


if __name__ == "__main__":
    main()

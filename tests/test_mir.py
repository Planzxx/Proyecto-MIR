import unittest

from app import create_app
from mir import scoring, simulator
from mir.data import Catalogo
from mir.texto import miles, normalizar, titulo

CAT = Catalogo()


class TestTexto(unittest.TestCase):
    def test_titulo(self):
        self.assertEqual(titulo("H. UNIVERSITARIO LA PAZ"), "H. Universitario La Paz")
        self.assertEqual(titulo("H. UNIVERSITARIO VIRGEN DE LAS NIEVES"), "H. Universitario Virgen de las Nieves")
        self.assertEqual(titulo("C.H.UNIVERSITARIO INSULAR"), "C.H. Universitario Insular")
        self.assertEqual(titulo("UDM AFYC SEVILLA"), "UDM AFYC Sevilla")
        self.assertEqual(titulo("C.H. UNIVERSITARIO A CORUÑA"), "C.H. Universitario A Coruña")

    def test_normalizar_y_miles(self):
        self.assertEqual(normalizar("Cardiología ÁVILA"), "cardiologia avila")
        self.assertEqual(miles(12345), "12.345")


class TestNotas(unittest.TestCase):
    def test_ejemplo_publicado(self):
        # 102 netas y expediente 7,50 en 2026: 60,21 + 8,51 = 68,72 puntos, orden ~7.500.
        nota = scoring.nota_total(102, 7.5, "2026")
        self.assertAlmostEqual(nota, 68.72, places=2)
        self.assertAlmostEqual(scoring.orden_desde_nota(nota, "2026"), 7500, delta=60)

    def test_monotonia(self):
        ordenes = [scoring.orden_desde_nota(scoring.nota_total(n, 7.5, "2026"), "2026") for n in range(60, 175, 5)]
        self.assertEqual(ordenes, sorted(ordenes, reverse=True))

    def test_extremos(self):
        self.assertEqual(scoring.orden_desde_nota(130, "2026"), 1)
        self.assertLessEqual(scoring.orden_desde_nota(0, "2026"), scoring.ORDEN_MAXIMO)

    def test_calcular(self):
        c = scoring.calcular("2026", 136.67, 7.5, None, 10)
        self.assertEqual((c["orden"], c["mejor"], c["peor"]), (2649, 2384, 2914))
        self.assertEqual(scoring.calcular("2026", orden=300, margen=0)["peor"], 300)
        self.assertIsNone(scoring.calcular("2026"))
        with self.assertRaises(ValueError):
            scoring.calcular("2026", 100, 11)
        with self.assertRaises(ValueError):
            scoring.calcular("1999", 100, 7)

    def test_netas(self):
        self.assertAlmostEqual(scoring.netas(140, 40), 126.6667, places=3)


class TestDatos(unittest.TestCase):
    def test_carga(self):
        self.assertEqual(len(CAT.plazas), 4710)
        self.assertEqual(len({p.adj for p in CAT.plazas}), 4710)
        self.assertEqual(len({p.n for p in CAT.plazas}), 4710)
        self.assertEqual(CAT.n_max, 4800)
        self.assertEqual(len(CAT.especialidades), 43)

    def test_primera_plaza(self):
        p = CAT.por_n[0]
        self.assertEqual((p.n, CAT.centros[p.c], p.provincia), (1, "H. Universitario Virgen de las Nieves", "Granada"))

    def test_busqueda_sin_tildes_y_varios_terminos(self):
        todas = CAT.filtrar(q="cardiologia madrid")
        self.assertEqual(len(todas), 34)
        self.assertTrue(all(p.comunidad == "Madrid" for p in todas))

    def test_filtros_y_rango(self):
        derm = CAT.id_especialidad("Dermatología Médico-Quirúrgica y V.")
        res = CAT.filtrar(e=derm)
        self.assertEqual((len(res), max(p.n for p in res)), (115, 721))
        self.assertTrue(all(100 <= p.n <= 200 for p in CAT.filtrar(n1=100, n2=200)))

    def test_orden(self):
        asc = CAT.ordenar(CAT.filtrar(), "n")
        self.assertEqual([p.n for p in asc], sorted(p.n for p in asc))
        desc = CAT.ordenar(CAT.filtrar(), "n", True)
        self.assertEqual(desc[0].n, 4800)

    def test_resumen(self):
        por_ccaa = {g["nombre"]: g for g in CAT.resumen(CAT.plazas, "a")}
        self.assertEqual(por_ccaa["Madrid"]["plazas"], 974)
        self.assertEqual(sum(g["plazas"] for g in por_ccaa.values()), 4710)


class TestSimulador(unittest.TestCase):
    def setUp(self):
        card, dig = CAT.id_especialidad("Cardiología"), CAT.id_especialidad("Aparato Digestivo")
        self.prefs = [simulator.Preferencia(card, "Madrid"), simulator.Preferencia(card),
                      simulator.Preferencia(dig, "Madrid")]

    def test_caso_ejemplo(self):
        r = simulator.simular(CAT, "2026", 136.67, 7.5, None, 10, self.prefs)
        est = {e["etiqueta"]: e["resultado"] for e in r["escenarios"]}
        self.assertEqual(est["Estimado"]["centro"], "C.H. Universitario de Cáceres")
        self.assertEqual(est["Estimado"]["preferencia"], 2)
        self.assertEqual([e["estado"] for e in r["estados"]], ["agotada", "tu_plaza", "libre"])

    def test_turno_temprano_consigue_la_primera(self):
        r = simulator.simular(CAT, "2026", orden=300, margen=0, prefs=self.prefs)
        res = r["escenarios"][0]["resultado"]
        self.assertEqual((res["preferencia"], res["comunidad"]), (1, "Madrid"))
        self.assertGreaterEqual(res["n"], 300)

    def test_nunca_se_elige_plaza_de_alguien_anterior(self):
        for turno in (50, 800, 2000, 4000):
            r = simulator.simular(CAT, "2026", orden=turno, margen=0, prefs=self.prefs)
            res = r["escenarios"][0]["resultado"]
            if res:
                self.assertGreaterEqual(res["n"], turno)

    def test_fuera_de_rango(self):
        r = simulator.simular(CAT, "2026", orden=5000, margen=0, prefs=self.prefs)
        self.assertTrue(r["escenarios"][0]["fuera_de_rango"])
        self.assertEqual(r["quedaba"], [])
        self.assertEqual(r["cercanos"], [])
        self.assertEqual({e["estado"] for e in r["estados"]}, {"sin_datos"})

    def test_agotada_vs_sin_datos_fiables(self):
        derm = CAT.id_especialidad("Dermatología Médico-Quirúrgica y V.")
        r = simulator.simular(CAT, "2026", orden=1500, margen=0, prefs=[simulator.Preferencia(derm)])
        self.assertEqual(r["estados"][0]["estado"], "agotada")
        mi = CAT.id_especialidad("Medicina Interna")
        r = simulator.simular(CAT, "2026", orden=4790, margen=0, prefs=[simulator.Preferencia(mi)])
        self.assertIn(r["estados"][0]["estado"], ("tu_plaza", "sin_datos"))

    def test_sin_datos_suficientes(self):
        self.assertIsNone(simulator.simular(CAT, "2026", prefs=self.prefs)["calculo"])

    def test_cercanos_incluyen_el_turno(self):
        r = simulator.simular(CAT, "2026", orden=2000, margen=0, prefs=self.prefs)
        self.assertEqual(sum(c["tu_turno"] for c in r["cercanos"]), 1)
        self.assertEqual(len(r["cercanos"]), 13)

    def test_limite_de_preferencias(self):
        with self.assertRaises(ValueError):
            simulator.simular(CAT, "2026", orden=100, prefs=[simulator.Preferencia()] * 13)


class TestApi(unittest.TestCase):
    def setUp(self):
        self.c = create_app().test_client()

    def test_paginas_y_meta(self):
        self.assertEqual(self.c.get("/").status_code, 200)
        m = self.c.get("/api/meta").json
        self.assertEqual((m["total"], m["n_max"]), (4710, 4800))
        self.assertEqual(len(m["prefs_ejemplo"]), 5)

    def test_plazas_paginadas(self):
        a = self.c.get("/api/plazas?limit=10").json
        b = self.c.get("/api/plazas?limit=10&offset=10").json
        self.assertEqual((a["total"], len(a["filas"])), (4710, 10))
        self.assertNotEqual(a["filas"][0]["a"], b["filas"][0]["a"])
        self.assertEqual(self.c.get("/api/plazas?limit=100000").json["filas"][499]["a"], 500)

    def test_opciones_dependientes(self):
        o = self.c.get("/api/opciones?g=Galicia").json
        self.assertEqual(set(o["provincias"]), {"A Coruña", "Lugo", "Ourense", "Pontevedra"})
        self.assertTrue(all(len(c["nombre"]) for c in o["centros"]))

    def test_errores_de_entrada(self):
        self.assertEqual(self.c.get("/api/plazas?e=abc").status_code, 400)
        self.assertEqual(self.c.get("/api/resumen?grp=x").status_code, 400)
        self.assertEqual(self.c.post("/api/simulador", data="no json").status_code, 400)
        self.assertEqual(self.c.post("/api/simulador", json={"orden": 100, "prefs": [{"e": 999}]}).status_code, 400)
        self.assertEqual(self.c.post("/api/simulador", json={"orden": 100, "margen": 99}).status_code, 400)

    def test_simulador_http(self):
        r = self.c.post("/api/simulador", json={"escala": "2026", "orden": 300, "margen": 0,
                                                "prefs": [{"e": None, "g": "Madrid", "c": None}]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["calculo"]["orden"], 300)


if __name__ == "__main__":
    unittest.main()

"""Tests del servicio de cálculo (paso de conexión V3).

Ejercitan los handlers DIRECTAMENTE con productor/solver FALSOS: no requieren
PyNite instalado (la física PyNite ya está cubierta y verde en qa-pynite/firma).
Aquí se valida la MÁQUINA del servicio: estados de las dos llaves, EC3 «qué no
cumple», guarda de firma, meta de gobierno (provisional/independiente) y el
servidor HTTP stdlib (CORS, rutas, errores claros).

Ejecutable directo (`python tests/test_service.py`) o con pytest/unittest.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import unittest
from dataclasses import replace
from http.client import HTTPConnection

_here = os.path.dirname(__file__)
for rel in (("..", "src"), ("..", "..", "puente-calculo", "src"), ("..", "..", "qa-pynite", "src"),
            ("..", "..", "verificacion-ec", "src"), ("..", "..", "firma", "src")):
    sys.path.insert(0, os.path.join(_here, *rel))

from puente_calculo import contract as c  # noqa: E402
from servicio_calculo import app, producer as prod  # noqa: E402
from servicio_calculo.server import _Handler  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

# ── Caso patrón: ménsula B1 (N1 empotrado -> N2), carga puntual -Z en N2 ────────
SEC = c.SectionRef(
    profile="IPE300",
    props=c.SectionProps(A=0.00538, I_strong=8.356e-5, I_weak=6.04e-6, J=2.01e-7,
                         Wpl_strong=6.28e-4, Wpl_weak=1.25e-4),
    materialProps=c.MaterialProps(E=2.1e8, G=8.08e7, density=78.5, fy_or_fck=2.75e5),
)
PAYLOAD = {
    "model": {
        "nodes": [{"id": "N1", "x": 0, "y": 0, "z": 0}, {"id": "N2", "x": 4, "y": 0, "z": 0}],
        "members": [{
            "id": "B1", "kind": "beam", "nodeStart": "N1", "nodeEnd": "N2",
            "section": {
                "profile": "IPE300",
                "props": {"A": 0.00538, "I_strong": 8.356e-5, "I_weak": 6.04e-6, "J": 2.01e-7,
                          "Wpl_strong": 6.28e-4, "Wpl_weak": 1.25e-4},
                "materialProps": {"E": 2.1e8, "G": 8.08e7, "density": 78.5, "fy_or_fck": 2.75e5},
            },
        }],
        "supports": [{"id": "S1", "nodeId": "N1",
                      "restraints": {"ux": True, "uy": True, "uz": True, "rx": True, "ry": True, "rz": True}}],
        "loads": [{"id": "L1", "kind": "point", "target": "N2", "value": 100.0, "direction": "z", "case": "G"}],
    },
    "combinations": [{"id": "ELU1", "name": "ELU", "limitState": "ULS", "terms": {"G": 1.0}}],
}

REACTION_FZ = 100.0  # equilibra la carga puntual de 100 kN (-Z) -> +Z en N1


def _fake_group(*, reaction_fz: float = REACTION_FZ, m_strong: float = 200.0, axial: float = 50.0) -> c.ResultGroup:
    """Grupo `computed` fabricado: B1 con flector que NO cumple a flexión (u>1)."""
    return c.ResultGroup(
        id="RG-ELU1", combinationId="ELU1", state="computed",
        members=[c.MemberResult(memberId="B1", stations=[
            c.MemberStation(x=0.0, N=axial, V_strong=0.0, V_weak=0.0, M_strong=m_strong, M_weak=0.0,
                            T=0.0, dx=0.0, dy=0.0, dz=-0.01),
            c.MemberStation(x=4.0, N=axial, V_strong=0.0, V_weak=0.0, M_strong=0.0, M_weak=0.0,
                            T=0.0, dx=0.0, dy=0.0, dz=-0.05),
        ])],
        nodes=[
            c.NodeResult(nodeId="N1", ux=0, uy=0, uz=0, rx=0, ry=0, rz=0,
                         reaction=c.NodeReaction(fx=0, fy=0, fz=reaction_fz, mx=0, my=0, mz=0)),
            c.NodeResult(nodeId="N2", ux=0, uy=0, uz=-0.05, rx=0, ry=0, rz=0, reaction=None),
        ],
        surfaces=[],
    )


def _fake_producer(req: c.CalcRequest) -> list[c.ResultGroup]:
    return [_fake_group()]


def _fake_qa_solver(req: c.CalcRequest, combo_id: str) -> c.ResultGroup:
    return _fake_group()  # QA coincide con el motor -> reconcilia


def _fake_qa_solver_bad(req: c.CalcRequest, combo_id: str) -> c.ResultGroup:
    return _fake_group(reaction_fz=REACTION_FZ * 1.3)  # 30% -> discrepancia -> qa-fail


class TestSolve(unittest.TestCase):
    def test_solve_computed_con_ec3_y_no_cumple(self):
        status, body = app.handle_solve(PAYLOAD, producer=_fake_producer, producer_id=prod.PROVISIONAL_ID)
        self.assertEqual(status, 200)
        g = body["groups"][0]
        self.assertEqual(g["state"], "computed")                 # nace 0 llaves
        self.assertGreater(g["members"][0]["utilization"], 1.0)  # EC3 relleno: no cumple
        self.assertIn("flexion", g["members"][0]["governing"])
        self.assertFalse(g["members"][0]["passes"])
        self.assertEqual(body["summary"][0]["notPassingIds"], ["B1"])
        self.assertEqual(body["summary"][0]["atLimitIds"], ["B1"])

    def test_solve_meta_provisional_no_independiente(self):
        _, body = app.handle_solve(PAYLOAD, producer=_fake_producer, producer_id=prod.PROVISIONAL_ID)
        meta = body["meta"]
        self.assertTrue(meta["provisional"])
        self.assertFalse(meta["independent"])        # PyNite produce y verifica -> no independiente
        self.assertTrue(meta["warning"])             # aviso de gobierno presente

    def test_solve_nunca_devuelve_verde(self):
        _, body = app.handle_solve(PAYLOAD, producer=_fake_producer, producer_id=prod.PROVISIONAL_ID)
        for g in body["groups"]:
            self.assertNotEqual(g["state"], "verified-signed")   # regla inviolable


class TestQA(unittest.TestCase):
    def _computed_group(self) -> dict:
        _, body = app.handle_solve(PAYLOAD, producer=_fake_producer, producer_id=prod.PROVISIONAL_ID)
        return body["groups"][0]

    def test_qa_passed_pone_primera_llave(self):
        payload = {**PAYLOAD, "group": self._computed_group()}
        status, body = app.handle_qa(payload, qa_solver=_fake_qa_solver)
        self.assertEqual(status, 200)
        self.assertEqual(body["verdict"], "qa-passed")
        self.assertIsNotNone(body["group"])
        self.assertEqual(body["group"]["state"], "qa-passed")    # 1.ª llave puesta

    def test_qa_fail_bloquea(self):
        payload = {**PAYLOAD, "group": self._computed_group()}
        status, body = app.handle_qa(payload, qa_solver=_fake_qa_solver_bad)
        self.assertEqual(status, 200)
        self.assertEqual(body["verdict"], "qa-fail")
        self.assertIsNone(body["group"])                         # nada que elevar (bloqueo)
        self.assertTrue(body["report"]["discrepancies"])         # discrepancia expuesta


class TestSign(unittest.TestCase):
    def _qa_passed_group(self) -> dict:
        _, body = app.handle_solve(PAYLOAD, producer=_fake_producer, producer_id=prod.PROVISIONAL_ID)
        payload = {**PAYLOAD, "group": body["groups"][0]}
        _, qa = app.handle_qa(payload, qa_solver=_fake_qa_solver)
        return qa["group"]

    def test_firma_eleva_a_verde(self):
        status, body = app.handle_sign({"group": self._qa_passed_group(), "signer": "JM"})
        self.assertEqual(status, 200)
        self.assertEqual(body["group"]["state"], "verified-signed")  # 2.ª llave: verde
        self.assertEqual(body["record"]["signer"], "JM")

    def test_no_se_firma_sin_qa(self):
        _, body0 = app.handle_solve(PAYLOAD, producer=_fake_producer, producer_id=prod.PROVISIONAL_ID)
        status, body = app.handle_sign({"group": body0["groups"][0], "signer": "JM"})
        self.assertEqual(status, 409)                            # computed no es firmable
        self.assertEqual(body["state"], "computed")

    def test_firma_exige_firmante(self):
        status, body = app.handle_sign({"group": self._qa_passed_group()})
        self.assertEqual(status, 400)                            # la IA no firma: falta signer
        self.assertIn("signer", body["error"])


class TestEc3(unittest.TestCase):
    def test_ec3_rellena_aprovechamiento(self):
        raw = _fake_group()
        raw = replace(raw, members=[replace(raw.members[0], utilization=0.0, governing=None, passes=True)])
        from servicio_calculo.serialize import result_group_to_dict
        payload = {**PAYLOAD, "group": result_group_to_dict(raw)}
        status, body = app.handle_ec3(payload)
        self.assertEqual(status, 200)
        self.assertGreater(body["group"]["members"][0]["utilization"], 1.0)
        self.assertEqual(body["summary"]["notPassing"], 1)


class TestServerHTTP(unittest.TestCase):
    """Servidor stdlib: /health, preflight CORS y 404. (No toca el productor real.)"""

    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.httpd.server_address[1]
        cls.t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _conn(self) -> HTTPConnection:
        return HTTPConnection("127.0.0.1", self.port, timeout=5)

    def test_health(self):
        conn = self._conn()
        conn.request("GET", "/health")
        r = conn.getresponse()
        self.assertEqual(r.status, 200)
        body = json.loads(r.read())
        self.assertTrue(body["ok"])
        self.assertIn("pyniteAvailable", body)

    def test_preflight_cors(self):
        conn = self._conn()
        conn.request("OPTIONS", "/solve", headers={"Origin": "http://localhost:5173"})
        r = conn.getresponse()
        r.read()
        self.assertEqual(r.status, 204)
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "http://localhost:5173")

    def test_404(self):
        conn = self._conn()
        conn.request("GET", "/nope")
        r = conn.getresponse()
        self.assertEqual(r.status, 404)
        r.read()


def _run() -> int:
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(_run())

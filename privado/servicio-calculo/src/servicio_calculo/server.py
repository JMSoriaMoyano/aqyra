"""Servidor HTTP LOCAL del servicio de cálculo (stdlib, sin dependencias).

Por qué stdlib y no FastAPI/Flask: el servicio es un helper LOCAL del anzuelo; un
servidor de la librería estándar no añade dependencias, arranca en cualquier Python
3.10+ y mantiene la superficie mínima. El visor (cebo) sigue SIN servidor para VER;
solo el POST del post-proceso llama aquí (D-019·C.4).

Arranque:  python -m servicio_calculo            (escucha en 127.0.0.1:8765)
           AQYRA_CALC_PORT=9000 python -m servicio_calculo
CORS abierto al dev-server del visor (localhost:5173) para el fetch del navegador.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .app import ROUTES, handle_health

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
# Orígenes permitidos para el navegador (dev-server Vite del visor).
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}


class _Handler(BaseHTTPRequestHandler):
    server_version = "AqyraCalc/0.1"

    # — utilidades —
    def _cors(self) -> None:
        origin = self.headers.get("Origin", "")
        allow = origin if origin in ALLOWED_ORIGINS else "*"
        self.send_header("Access-Control-Allow-Origin", allow)
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw or b"{}")

    def log_message(self, *args: Any) -> None:  # silencio (evita ruido en consola)
        pass

    # — métodos HTTP —
    def do_OPTIONS(self) -> None:  # preflight CORS
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path.rstrip("/") in ("/health", "/"):
            status, body = handle_health()
            self._send(status, body)
        else:
            self._send(404, {"error": f"no encontrado: GET {self.path}"})

    def do_POST(self) -> None:
        handler = ROUTES.get(("POST", self.path.rstrip("/") or "/"))
        if handler is None:
            self._send(404, {"error": f"no encontrado: POST {self.path}"})
            return
        try:
            payload = self._read_json()
        except json.JSONDecodeError as exc:
            self._send(400, {"error": f"JSON inválido: {exc}"})
            return
        try:
            status, body = handler(payload)
        except KeyError as exc:
            self._send(400, {"error": f"falta campo requerido: {exc}"})
        except Exception as exc:  # noqa: BLE001  (no fingir cálculo: error claro)
            self._send(500, {"error": f"{type(exc).__name__}: {exc}"})
        else:
            self._send(status, body)


def serve(host: str = DEFAULT_HOST, port: int | None = None) -> None:
    port = port if port is not None else int(os.environ.get("AQYRA_CALC_PORT", DEFAULT_PORT))
    httpd = ThreadingHTTPServer((host, port), _Handler)
    print(f"servicio-calculo escuchando en http://{host}:{port}  (Ctrl+C para parar)")
    print("  POST /solve · /qa · /sign · /ec3   GET /health")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nparado.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    serve()

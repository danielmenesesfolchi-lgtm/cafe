"""Servidor del sitio: sirve los archivos estáticos y guarda los contactos.

Uso:  python server.py [puerto]     (por defecto 8000)
Los envíos se guardan en contactos.jsonl (una consulta por línea).
Solo usa la biblioteca estándar.
"""
import json
import re
import sys
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).parent
ARCHIVO = RAIZ / "contactos.jsonl"
CAMPOS = ["nombre", "empresa", "email", "telefono", "pais", "tipo", "volumen", "mensaje"]
REQUERIDOS = ["nombre", "empresa", "email", "pais", "tipo", "volumen"]
MAX_BYTES = 20_000
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PUBLICOS = {"/", "/index.html", "/styles.css", "/script.js"}


class Handler(SimpleHTTPRequestHandler):
    def _json(self, codigo, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        # Solo se exponen los archivos del sitio (no el JSONL ni el servidor).
        if self.path.split("?")[0] not in PUBLICOS:
            return self.send_error(404)
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/contacto":
            return self._json(404, {"error": "No encontrado."})
        try:
            largo = int(self.headers.get("Content-Length", 0))
            if not 0 < largo <= MAX_BYTES:
                return self._json(413, {"error": "Solicitud inválida."})
            datos = json.loads(self.rfile.read(largo).decode("utf-8"))
            if not isinstance(datos, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {"error": "Solicitud inválida."})

        if datos.get("web"):  # honeypot: los bots rellenan este campo
            return self._json(200, {"ok": True})

        limpio = {k: str(datos.get(k, "")).strip()[:2000] for k in CAMPOS}
        if any(not limpio[k] for k in REQUERIDOS) or not EMAIL.match(limpio["email"]):
            return self._json(422, {"error": "Revisa los campos obligatorios y el email."})
        if not datos.get("acepta"):
            return self._json(422, {"error": "Debes aceptar ser contactado."})

        limpio["recibido"] = datetime.now().isoformat(timespec="seconds")
        with ARCHIVO.open("a", encoding="utf-8") as f:
            f.write(json.dumps(limpio, ensure_ascii=False) + "\n")
        print(f"Nueva consulta: {limpio['nombre']} <{limpio['email']}> ({limpio['empresa']})")
        self._json(200, {"ok": True})


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), partial(Handler, directory=str(RAIZ)))
    print(f"Sitio en http://localhost:{puerto}  (Ctrl+C para salir)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass

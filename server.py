

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sqlite3
from urllib.parse import urlsplit


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "forma.sqlite3"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
PAGE_PATH = PROJECT_DIR / "outputs" / "index.html"


def initialize_database():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


class SiteHandler(BaseHTTPRequestHandler):
    def send_bytes(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_bytes(status, "application/json; charset=utf-8", body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            if not PAGE_PATH.exists():
                self.send_json(500, {"error": "Не найден файл outputs/index.html"})
                return
            self.send_bytes(200, "text/html; charset=utf-8", PAGE_PATH.read_bytes())
        elif path in ("/api/health", "/api/health/"):
            try:
                with sqlite3.connect(DATABASE_PATH) as connection:
                    connection.execute("SELECT 1").fetchone()
                self.send_json(200, {"status": "ok", "database": "connected"})
            except sqlite3.Error:
                self.send_json(500, {"status": "error", "database": "unavailable"})
        else:
            self.send_json(404, {"error": "Страница не найдена"})


if __name__ == "__main__":
    initialize_database()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), SiteHandler)
    print("Сайт запущен: http://127.0.0.1:8000/")
    print("Чтобы остановить сервер, нажми Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()

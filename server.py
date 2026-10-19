"""Локальный сервер сайта на стандартной библиотеке Python."""
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib, hmac, json, secrets, sqlite3, time
from urllib.parse import urlsplit

PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "data" / "forma.sqlite3"
SCHEMA_PATH = PROJECT_DIR / "schema.sql"
PAGE_PATH = PROJECT_DIR / "index.html"
SESSION_SECONDS = 7 * 24 * 60 * 60
PASSWORD_ITERATIONS = 240_000

def connect_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def initialize_database():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    with connect_database() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join(("pbkdf2_sha256", str(PASSWORD_ITERATIONS), salt.hex(), digest.hex()))

def verify_password(password, stored):
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds)).hex()
        return hmac.compare_digest(digest, digest_hex)
    except (ValueError, TypeError):
        return False

class SiteHandler(BaseHTTPRequestHandler):
    def send_bytes(self, status, content_type, body, headers=()):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, value, headers=()):
        self.send_bytes(status, "application/json; charset=utf-8", json.dumps(value, ensure_ascii=False).encode("utf-8"), headers)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 1_000_000:
                return None
            value = json.loads(self.rfile.read(length).decode("utf-8"))
            return value if isinstance(value, dict) else None
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None

    def create_session(self, user_id):
        token = secrets.token_urlsafe(32)
        expires = int(time.time()) + SESSION_SECONDS
        with connect_database() as db:
            db.execute("INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires))
        cookie = "session_id=" + token + "; Path=/; HttpOnly; SameSite=Lax; Max-Age=" + str(SESSION_SECONDS)
        return [("Set-Cookie", cookie)]

    def current_user(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        morsel = cookie.get("session_id")
        if morsel is None:
            return None
        with connect_database() as db:
            row = db.execute(
                "SELECT users.id, users.name, users.email, sessions.expires_at FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.session_id=?",
                (morsel.value,),
            ).fetchone()
            if row is None:
                return None
            if row["expires_at"] < int(time.time()):
                db.execute("DELETE FROM sessions WHERE session_id=?", (morsel.value,))
                return None
            return {"id": row["id"], "name": row["name"], "email": row["email"]}

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            if not PAGE_PATH.exists():
                self.send_json(500, {"error": "Не найден файл index.html"})
            else:
                self.send_bytes(200, "text/html; charset=utf-8", PAGE_PATH.read_bytes())
        elif path in ("/api/health", "/api/health/"):
            try:
                with connect_database() as db:
                    db.execute("SELECT 1")
                self.send_json(200, {"status": "ok", "database": "connected"})
            except sqlite3.Error:
                self.send_json(500, {"status": "error", "database": "unavailable"})
        elif path == "/api/me":
            user = self.current_user()
            self.send_json(200, {"user": user}) if user else self.send_json(401, {"error": "Войдите в аккаунт"})
        else:
            self.send_json(404, {"error": "Страница не найдена"})

    def do_POST(self):
        path = urlsplit(self.path).path
        data = self.read_json()
        if data is None:
            self.send_json(400, {"error": "Отправь корректные данные в формате JSON"})
            return
        if path == "/api/register":
            name = str(data.get("name", "")).strip()
            email = str(data.get("email", "")).strip().lower()
            password = data.get("password", "")
            if not name or len(name) > 80 or "@" not in email or len(email) > 254:
                self.send_json(400, {"error": "Проверь имя и электронную почту"})
                return
            if not isinstance(password, str) or not 8 <= len(password) <= 200:
                self.send_json(400, {"error": "Пароль должен содержать от 8 до 200 символов"})
                return
            try:
                with connect_database() as db:
                    cursor = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, hash_password(password)))
                    user_id = cursor.lastrowid
                self.send_json(201, {"user": {"id": user_id, "name": name, "email": email}}, self.create_session(user_id))
            except sqlite3.IntegrityError:
                self.send_json(409, {"error": "Аккаунт с такой почтой уже существует"})
            except sqlite3.Error:
                self.send_json(500, {"error": "Не удалось сохранить аккаунт"})
        elif path == "/api/login":
            email = str(data.get("email", "")).strip().lower()
            password = data.get("password", "")
            if not isinstance(password, str):
                password = ""
            with connect_database() as db:
                user = db.execute("SELECT id, name, email, password_hash FROM users WHERE email=?", (email,)).fetchone()
            if user is None or not verify_password(password, user["password_hash"]):
                self.send_json(401, {"error": "Неверная почта или пароль"})
                return
            self.send_json(200, {"user": {"id": user["id"], "name": user["name"], "email": user["email"]}}, self.create_session(user["id"]))
        elif path == "/api/logout":
            cookie = SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            morsel = cookie.get("session_id")
            if morsel:
                with connect_database() as db:
                    db.execute("DELETE FROM sessions WHERE session_id=?", (morsel.value,))
            self.send_json(200, {"status": "ok"}, [("Set-Cookie", "session_id=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")])
        else:
            self.send_json(404, {"error": "Адрес не найден"})

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

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
        seed_exercises(connection)

def seed_exercises(db):
    exercises = [
        ("Приседание к стулу", "Силовая", "Поставь стул позади себя. Отведи таз назад, согни колени и мягко коснись стула. Поднимись, надавливая стопами в пол.", "Без оборудования", "beginner"),
        ("Отжимание от стены", "Силовая", "Упрись ладонями в стену на ширине плеч. Согни руки, приближая грудь к стене, затем плавно выпрями их.", "Стена", "beginner"),
        ("Ягодичный мост", "Силовая", "Ляг на спину, согни колени, стопы поставь на пол. Напряги ягодицы и подними таз до прямой линии корпуса.", "Коврик", "beginner"),
        ("Птица-собака", "Стабилизация", "Встань на четвереньки. Вытяни противоположные руку и ногу, сохраняя спину ровной, затем поменяй сторону.", "Коврик", "beginner"),
        ("Подъём на носки", "Силовая", "Встань устойчиво, при необходимости держись за опору. Поднимись на носки, задержись на секунду и медленно опустись.", "Без оборудования", "beginner"),
        ("Шаги на месте", "Кардио", "Шагай на месте в комфортном темпе, мягко ставя стопу и свободно двигая руками.", "Без оборудования", "beginner"),
        ("Наклон от таза", "Подвижность", "Слегка согни колени и отведи таз назад, наклоняя корпус с ровной спиной. Вернись в исходное положение.", "Без оборудования", "beginner"),
        ("Планка с колен", "Стабилизация", "Обопрись на предплечья и колени. Напряги живот, держи корпус прямым и спокойно дыши.", "Коврик", "beginner"),
    ]
    db.executemany("INSERT OR IGNORE INTO exercises (name, category, instructions, equipment, difficulty) VALUES (?, ?, ?, ?, ?)", exercises)

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

def build_plan(profile):
    """Подбирает отдельную недельную программу по предпочтению, цели, опыту и месту занятий."""
    strength = [
      ("Приседание к стулу","ноги","нет","8–12","Стул поставь позади, стопы на ширине таза, носки слегка наружу. Отведи таз назад и согни колени, пока легко не коснёшься сиденья. Колени направляй по линии носков. Встань, надавливая всей стопой; не падай на стул."),
      ("Отжимание от стены","грудь","нет","8–12","Встань лицом к стене, ладони на уровне груди чуть шире плеч. Отойди на шаг. Напряги живот, держи тело прямым. Согни локти примерно под углом 30–45° к корпусу и приблизь грудь к стене. Выпрями руки без рывка."),
      ("Ягодичный мост","ягодицы","коврик","10–15","Ляг на спину, согни колени, стопы поставь на полу на ширине таза. Подтяни стопы так, чтобы пальцы почти касались пяток. Выдохни, напряги ягодицы и подними таз до прямой линии плечи–таз–колени. Не прогибай поясницу; опустись медленно."),
      ("Тяга рюкзака в наклоне","спина","рюкзак","8–12","Положи в рюкзак лёгкие вещи. Стопы на ширине таза, колени мягкие. Отведи таз назад и наклони корпус, сохраняя спину ровной. Подтяни рюкзак к нижним рёбрам, локти веди вдоль корпуса, затем медленно опусти."),
      ("Выпад назад с опорой","ноги","опора","6–10 на сторону","Встань рядом со стеной и держись одной рукой. Сделай небольшой шаг назад. Согни оба колена настолько, насколько комфортно; переднее колено направляй по носку, корпус слегка наклони вперёд. Оттолкнись передней стопой и вернись."),
      ("Жим бутылок лёжа","грудь","бутылки","8–12","Ляг на спину, колени согнуты. Возьми лёгкие бутылки, локти согнуты и лежат на полу под углом около 45° к корпусу. Выжми бутылки над серединой груди, не сталкивая их, и плавно опусти."),
    ]
    cardio = [
      ("Быстрая ходьба","кардио","улица","10–20 минут","Иди в темпе, при котором дыхание стало активнее, но ты можешь говорить короткими фразами. Ставь стопу мягко, плечи расслабь. Замедлись, если не можешь говорить или чувствуешь недомогание."),
      ("Танцевальные шаги","кардио","нет","30 секунд работы / 30 секунд отдыха × 6","Включи музыку и шагай в стороны, добавляя движения руками. Не прыгай, если это некомфортно. Двигайся в разговорном темпе; между интервалами спокойно восстанови дыхание."),
      ("Низкоударные шаги в стороны","кардио","нет","40 секунд × 4","Стой прямо, колени слегка согнуты. Шагни вправо и приставь левую ногу, затем влево. Не скрещивай ноги, ставь стопу тихо. Темп умеренный, без прыжков."),
    ]
    mobility = [
      ("Кошка–корова","спина","коврик","6–8 медленных циклов","Встань на четвереньки: кисти под плечами, колени под тазом. На выдохе мягко округли спину и опусти голову. На вдохе верни спину в нейтральное положение и слегка раскрой грудь. Не запрокидывай голову и не продавливай поясницу."),
      ("Поза ребёнка","таз","коврик","20–30 секунд × 2","Встань на колени, большие пальцы ног можно соединить. Медленно отведи таз к пяткам и наклони корпус вперёд, руки вытяни. Если коленям неприятно, подложи полотенце и не опускайся глубоко. Дыши спокойно."),
      ("Растяжка задней поверхности бедра лёжа","ноги","коврик","20 секунд на сторону × 2","Ляг на спину, одну ногу согни и оставь стопу на полу. Другую подними, слегка согнув колено, возьмись руками за бедро. Осторожно приблизь ногу к себе до мягкого натяжения сзади бедра. Не дёргай и не вызывай боль."),
      ("Растяжка грудных мышц у стены","грудь","стена","20 секунд на сторону × 2","Встань боком к стене. Положи ладонь и предплечье на стену, локоть примерно на уровне плеча. Медленно поверни корпус от руки до мягкого натяжения в груди. Не выкручивай плечо; смени сторону."),
    ]
    yoga = [
      ("Поза горы","осанка","нет","5 спокойных дыханий","Встань, стопы параллельны и примерно на ширине таза. Равномерно прижми пятку и основание большого пальца, колени не блокируй. Макушка тянется вверх, плечи расслаблены. Дыши спокойно, не выгибай поясницу."),
      ("Наклон стоя с согнутыми коленями","задняя цепь","нет","5 дыханий","Из положения стоя слегка согни колени и наклонись от тазобедренных суставов. Живот приблизь к бёдрам, руки свободно свисают или лежат на опоре. Не тяни себя вниз и не округляй спину насильно. Медленно поднимись."),
      ("Низкий выпад у опоры","таз","опора","3–5 дыханий на сторону","Поставь руки на устойчивый стул, шагни одной ногой назад и опусти пятку. Переднее колено согнуто и находится над стопой. Мягко направь таз вперёд до комфортного растяжения спереди бедра задней ноги. Повтори другой ногой."),
      ("Поза стола с вытяжением руки","плечи","коврик","4 дыхания на сторону","Встань на четвереньки, кисти под плечами, колени под тазом. Перенеси вес равномерно, вытянув одну руку вперёд на комфортную высоту. Не поворачивай таз. Верни ладонь и повтори другой рукой; можно выполнять только перенос веса без подъёма руки."),
    ]
    prefs = profile.get("prefs", [])
    if isinstance(prefs, str):
        try: prefs = json.loads(prefs)
        except ValueError: prefs = []
    prefs = [str(x).lower() for x in prefs]
    place = str(profile.get("place", "")).lower()
    level = str(profile.get("level", profile.get("fitness_level", "beginner"))).lower()
    frequency = max(2, min(int(profile.get("frequency", profile.get("weekly_frequency", 3))), 5))
    if any("йог" in x for x in prefs): mode, library = "Йога и мобильность", yoga + mobility
    elif any("растяж" in x for x in prefs): mode, library = "Растяжка и мобильность", mobility + yoga[:2]
    elif any("кардио" in x for x in prefs): mode, library = "Кардио", cardio + mobility[:1]
    else: mode, library = "Силовая программа", strength
    if "зал" in place or "инвентар" in place:
        library += [("Румынская тяга с рюкзаком","задняя цепь","рюкзак","8–12","Возьми лёгкий рюкзак перед бёдрами. Стопы на ширине таза, колени слегка согнуты. Отведи таз назад, скользя рюкзаком вдоль бёдер до натяжения сзади ног; спина ровная. Напряги ягодицы и вернись, не переразгибая поясницу.")]
    if "начинаю" in level or "beginner" in level or "начина" in level:
        sets, rest = 2, 60
    else: sets, rest = 3, 60
    # Раскладываем последовательность на разные дни недели и чередуем акценты.
    sessions = []
    for day in range(1, frequency + 1):
        rotated = library[day-1:] + library[:day-1]
        exercises = [{"name":n,"group":g,"equipment":eq,"sets":sets,"repetitions":rep,"rest":rest,"instructions":how} for n,g,eq,rep,how in rotated[:4]]
        sessions.append({"day":day,"title":f"{mode} · день {day}","duration":"20–35 минут","exercises":exercises})
    return {"goal":profile.get("goal","Поддерживать форму"),"mode":mode,"sessions":sessions,
            "warmup":"Начни с 3–5 минут лёгкой ходьбы и мягких движений суставами. Не растягивайся через боль.",
            "cooldown":"Заверши спокойным дыханием и лёгкой ходьбой 2–3 минуты. При боли или головокружении остановись."}

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
        elif path == "/api/profile":
            user = self.current_user()
            if not user:
                self.send_json(401, {"error": "Войдите в аккаунт"})
                return
            with connect_database() as db:
                row = db.execute("SELECT * FROM profiles WHERE user_id=?", (user["id"],)).fetchone()
            if not row:
                self.send_json(200, {"profile": None})
                return
            profile = dict(row)
            profile["prefs"] = json.loads(profile.get("equipment") or "[]")
            profile["frequency"] = profile["weekly_frequency"]
            profile["level"] = {"beginner":"Начинаю с нуля","intermediate":"Иногда тренируюсь","advanced":"Тренируюсь регулярно"}.get(profile["fitness_level"], "Начинаю с нуля")
            profile["place"] = profile["location"]
            profile["limits"] = profile["limitations"]
            plan = build_plan(profile)
            for session in plan["sessions"]:
                for exercise in session["exercises"]:
                    exercise["desc"] = exercise["instructions"]
                    exercise["meta"] = f"{exercise['sets']} подхода × {exercise['repetitions']} · отдых {exercise['rest']} сек"
            self.send_json(200, {"profile": profile, "plan": plan})
        elif path == "/api/workouts":
            user = self.current_user()
            if not user:
                self.send_json(401, {"error": "Войдите в аккаунт"})
                return
            with connect_database() as db:
                rows = db.execute("SELECT id, scheduled_date, status, started_at, completed_at, notes FROM workout_sessions WHERE user_id=? ORDER BY scheduled_date DESC, id DESC", (user["id"],)).fetchall()
            self.send_json(200, {"workouts": [dict(row) for row in rows]})
        else:
            self.send_json(404, {"error": "Страница не найдена"})

    def do_POST(self):
        path = urlsplit(self.path).path
        data = {} if path == "/api/logout" else self.read_json()
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
        elif path == "/api/profile":
            user = self.current_user()
            if not user:
                self.send_json(401, {"error": "Войдите в аккаунт"})
                return
            try:
                age = data.get("age") or None
                height = data.get("height") or None
                weight = data.get("weight") or None
                frequency = int(data.get("frequency", 3))
                if age is not None: age = int(age)
                if height is not None: height = float(height)
                if weight is not None: weight = float(weight)
                level_map = {"Начинаю с нуля": "beginner", "Иногда тренируюсь": "intermediate", "Тренируюсь регулярно": "advanced"}
                with connect_database() as db:
                    db.execute("""INSERT INTO profiles (user_id, age, height_cm, weight_kg, fitness_level, goal, weekly_frequency, location, equipment, limitations, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET age=excluded.age,height_cm=excluded.height_cm,weight_kg=excluded.weight_kg,fitness_level=excluded.fitness_level,goal=excluded.goal,weekly_frequency=excluded.weekly_frequency,location=excluded.location,equipment=excluded.equipment,limitations=excluded.limitations,updated_at=CURRENT_TIMESTAMP""",
                    (user["id"], age, height, weight, level_map.get(data.get("level"), "beginner"), str(data.get("goal", "Поддерживать форму"))[:80], max(1,min(frequency,7)), str(data.get("place", "Дома"))[:80], json.dumps(data.get("prefs", []), ensure_ascii=False), str(data.get("limits", ""))[:500]))
                self.send_json(200, {"status": "saved", "plan": build_plan(data)})
            except (ValueError, sqlite3.Error):
                self.send_json(400, {"error": "Проверь данные анкеты"})
        elif path == "/api/workout":
            user = self.current_user()
            if not user:
                self.send_json(401, {"error": "Войдите в аккаунт"})
                return
            date = str(data.get("date", ""))
            status = data.get("status")
            if len(date) != 10 or status not in ("in_progress", "completed", "incomplete"):
                self.send_json(400, {"error": "Проверь дату и статус тренировки"})
                return
            notes = json.dumps(data.get("done", []), ensure_ascii=False)
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            with connect_database() as db:
                old = db.execute("SELECT id, started_at FROM workout_sessions WHERE user_id=? AND scheduled_date=?", (user["id"], date)).fetchone()
                if old:
                    db.execute("UPDATE workout_sessions SET status=?, notes=?, started_at=COALESCE(started_at, ?), completed_at=? WHERE id=?", (status, notes, now, now if status == "completed" else None, old["id"]))
                    workout_id = old["id"]
                else:
                    db.execute("INSERT INTO workout_sessions (user_id, scheduled_date, started_at, completed_at, status, notes) VALUES (?, ?, ?, ?, ?, ?)", (user["id"], date, now, now if status == "completed" else None, status, notes))
                    workout_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            self.send_json(200, {"status": "saved", "workout_id": workout_id})
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

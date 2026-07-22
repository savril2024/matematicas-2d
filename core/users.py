import sqlite3
from pathlib import Path

# Render permite volúmenes persistentes. Usamos /data si existe, si no, local.
DB_PATH = Path("/data/matekids.db") if Path("/data").exists() else Path("data/matekids.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

AVATARS = ["🦁", "🦄", "🦊", "🐝", "🐵", "🐯", "🐰", "🐶"]


def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _conn() as c:
        # 1. Crear tabla con la nueva columna 'lang'
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                name TEXT PRIMARY KEY,
                avatar TEXT NOT NULL,
                stars INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                lang TEXT DEFAULT 'es'
            )
        """)
        
        # 2. Migración automática: Si la tabla ya existía sin 'lang', la agregamos
        try:
            c.execute("SELECT lang FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("🔄 Actualizando base de datos: agregando columna 'lang'...")
            c.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'es'")


_init_db()


def list_users() -> list[dict]:
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM users").fetchall()]


def create_user(name: str, avatar: str, lang: str = "es") -> dict:
    with _conn() as c:
        existing = c.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
        
        if existing:
            # Si el usuario ya existe, actualizamos su idioma preferido
            c.execute("UPDATE users SET lang = ? WHERE name = ?", (lang, name))
            # Recargamos los datos actualizados
            updated_user = c.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
            return dict(updated_user)
            
        # Si es nuevo, lo creamos con el idioma
        c.execute("INSERT INTO users (name, avatar, lang) VALUES (?, ?, ?)",
                  (name, avatar, lang))
        return {"name": name, "avatar": avatar, "stars": 0, "level": 1, "lang": lang}


def add_stars(name: str, n: int):
    with _conn() as c:
        c.execute("UPDATE users SET stars = stars + ? WHERE name=?",
                  (n, name))


def get_user(name: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE name=?",
                        (name,)).fetchone()
        return dict(row) if row else None
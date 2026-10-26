import os
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")
USE_PG = bool(DATABASE_URL)
if USE_PG:
    import psycopg2

PH = "%s" if USE_PG else "?"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "cambiame123")


def get_conn():
    if USE_PG:
        return psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=10)
    conn = sqlite3.connect("vias_rurales.db")
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite no valida llaves foráneas si no se activa
    return conn


def _agregar_columna(c, tabla, columna):
    """Migración: agrega una columna de texto si la tabla ya existía sin ella."""
    if USE_PG:
        c.execute(f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS {columna} TEXT")
    else:
        c.execute(f"PRAGMA table_info({tabla})")
        if columna not in [r[1] for r in c.fetchall()]:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} TEXT")


def init_db():
    conn = get_conn()
    c = conn.cursor()
    pk = "SERIAL PRIMARY KEY" if USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    c.execute(f"""CREATE TABLE IF NOT EXISTS reportes (
        id {pk}, via TEXT, estado TEXT, dano TEXT, descripcion TEXT,
        latitud REAL, longitud REAL, fecha TEXT, foto TEXT, ia_evaluacion TEXT, medio TEXT)""")
    _agregar_columna(c, "reportes", "medio")
    c.execute(f"""CREATE TABLE IF NOT EXISTS usuarios (
        id {pk}, usuario TEXT UNIQUE, password_hash TEXT)""")
    # Aportes de la comunidad (comentarios con foto) ligados a un reporte: relación 1 a muchos
    c.execute(f"""CREATE TABLE IF NOT EXISTS comentarios (
        id {pk},
        reporte_id INTEGER NOT NULL REFERENCES reportes(id) ON DELETE CASCADE,
        autor TEXT, tipo TEXT, texto TEXT, foto TEXT, fecha TEXT, ia TEXT)""")
    _agregar_columna(c, "comentarios", "ia")
    c.execute(f"SELECT 1 FROM usuarios WHERE usuario = {PH}", (ADMIN_USER,))
    if not c.fetchone():
        h = generate_password_hash(ADMIN_PASS, method="pbkdf2:sha256")
        c.execute(f"INSERT INTO usuarios (usuario, password_hash) VALUES ({PH}, {PH})",
                  (ADMIN_USER, h))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- reportes
def guardar_reporte(via, estado, dano, descripcion, latitud, longitud, fecha,
                    foto="sin_foto.jpg", ia_evaluacion="No analizado", medio="No indicado"):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""INSERT INTO reportes
        (via, estado, dano, descripcion, latitud, longitud, fecha, foto, ia_evaluacion, medio)
        VALUES ({",".join([PH] * 10)})""",
        (via, estado, dano, descripcion, latitud, longitud, fecha, foto, ia_evaluacion, medio))
    conn.commit()
    conn.close()


def obtener_reportes():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM reportes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def obtener_reporte(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT * FROM reportes WHERE id = {PH}", (id_,))
    row = c.fetchone()
    conn.close()
    return row


def borrar_reporte(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"DELETE FROM comentarios WHERE reporte_id = {PH}", (id_,))
    c.execute(f"DELETE FROM reportes WHERE id = {PH}", (id_,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- aportes
def guardar_comentario(reporte_id, autor, tipo, texto, foto, fecha, ia=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""INSERT INTO comentarios (reporte_id, autor, tipo, texto, foto, fecha, ia)
        VALUES ({",".join([PH] * 7)})""",
        (reporte_id, autor, tipo, texto, foto, fecha, ia))
    conn.commit()
    conn.close()


def obtener_comentarios(reporte_id):
    """Columnas: 0 id, 1 reporte_id, 2 autor, 3 tipo, 4 texto, 5 foto, 6 fecha, 7 ia."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""SELECT id, reporte_id, autor, tipo, texto, foto, fecha, ia
        FROM comentarios WHERE reporte_id = {PH} ORDER BY id DESC""", (reporte_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def contar_comentarios():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT reporte_id, COUNT(*) FROM comentarios GROUP BY reporte_id")
    d = dict(c.fetchall())
    conn.close()
    return d


def borrar_comentario(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"DELETE FROM comentarios WHERE id = {PH}", (id_,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- admin
def obtener_hash(usuario):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT password_hash FROM usuarios WHERE usuario = {PH}", (usuario,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
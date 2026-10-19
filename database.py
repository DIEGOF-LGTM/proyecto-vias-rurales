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
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    return sqlite3.connect("vias_rurales.db")


def init_db():
    conn = get_conn()
    c = conn.cursor()
    pk = "SERIAL PRIMARY KEY" if USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    c.execute(f"""CREATE TABLE IF NOT EXISTS reportes (
        id {pk}, via TEXT, estado TEXT, dano TEXT, descripcion TEXT,
        latitud REAL, longitud REAL, fecha TEXT, foto TEXT, ia_evaluacion TEXT)""")
    c.execute(f"""CREATE TABLE IF NOT EXISTS usuarios (
        id {pk}, usuario TEXT UNIQUE, password_hash TEXT)""")
    c.execute(f"SELECT 1 FROM usuarios WHERE usuario = {PH}", (ADMIN_USER,))
    if not c.fetchone():
        h = generate_password_hash(ADMIN_PASS, method="pbkdf2:sha256")
        c.execute(f"INSERT INTO usuarios (usuario, password_hash) VALUES ({PH}, {PH})",
                  (ADMIN_USER, h))
    conn.commit()
    conn.close()


def guardar_reporte(via, estado, dano, descripcion, latitud, longitud, fecha,
                    foto="sin_foto.jpg", ia_evaluacion="No analizado"):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""INSERT INTO reportes
        (via, estado, dano, descripcion, latitud, longitud, fecha, foto, ia_evaluacion)
        VALUES ({",".join([PH] * 9)})""",
        (via, estado, dano, descripcion, latitud, longitud, fecha, foto, ia_evaluacion))
    conn.commit()
    conn.close()


def obtener_reportes():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM reportes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def borrar_reporte(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"DELETE FROM reportes WHERE id = {PH}", (id_,))
    conn.commit()
    conn.close()


def obtener_hash(usuario):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT password_hash FROM usuarios WHERE usuario = {PH}", (usuario,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
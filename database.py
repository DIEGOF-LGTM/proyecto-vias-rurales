import sqlite3

DB_NAME = "vias_rurales.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            via TEXT,
            estado TEXT,
            dano TEXT,
            descripcion TEXT,
            latitud REAL,
            longitud REAL,
            fecha TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_reporte(via, estado, dano, descripcion, latitud, longitud, fecha):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reportes (via, estado, dano, descripcion, latitud, longitud, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (via, estado, dano, descripcion, latitud, longitud, fecha))
    conn.commit()
    conn.close()

def obtener_reportes():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM reportes ORDER BY id DESC")
    reportes = c.fetchall()
    conn.close()
    return reportes

def eliminar_reporte(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM reportes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
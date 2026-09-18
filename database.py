import sqlite3

def init_db():
    conn = sqlite3.connect('vias_rurales.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vereda TEXT,
            estado TEXT,
            dano TEXT,
            descripcion TEXT,
            latitud REAL,
            longitud REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            foto TEXT,
            ia TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insertar_reporte(vereda, estado, dano, descripcion, lat, lng, foto, ia):
    conn = sqlite3.connect('vias_rurales.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reportes (vereda, estado, dano, descripcion, latitud, longitud, foto, ia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (vereda, estado, dano, descripcion, lat, lng, foto, ia))
    conn.commit()
    conn.close()

def obtener_reportes():
    conn = sqlite3.connect('vias_rurales.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reportes ORDER BY id DESC')
    registros = cursor.fetchall()
    conn.close()
    return registros
    
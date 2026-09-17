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
            fecha TEXT,
            foto TEXT,
            ia_evaluacion TEXT
        )
    ''')
    
    # Asegurar que existan las columnas nuevas en bases de datos previas
    try:
        c.execute("ALTER TABLE reportes ADD COLUMN foto TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE reportes ADD COLUMN ia_evaluacion TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def guardar_reporte(via, estado, dano, descripcion, latitud, longitud, fecha, foto="sin_foto.jpg", ia_evaluacion="No analizado"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reportes (via, estado, dano, descripcion, latitud, longitud, fecha, foto, ia_evaluacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (via, estado, dano, descripcion, latitud, longitud, fecha, foto, ia_evaluacion))
    conn.commit()
    conn.close()

def obtener_reportes():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM reportes ORDER BY id DESC")
    reportes = c.fetchall()
    conn.close()
    return reportes
import os
import sqlite3
import urllib.parse as urlparse

# Obtener la URL de PostgreSQL desde Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    if DATABASE_URL:
        import psycopg2
        url = urlparse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        return conn
    else:
        return sqlite3.connect('vias_rurales.db')

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reportes (
                id SERIAL PRIMARY KEY,
                vereda VARCHAR(100),
                estado VARCHAR(50),
                dano VARCHAR(100),
                descripcion TEXT,
                latitud DOUBLE PRECISION,
                longitud DOUBLE PRECISION,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                foto VARCHAR(255),
                ia TEXT
            )
        ''')
    else:
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
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    
    query = f'''
        INSERT INTO reportes (vereda, estado, dano, descripcion, latitud, longitud, foto, ia)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
    '''
    
    cursor.execute(query, (vereda, estado, dano, descripcion, lat, lng, foto, ia))
    conn.commit()
    conn.close()

def obtener_reportes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reportes ORDER BY id DESC')
    registros = cursor.fetchall()
    conn.close()
    return registros
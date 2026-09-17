import psycopg2
import os
from urllib.parse import urlparse

def get_db_connection():
    # Render entrega la conexion como una sola URL en DATABASE_URL
    # (formato: postgres://usuario:clave@host:puerto/nombre_bd)
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        resultado = urlparse(database_url)
        return psycopg2.connect(
            host=resultado.hostname,
            user=resultado.username,
            password=resultado.password,
            dbname=resultado.path[1:],  # quita la "/" inicial
            port=resultado.port or 5432
        )

    # Alternativa para pruebas en tu computador, si no usas DATABASE_URL local
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "1234"),
        dbname=os.environ.get("PGDATABASE", "vias_rurales"),
        port=int(os.environ.get("PGPORT", 5432))
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reporte_incidente (
            id SERIAL PRIMARY KEY,
            via VARCHAR(150) NOT NULL,
            estado VARCHAR(50) NOT NULL,
            dano VARCHAR(50) NOT NULL,
            descripcion TEXT,
            latitud DECIMAL(10, 8) NOT NULL,
            longitud DECIMAL(11, 8) NOT NULL,
            fecha DATE NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def guardar_reporte(via, estado, dano, descripcion, latitud, longitud, fecha):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO reporte_incidente (via, estado, dano, descripcion, latitud, longitud, fecha)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (via, estado, dano, descripcion, latitud, longitud, fecha))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_reportes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, via, estado, dano, descripcion, latitud, longitud, fecha FROM reporte_incidente ORDER BY id DESC")
    datos = cursor.fetchall()
    cursor.close()
    conn.close()
    return datos

def eliminar_reporte(id_reporte):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reporte_incidente WHERE id = %s", (id_reporte,))
    conn.commit()
    cursor.close()
    conn.close()
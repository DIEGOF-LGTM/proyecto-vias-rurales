import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST", "localhost"),
        user=os.environ.get("MYSQLUSER", "root"),
        password=os.environ.get("MYSQLPASSWORD", "1234"),  # Tu contraseña local de MySQL
        database=os.environ.get("MYSQLDATABASE", "vias_rurales"),
        port=int(os.environ.get("MYSQLPORT", 3306))
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reporte_incidente (
            id INT AUTO_INCREMENT PRIMARY KEY,
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
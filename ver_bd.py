import psycopg2
import csv
from tabulate import tabulate

# Tu External Database URL de Render
URL_EXTERNA = "postgresql://vias_rurales_user:pXeOFzIu4GQtB2kyaAlugwQ9zKBxc66d@dpg-damogku7bikc73bslsv0-a.oregon-postgres.render.com/vias_rurales"

def consultar_base_datos():
    try:
        conexion = psycopg2.connect(URL_EXTERNA)
        cursor = conexion.cursor()
        
        # Consulta de registros
        cursor.execute("SELECT id, vereda, estado, dano, descripcion, latitud, longitud, fecha, foto, ia FROM reportes ORDER BY id DESC;")
        reportes = cursor.fetchall()
        
        # Encabezados de la tabla
        headers = ["ID", "Vereda", "Estado", "Tipo de Daño", "Descripción", "Latitud", "Longitud", "Fecha", "Foto", "Evaluación IA"]
        
        if not reportes:
            print("\n⚠️ No hay reportes registrados aún en la base de datos.\n")
        else:
            print(f"\n📊 TOTAL DE REPORTES EN POSTGRESQL: {len(reportes)}\n")
            
            # Imprimir en consola con formato de tabla profesional
            print(tabulate(reportes, headers=headers, tablefmt="fancy_grid"))
            
            # Guardar en un archivo CSV abreble en Excel
            nombre_archivo = "reportes_vias_ubate.csv"
            with open(nombre_archivo, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(headers)
                writer.writerows(reportes)
                
            print(f"\n✅ ¡Se ha generado el archivo Excel/CSV: '{nombre_archivo}' en la carpeta de tu proyecto!\n")
                
        cursor.close()
        conexion.close()
        
    except Exception as error:
        print(f"\n❌ Error al conectar a la base de datos: {error}\n")

if __name__ == "__main__":
    consultar_base_datos()
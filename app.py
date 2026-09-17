import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import database

app = Flask(__name__)

# Configuración de carpeta de imágenes
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar base de datos
database.init_db()

def analizar_imagen_danio(ruta_imagen):
    """
    Análisis básico con OpenCV: mide bordes y severidad de textura
    """
    try:
        img = cv2.imread(ruta_imagen)
        if img is None:
            return "No analizado"
        
        # Convertir a escala de grises y aplicar deteccion de bordes Canny
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # Calcular porcentaje de bordes/grietas detectados
        total_pixels = edges.size
        edge_pixels = np.count_nonzero(edges)
        porcentaje_dano = (edge_pixels / total_pixels) * 100

        if porcentaje_dano > 12.0:
            return f"IA: Daño Severo/Crítico ({porcentaje_dano:.1f}% textura)"
        elif porcentaje_dano > 5.0:
            return f"IA: Daño Moderado ({porcentaje_dano:.1f}% textura)"
        else:
            return f"IA: Daño Menor / Vía Estable ({porcentaje_dano:.1f}% textura)"
    except Exception as e:
        return "IA: Error procesando imagen"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reportar', methods=['POST'])
def reportar():
    via = request.form.get('via')
    estado = request.form.get('estado')
    dano = request.form.get('dano')
    descripcion = request.form.get('descripcion', '')
    latitud = request.form.get('latitud')
    longitud = request.form.get('longitud')
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Procesar imagen subida
    foto = request.files.get('foto')
    nombre_foto = "sin_foto.jpg"
    ia_evaluacion = "Sin imagen adjunta"

    if foto and foto.filename != '':
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto.filename}")
        ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(ruta_guardado)
        nombre_foto = filename
        
        # Analizar con OpenCV
        ia_evaluacion = analizar_imagen_danio(ruta_guardado)

    # Guardar en SQLite
    database.guardar_reporte(
        via, estado, dano, descripcion, 
        float(latitud) if latitud else 0.0, 
        float(longitud) if longitud else 0.0, 
        fecha, nombre_foto, ia_evaluacion
    )

    return redirect(url_for('reportes'))

@app.route('/reportes')
def reportes():
    lista_reportes = database.obtener_reportes()
    return render_template('reportes.html', reportes=lista_reportes)

if __name__ == '__main__':
    app.run(debug=True)
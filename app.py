import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import database

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

database.init_db()

def analizar_imagen_danio(ruta_imagen):
    try:
        img = cv2.imread(ruta_imagen)
        if img is None:
            return "Sin imagen válida"
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        porcentaje_dano = (np.count_nonzero(edges) / edges.size) * 100

        if porcentaje_dano > 12.0:
            return f"IA: Daño Severo ({porcentaje_dano:.1f}% textura)"
        elif porcentaje_dano > 5.0:
            return f"IA: Daño Moderado ({porcentaje_dano:.1f}% textura)"
        else:
            return f"IA: Daño Menor / Leve ({porcentaje_dano:.1f}% textura)"
    except Exception:
        return "IA: No analizado"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reportar', methods=['POST'])
def reportar():
    via = request.form.get('via')
    estado = request.form.get('estado')
    dano = request.form.get('dano')
    descripcion = request.form.get('descripcion', '')
    latitud = request.form.get('latitud', '5.3081')
    longitud = request.form.get('longitud', '-73.8143')
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    foto = request.files.get('foto')
    nombre_foto = "sin_foto.jpg"
    ia_evaluacion = "Sin foto adjunta"

    if foto and foto.filename != '':
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto.filename}")
        ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(ruta_guardado)
        nombre_foto = filename
        ia_evaluacion = analizar_imagen_danio(ruta_guardado)

    database.guardar_reporte(
        via, estado, dano, descripcion, 
        float(latitud), float(longitud), 
        fecha, nombre_foto, ia_evaluacion
    )

    return redirect(url_for('reportes'))

@app.route('/reportes')
def reportes():
    lista_reportes = database.obtener_reportes()
    return render_template('reportes.html', reportes=lista_reportes)

if __name__ == '__main__':
    app.run(debug=True)